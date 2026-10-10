import wave

import mido
import patches
import pytest
import synth_render as sr
from conftest import PATCHES, SYNTHDEFS, write_patches
from test_spec import set_meta


def test_registry_matches_synthdefs(song_with_patches):
    """登録簿の params / pieces の引数名は、すべて曲の SynthDef の引数として存在する。"""
    args = patches.synthdef_args("demo")
    for pid, e in patches.registry("demo").items():
        if e["kind"] == "drums":
            for name, p in e["pieces"].items():
                assert set(p["params"]) <= args[p["synthdef"]], (pid, name)
        else:
            assert set(e["params"]) <= args[e["synthdef"]], pid


def test_new_project_starts_without_any_patch(song):
    """曲は空の音色から始まる。リポジトリ共通の音色(config/patches.yaml)は引き継がない。"""
    assert patches.registry("demo") == {}
    assert patches.synthdef_args("demo") == {}


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
    assert patches.validate_overrides(reg["lowsaw"], {"cutoff": 700}) == []
    assert patches.validate_overrides(reg["lowsaw"], {"nope": 1})
    assert patches.validate_overrides(reg["kit"], {"kick": {"tune": 40}}) == []
    assert patches.validate_overrides(reg["kit"], {"kick": {"cutoff": 40}})
    assert patches.validate_overrides(reg["kit"], {"banjo": {"tune": 40}})


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
    assert len(v) == 2 and v[0]["sets"] == [(0.5, pytest.approx(sr.mtof(39), abs=1e-3))] and v[0]["release"] == 1.0


def test_poly_patch_makes_one_voice_per_note(song_with_patches):
    notes = [{"start": 0.0, "end": 1.0, "note": n, "vel": 90, "ch": 0} for n in (60, 64, 67)]
    v = sr.build_voices(notes, patches.registry("demo")["keys"], {"index": 2.0})
    assert len(v) == 3 and all(x["controls"]["index"] == 2.0 for x in v)


def test_drum_notes_map_to_pieces_and_velocity_scales_amp(song_with_patches):
    reg = patches.registry("demo")["kit"]
    notes = [
        {"start": 0.0, "end": 0.1, "note": 36, "vel": 127, "ch": 9},
        {"start": 0.5, "end": 0.6, "note": 56, "vel": 64, "ch": 9},
        {"start": 1.0, "end": 1.1, "note": 99, "vel": 100, "ch": 9},  # 割り当てなし
    ]
    v = sr.build_voices(notes, reg, {"kick": {"tune": 38}})
    assert [x["def"] for x in v] == ["thump", "tick"]
    assert v[0]["controls"]["tune"] == 38 and v[0]["release"] is None
    assert v[1]["controls"]["amp"] < reg["pieces"]["tick"]["params"]["amp"]


def test_scd_loads_the_songs_own_synthdefs(song_with_patches, tmp_path):
    notes = [{"start": 0.0, "end": 0.5, "note": 48, "vel": 100, "ch": 0}]
    v = sr.build_voices(notes, patches.registry("demo")["lowsaw"], {})
    scd = tmp_path / "r.scd"
    sr.write_scd(scd, v, sr.end_time(v), tmp_path / "s.osc", tmp_path / "o.wav", patches.synthdefs_path("demo"))
    src = scd.read_text(encoding="utf-8")
    assert "\\lowsaw" in src and "Score.recordNRT" in src and "0.exit" in src
    assert str(song_with_patches / "synth" / "synthdefs.scd") in src and "synth/synthdefs.scd\"" in src
    assert [e[1] for e in sr.score_events(v)] == [0, 2]


def _wav(path, seconds=0.5, rate=8000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(seconds * rate))


SAMPLE_PATCHES = PATCHES + """  hit:
    {name: 声, kind: melodic, synthdef: player, oneshot: true, sample: samples/hit.wav, root_note: 60, params: {amp: 0.5, pan: 0}}
"""


def test_user_sample_is_pitched_and_loaded_as_buffer(song_with_patches, tmp_path):
    _wav(song_with_patches / "samples" / "hit.wav")
    write_patches(song_with_patches, SAMPLE_PATCHES)
    set_meta(song_with_patches, "06-melody", params={"patch": "hit"})
    assert patches.check("demo", only="06-melody") == []
    notes = [{"start": 0.0, "end": 0.1, "note": 72, "vel": 100, "ch": 0}]
    v = sr.build_voices(notes, patches.registry("demo")["hit"], {}, song_with_patches)
    assert v[0]["controls"]["rate"] == pytest.approx(2.0) and v[0]["tail"] == pytest.approx(0.25)
    scd = tmp_path / "r.scd"
    sr.write_scd(scd, v, sr.end_time(v), tmp_path / "s.osc", tmp_path / "o.wav", patches.synthdefs_path("demo"))
    src = scd.read_text(encoding="utf-8")
    assert "/b_allocRead" in src and "hit.wav" in src and sr.end_time(v) >= 0.25
    assert v[0]["controls"]["buf"] == 0


def test_sample_outside_samples_dir_is_rejected(song_with_patches):
    (song_with_patches / "evil.wav").write_bytes(b"")
    write_patches(song_with_patches, SAMPLE_PATCHES.replace("samples/hit.wav", "../demo/evil.wav"))
    set_meta(song_with_patches, "06-melody", params={"patch": "hit"})
    assert any("samples/" in e for e in patches.check("demo"))


def test_sample_missing_or_synthdef_without_buf_is_an_error(song_with_patches):
    write_patches(song_with_patches, SAMPLE_PATCHES, SYNTHDEFS.replace("buf=0, rate=1, ", ""))
    _wav(song_with_patches / "samples" / "hit.wav")
    set_meta(song_with_patches, "06-melody", params={"patch": "hit"})
    assert any("buf" in e for e in patches.check("demo"))
    (song_with_patches / "samples" / "hit.wav").unlink()
    assert any("samples/" in e for e in patches.check("demo"))


def test_render_dry_run(song_with_patches, capsys):
    import common

    d = common.require_project("demo")
    set_meta(d, "04-bass", params={"patch": "lowsaw", "patch_params": {"cutoff": 700}})
    (d / "tracks").mkdir(exist_ok=True)
    _mid(d / "tracks", [(0, "note_on", 36, 100), (480, "note_off", 36, 0)]).rename(d / "tracks" / "04_bass_v1.mid")
    sr.render("demo", "04_bass_v1", dry_run=True)
    assert "lowsaw" in capsys.readouterr().out
