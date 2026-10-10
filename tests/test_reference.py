import pytest
import reference_analyze as ra


def test_roman_numerals_relative_to_major_tonic():
    assert ra.roman(7, "", 0) == "V"  # C メジャーの G
    assert ra.roman(9, "m", 0) == "vi"  # Am
    assert ra.roman(10, "", 0) == "♭VII"


def test_key_estimation_prefers_tonic():
    np = pytest.importorskip("numpy")
    chroma = np.zeros(12)
    chroma[[0, 4, 7]] = 1.0
    chroma[[2, 5, 9, 11]] = 0.3
    tonic, mode, _ = ra.estimate_key(chroma)
    assert (tonic, mode) == (0, "長調")


def test_ref_id_rejects_path_escape(tmp_path):
    import common

    with pytest.raises(SystemExit):
        common.safe_ref_dir(tmp_path, "../x")


def test_separate_requires_audio(song, monkeypatch):
    import sys

    import reference_separate

    (song / "reference" / "abc").mkdir(parents=True)
    monkeypatch.setattr(sys, "argv", ["reference_separate.py", "demo", "abc"])
    with pytest.raises(SystemExit, match="音声がありません"):
        reference_separate.main()


def test_separate_refuses_overwrite(song, monkeypatch):
    import sys

    import reference_separate

    d = song / "reference" / "abc"
    (d / "stems").mkdir(parents=True)
    (d / "audio.wav").write_bytes(b"")
    (d / "stems" / "bass.wav").write_bytes(b"")
    monkeypatch.setattr(sys, "argv", ["reference_separate.py", "demo", "abc"])
    with pytest.raises(SystemExit, match="既に存在"):
        reference_separate.main()


def test_diatonic_fit_prefers_major_when_tonic_chord_is_major():
    chords = [(9, ""), (2, ""), (9, ""), (2, "")]  # A, D, A, D
    assert ra.diatonic_fit(chords, 9, "長調") > ra.diatonic_fit(chords, 9, "短調")


def test_ambiguous_third_matches_either_quality():
    assert ra.diatonic_fit([(0, "5")], 0, "長調") == 1.0
    assert ra.diatonic_fit([(0, "5")], 9, "短調") == 1.0


def test_to_midi_builds_pinned_muscriptor_cmd(song):
    import reference_to_midi as r2m

    cmd = r2m.build_cmd("a.wav", "o.mid", "large")
    assert cmd[:4] == ["uvx", "--from", r2m.MUSCRIPTOR, "muscriptor"]
    assert "==" in r2m.MUSCRIPTOR and cmd[-2:] == ["--model", "large"]


def test_to_midi_runs_and_refuses_overwrite(song, monkeypatch):
    import subprocess
    import sys

    import reference_to_midi as r2m

    d = song / "reference" / "abc"
    d.mkdir(parents=True)
    (d / "audio.wav").write_bytes(b"")
    calls = []

    def fake_run(cmd, check=False):
        calls.append(cmd)
        (d / "transcription.mid").write_bytes(b"MThd")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(r2m.subprocess, "run", fake_run)
    monkeypatch.setattr(r2m.shutil, "which", lambda _: "/usr/bin/uvx")
    monkeypatch.setattr(sys, "argv", ["reference_to_midi.py", "demo", "abc"])
    r2m.main()
    assert len(calls) == 1
    with pytest.raises(SystemExit, match="既に存在"):
        r2m.main()


def test_to_midi_reports_auth_hint_on_failure(song, monkeypatch):
    import subprocess
    import sys

    import reference_to_midi as r2m

    d = song / "reference" / "abc"
    d.mkdir(parents=True)
    (d / "audio.wav").write_bytes(b"")
    monkeypatch.setattr(r2m.subprocess, "run", lambda cmd, check=False: subprocess.CompletedProcess(cmd, 1))
    monkeypatch.setattr(r2m.shutil, "which", lambda _: "/usr/bin/uvx")
    monkeypatch.setattr(sys, "argv", ["reference_to_midi.py", "demo", "abc"])
    with pytest.raises(SystemExit, match="hf auth login"):
        r2m.main()


def test_summarize_midi_groups_by_instrument(tmp_path):
    import mido

    m = mido.MidiFile(ticks_per_beat=480)
    t = mido.MidiTrack()
    m.tracks.append(t)
    t.append(mido.Message("program_change", program=33, channel=0, time=0))
    for p in (36, 40, 43):
        t.append(mido.Message("note_on", note=p, velocity=80, channel=0, time=10))
        t.append(mido.Message("note_off", note=p, velocity=0, channel=0, time=10))
    t.append(mido.Message("note_on", note=36, velocity=90, channel=9, time=10))
    p = tmp_path / "x.mid"
    m.save(p)
    out = ra.summarize_midi(p, 10.0)
    assert set(out) == {"ベース", "ドラム"}
    assert out["ドラム"]["register"] is None and out["ベース"]["notes"] == 3


def test_separate_default_is_six_stem_model():
    import reference_separate as rs

    assert rs.MODELS["htdemucs_6s"][-2:] == ("guitar", "piano")
    assert rs.MODELS["htdemucs"] == ("drums", "bass", "other", "vocals")
