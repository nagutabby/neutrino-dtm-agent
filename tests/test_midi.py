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
