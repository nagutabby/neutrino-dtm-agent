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
