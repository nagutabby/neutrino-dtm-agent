import wave

import mido
import patches
import pytest
import synth_render as sr
from conftest import PATCHES, write_patches
from test_spec import set_meta


def test_registry_matches_sonic_pi_synths(song_with_patches):
    """登録簿の synth / params / fx は、すべて Sonic Pi の内蔵シンセ・FX の名前と引数として存在する。"""
    reg = patches.registry("demo")
    assert patches.voice_errors("lowsaw", reg["lowsaw"]) == []
    assert patches.voice_errors("kit.kick", reg["kit"]["pieces"]["kick"]) == []
    assert patches.fx_errors("keys", reg["keys"]) == []


def test_unknown_synth_param_and_fx_are_errors(song_with_patches):
    assert patches.voice_errors("x", {"synth": "nosuch", "params": {}})
    assert any("cutoffy" in e for e in patches.voice_errors("x", {"synth": "tb303", "params": {"cutoffy": 1}}))
    assert patches.fx_errors("x", {"fx": [{"name": "nosuch"}]})
    assert patches.fx_errors("x", {"fx": [{"name": "reverb", "params": {"nosuch": 1}}]})
    assert patches.voice_errors("x", {"synth": "tb303", "params": {}, "sweep": {"note": 30}})


def test_new_project_starts_without_any_patch(song):
    """曲は空の音色から始まる。リポジトリ共通の音色(config/patches.yaml)は引き継がない。"""
    assert patches.registry("demo") == {}


def test_other_songs_patches_are_not_visible(song_with_patches, tmp_path):
    (tmp_path / "other" / "synth").mkdir(parents=True)
    assert patches.registry("other") == {}


def test_unregistered_patch_is_an_error(song):
    set_meta(song, "04-bass", params={"patch": "lowsaw"})
    errs = patches.check("demo")
    assert any("lowsaw" in e and "流用しない" in e for e in errs)


def test_no_default_patch_is_assumed(song_with_patches):
    """patch を AI が補わない: 指定が無ければエラー。"""
    import common

    set_meta(song_with_patches, "04-bass", status="draft")
    assert patches.patch_id_of(common.load_specs("demo"), "04-bass") is None
    assert any("04-bass" in e and "patch が決まらない" in e for e in patches.check("demo"))


def test_override_validation(song_with_patches):
    reg = patches.registry("demo")
    assert patches.validate_overrides(reg["lowsaw"], {"cutoff": 70}) == []
    assert patches.validate_overrides(reg["lowsaw"], {"nope": 1})
    assert patches.validate_overrides(reg["kit"], {"kick": {"decay": 0.4}}) == []
    assert patches.validate_overrides(reg["kit"], {"kick": {"cutoff": 40}})
    assert patches.validate_overrides(reg["kit"], {"banjo": {"decay": 0.4}})


def _mid(tmp_path, events, ticks=480):
    m = mido.MidiFile(ticks_per_beat=ticks)
    t = mido.MidiTrack()
    m.tracks.append(t)
    t.append(mido.MetaMessage("set_tempo", tempo=500000))  # 120 BPM: 1 拍=0.5 秒
    last = 0
    for tick, kind, note, vel in sorted(events):
        t.append(mido.Message(kind, note=note, velocity=vel, time=tick - last))
        last = tick
    p = tmp_path / "x.mid"
    m.save(str(p))
    return p


def test_read_notes_seconds(tmp_path):
    p = _mid(tmp_path, [(0, "note_on", 60, 100), (480, "note_off", 60, 0), (480, "note_on", 64, 80), (960, "note_off", 64, 0)])
    notes = sr.read_notes(p)
    assert [(n["note"], round(n["start"], 3), round(n["end"], 3)) for n in notes] == [(60, 0.0, 0.5), (64, 0.5, 1.0)]


def test_mono_patch_glides_adjacent_notes(song_with_patches):
    reg = patches.registry("demo")["lowsaw"]
    notes = [
        {"start": 0.0, "end": 0.5, "note": 36, "vel": 100, "ch": 0},
        {"start": 0.5, "end": 1.0, "note": 39, "vel": 100, "ch": 0},
        {"start": 2.0, "end": 2.5, "note": 36, "vel": 100, "ch": 0},
    ]
    v = sr.build_voices(notes, reg, {})
    assert len(v) == 2 and v[0]["sets"] == [(0.5, 39)] and v[0]["end"] == 1.0
    assert v[0]["opts"]["note"] == 36 and v[0]["opts"]["note_slide"] == sr.DEFAULT_GLIDE


def test_poly_patch_makes_one_voice_per_note(song_with_patches):
    notes = [{"start": 0.0, "end": 1.0, "note": n, "vel": 90, "ch": 0} for n in (60, 64, 67)]
    v = sr.build_voices(notes, patches.registry("demo")["keys"], {"depth": 2.0})
    assert len(v) == 3 and all(x["opts"]["depth"] == 2.0 and x["synth"] == "fm" for x in v)


def test_drum_notes_map_to_pieces_and_velocity_scales_amp(song_with_patches):
    reg = patches.registry("demo")["kit"]
    notes = [
        {"start": 0.0, "end": 0.1, "note": 36, "vel": 127, "ch": 9},
        {"start": 0.5, "end": 0.6, "note": 56, "vel": 64, "ch": 9},
        {"start": 1.0, "end": 1.1, "note": 99, "vel": 100, "ch": 9},  # 割り当てなし
    ]
    v = sr.build_voices(notes, reg, {"kick": {"decay": 0.4}})
    assert [x["synth"] for x in v] == ["sc808_bassdrum", "sc808_closed_hihat"]
    assert v[0]["opts"]["decay"] == 0.4 and v[0]["end"] is None
    assert v[1]["opts"]["amp"] < reg["pieces"]["tick"]["params"]["amp"]


def test_code_uses_builtin_synths_and_fx(song_with_patches):
    reg = patches.registry("demo")
    notes = [{"start": 0.0, "end": 0.5, "note": 48, "vel": 100, "ch": 0}, {"start": 0.5, "end": 1.0, "note": 52, "vel": 100, "ch": 0}]
    v = sr.build_voices(notes, reg["keys"], {})
    code = sr.build_code(v, sr.end_time(v), reg["keys"]["fx"])
    assert "with_fx :reverb, room: 0.6, mix: 0.3 do" in code and "synth :fm, " in code and "note: 48" in code
    assert code.count("sleep ") == 2 and code.rstrip().endswith("end")
    # sustain はノート長から決まる(0.5 秒 - attack 0 - decay 0)
    assert "sustain: 0.5" in code


def test_mono_and_sweep_emit_control(song_with_patches):
    reg = patches.registry("demo")
    notes = [{"start": 0.0, "end": 0.5, "note": 36, "vel": 100, "ch": 0}, {"start": 0.5, "end": 1.0, "note": 39, "vel": 100, "ch": 0}]
    code = sr.build_code(sr.build_voices(notes, reg["lowsaw"], {}), 3.0)
    assert "v0 = synth :tb303" in code and "control v0, note: 39.0" in code and "sustain: 1.0" in code
    kick = sr.build_voices([{"start": 0.0, "end": 0.1, "note": 36, "vel": 127, "ch": 9}], reg["kit"], {})
    kc = sr.build_code(kick, 2.0)
    assert "v0 = synth :sc808_bassdrum" in kc and "note_slide: 0.1" in kc and "control v0, note: 30.0" in kc


def test_timeline_has_no_drift(song_with_patches):
    notes = [{"start": i / 3, "end": i / 3 + 0.1, "note": 60, "vel": 100, "ch": 0} for i in range(30)]
    code = sr.build_code(sr.build_voices(notes, patches.registry("demo")["keys"], {}), 12.0)
    total = sum(float(ln.split()[1]) for ln in code.splitlines() if ln.strip().startswith("sleep "))
    assert total == pytest.approx(12.0, abs=1e-3)


def _wav(path, seconds=0.5, rate=8000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(seconds * rate))


SAMPLE_PATCHES = PATCHES + """  hit:
    {name: 声, kind: melodic, sample: samples/hit.wav, root_note: 60, params: {amp: 0.5, pan: 0}}
"""


def test_user_sample_is_pitched_and_played_with_sample(song_with_patches):
    _wav(song_with_patches / "samples" / "hit.wav")
    write_patches(song_with_patches, SAMPLE_PATCHES)
    set_meta(song_with_patches, "06-melody", params={"patch": "hit"})
    assert patches.check("demo", only="06-melody") == []
    notes = [{"start": 0.0, "end": 0.1, "note": 72, "vel": 100, "ch": 0}]
    v = sr.build_voices(notes, patches.registry("demo")["hit"], {}, song_with_patches)
    assert v[0]["opts"]["rate"] == pytest.approx(2.0) and v[0]["tail"] == pytest.approx(0.25) and v[0]["end"] is None
    code = sr.build_code(v, sr.end_time(v))
    assert "sample \"" in code and "hit.wav" in code and "rate: 2.0" in code and sr.end_time(v) >= 0.25


def test_sample_outside_samples_dir_is_rejected(song_with_patches):
    (song_with_patches / "evil.wav").write_bytes(b"")
    write_patches(song_with_patches, SAMPLE_PATCHES.replace("samples/hit.wav", "../demo/evil.wav"))
    set_meta(song_with_patches, "06-melody", params={"patch": "hit"})
    assert any("samples/" in e for e in patches.check("demo"))


def test_sample_missing_or_with_synth_is_an_error(song_with_patches):
    write_patches(song_with_patches, SAMPLE_PATCHES)
    set_meta(song_with_patches, "06-melody", params={"patch": "hit"})
    assert any("samples/" in e for e in patches.check("demo"))  # wav がまだない
    _wav(song_with_patches / "samples" / "hit.wav")
    write_patches(song_with_patches, SAMPLE_PATCHES.replace("kind: melodic, sample", "kind: melodic, synth: beep, sample"))
    assert any("同時に" in e for e in patches.check("demo"))


def test_render_dry_run(song_with_patches, capsys):
    import common

    d = common.require_project("demo")
    set_meta(d, "04-bass", params={"patch": "lowsaw", "patch_params": {"cutoff": 70}})
    (d / "tracks").mkdir(exist_ok=True)
    _mid(d / "tracks", [(0, "note_on", 36, 100), (480, "note_off", 36, 0)]).rename(d / "tracks" / "04_bass_v1.mid")
    sr.render("demo", "04_bass_v1", dry_run=True)
    assert "lowsaw" in capsys.readouterr().out
