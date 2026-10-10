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


def test_separate_default_is_six_stem_model():
    import reference_separate as rs

    assert rs.MODELS["htdemucs_6s"][-2:] == ("guitar", "piano")
    assert rs.MODELS["htdemucs"] == ("drums", "bass", "other", "vocals")


def test_reference_summary_finds_common_traits(song):
    import json

    import reference_summary as rs

    def put(rid, bpm, key, loop):
        d = song / "reference" / rid
        d.mkdir(parents=True)
        (d / "source.json").write_text(json.dumps({"title": f"t{rid}"}) + "\n")
        (d / "analysis.json").write_text(json.dumps({
            "tempo_bpm": bpm, "key": key, "loop_4bars": [loop, 2], "common_roman": [["I", 3], ["V", 2]],
            "brightness_hz": 2000, "onsets_per_sec": 3.0, "energy_by_eighth": [0.5] * 8,
            "part_balance": {"bass": 0.5, "drums": 0.5}}))

    put("a", 80, "C 長調", ["I", "V", "vi", "IV"])
    put("b", 90, "G 長調", ["I", "V", "vi", "IV"])
    md = rs.summarize(rs.load_refs(song / "reference"))
    assert "80〜90 BPM" in md and "長調 2曲" in md and "I - V - vi - IV(2曲)" in md
