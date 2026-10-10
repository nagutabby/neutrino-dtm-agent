import midi_validate
from conftest import make_midi


def melody(path, notes):
    make_midi(path, notes)
    return midi_validate.validate(str(path))


def test_good_melody_has_no_errors(tmp_path):
    notes = [(i * 1.0, 0.75, 60 + (i % 5), 80) for i in range(16)]
    errors, _ = melody(tmp_path / "m.mid", notes)
    assert errors == []


def test_overlap_is_error(tmp_path):
    errors, _ = melody(tmp_path / "m.mid", [(0, 2, 60, 80), (1, 2, 64, 80)])
    assert any("同時に鳴る音" in e for e in errors)


def test_out_of_range_warns(tmp_path):
    _, warns = melody(tmp_path / "m.mid", [(0, 1, 100, 80), (2, 1, 62, 80)])
    assert any("音域" in w for w in warns)


def test_empty_is_error(tmp_path):
    errors, _ = melody(tmp_path / "m.mid", [])
    assert errors


def test_ai_check_flags_flat_velocity_and_copied_bars(tmp_path):
    import ai_check
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    for _ in range(12):  # 同じ1小節を12回、ベロシティ固定
        for _ in range(4):
            tr.append(mido.Message("note_on", note=60, velocity=80, time=0))
            tr.append(mido.Message("note_off", note=60, velocity=0, time=480))
    p = tmp_path / "t.mid"
    mid.save(p)
    out = "\n".join(ai_check.check_midi(p))
    assert "ベロシティ" in out and "繰り返し" in out and "音域が狭い" in out


def test_apply_accent_adds_variation_within_limits(tmp_path):
    import ai_check
    import apply_accent
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    for _ in range(20):  # 1小節1和音(頭拍)・ベロシティ固定
        tr.append(mido.Message("note_on", note=60, velocity=70, time=0))
        tr.append(mido.Message("note_off", note=60, velocity=0, time=1920))
    src, dst = tmp_path / "a.mid", tmp_path / "b.mid"
    mid.save(src)
    assert "ベロシティ" in "\n".join(ai_check.check_midi(src))
    apply_accent.apply(str(src), str(dst), {"downbeat": 2, "phrase_arc": [-4, -1, 2, 5]})
    out = "\n".join(ai_check.check_midi(dst))
    vels = sorted({n.vel for n in apply_accent.midi_tools.load(dst).notes})
    assert "ベロシティ" not in out and vels == [68, 71, 74, 77]
