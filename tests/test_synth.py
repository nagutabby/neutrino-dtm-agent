import mido
import patches
import pytest
import synth_render as sr


def test_registry_matches_synthdefs():
    """登録簿の params / pieces の引数名は、すべて SynthDef の引数として存在する。"""
    args = patches.synthdef_args()
    for pid, e in patches.registry().items():
        if e["kind"] == "drums":
            for name, p in e["pieces"].items():
                assert p["synthdef"] in args, (pid, name)
                assert set(p["params"]) <= args[p["synthdef"]], (pid, name, set(p["params"]) - args[p["synthdef"]])
        else:
            assert e["synthdef"] in args, pid
            assert set(e["params"]) <= args[e["synthdef"]], (pid, set(e["params"]) - args[e["synthdef"]])
            if e.get("uses_dur"):
                assert "dur" in args[e["synthdef"]]


def test_defaults_point_to_existing_patches():
    assert set(patches.defaults().values()) <= set(patches.registry())


def test_override_validation():
    reg = patches.registry()
    assert patches.validate_overrides(reg["sub808"], {"glide": 0.1}) == []
    assert patches.validate_overrides(reg["sub808"], {"nope": 1})
    assert patches.validate_overrides(reg["kit_808"], {"kick": {"tune": 40}}) == []
    assert patches.validate_overrides(reg["kit_808"], {"kick": {"cutoff": 40}})
    assert patches.validate_overrides(reg["kit_808"], {"banjo": {"tune": 40}})


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


def test_mono_patch_glides_adjacent_notes():
    reg = patches.registry()["sub808"]
    notes = [
        {"start": 0.0, "end": 0.5, "note": 36, "vel": 100, "ch": 0},
        {"start": 0.5, "end": 1.0, "note": 39, "vel": 100, "ch": 0},
        {"start": 2.0, "end": 2.5, "note": 36, "vel": 100, "ch": 0},
    ]
    v = sr.build_voices(notes, reg, {})
    assert len(v) == 2 and v[0]["sets"] == [(0.5, pytest.approx(sr.mtof(39), abs=1e-3))] and v[0]["release"] == 1.0


def test_poly_patch_makes_one_voice_per_note():
    notes = [{"start": 0.0, "end": 1.0, "note": n, "vel": 90, "ch": 0} for n in (60, 64, 67)]
    v = sr.build_voices(notes, patches.registry()["epiano"], {"index": 2.0})
    assert len(v) == 3 and all(x["controls"]["index"] == 2.0 for x in v)


def test_drum_notes_map_to_pieces_and_velocity_scales_amp():
    reg = patches.registry()["kit_808"]
    notes = [
        {"start": 0.0, "end": 0.1, "note": 36, "vel": 127, "ch": 9},
        {"start": 0.5, "end": 0.6, "note": 56, "vel": 64, "ch": 9},
        {"start": 1.0, "end": 1.1, "note": 99, "vel": 100, "ch": 9},  # 割り当てなし
    ]
    v = sr.build_voices(notes, reg, {"kick": {"tune": 38}})
    assert [x["def"] for x in v] == ["kick", "cowbell"]
    assert v[0]["controls"]["tune"] == 38 and v[0]["release"] is None
    assert v[1]["controls"]["amp"] < reg["pieces"]["cowbell"]["params"]["amp"]


def test_scd_is_ordered_and_contains_release(tmp_path):
    notes = [{"start": 0.0, "end": 0.5, "note": 48, "vel": 100, "ch": 0}]
    v = sr.build_voices(notes, patches.registry()["bass_saw"], {})
    scd = tmp_path / "r.scd"
    sr.write_scd(scd, v, sr.end_time(v), tmp_path / "s.osc", tmp_path / "o.wav")
    src = scd.read_text(encoding="utf-8")
    assert "\\bass_saw" in src and "Score.recordNRT" in src and "0.exit" in src
    ev = sr.score_events(v)
    assert [e[1] for e in ev] == [0, 2]


def test_render_dry_run(song, capsys):
    import common
    from test_spec import set_meta

    d = common.require_project("demo")
    set_meta(d, "04-bass", params={"patch": "sub808", "patch_params": {"glide": 0.1}})
    (d / "tracks").mkdir(exist_ok=True)
    _mid(d / "tracks", [(0, "note_on", 36, 100), (480, "note_off", 36, 0)]).rename(d / "tracks" / "04_bass_v1.mid")
    sr.render("demo", "04_bass_v1", dry_run=True)
    assert "sub808" in capsys.readouterr().out
