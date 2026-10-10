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


def _chord_midi(path, ts=(4, 4)):
    from conftest import make_midi

    notes = []
    for bar, (root, third) in enumerate([(48, 4), (55, 4), (57, 3), (53, 4)] * 2):
        for p in (root, root + third, root + 7):
            notes.append((bar * 4, 4, p, 80))
    make_midi(path, notes, bpm=100, ts=ts)


def test_midi_analyze_finds_chord_functions(tmp_path):
    import reference_midi_analyze as rma

    p = tmp_path / "x.mid"
    _chord_midi(p)
    r = rma.analyze_file(p)
    assert r["key"] == "C 長調" and r["tempo_bpm"] == 100
    assert r["loop_4bars"][0] == ["I", "V", "vi", "IV"] and r["loop_4bars"][1] == 2


def test_midi_analyze_groups_parts(tmp_path):
    import mido
    import reference_midi_analyze as rma

    m = mido.MidiFile(ticks_per_beat=480)
    t = mido.MidiTrack()
    m.tracks.append(t)
    t.append(mido.Message("program_change", program=33, channel=0, time=0))
    for p in (36, 40, 43):
        t.append(mido.Message("note_on", note=p, velocity=80, channel=0, time=10))
        t.append(mido.Message("note_off", note=p, velocity=0, channel=0, time=10))
    t.append(mido.Message("note_on", note=36, velocity=90, channel=9, time=10))
    t.append(mido.Message("note_off", note=36, velocity=0, channel=9, time=10))
    p = tmp_path / "x.mid"
    m.save(p)
    assert set(rma.analyze_file(p)["parts"]) == {"ベース", "ドラム"}


def test_midi_fetch_rejects_bad_urls(song):
    import reference_midi_fetch as rmf

    for bad in ("http://a.com/x.mid", "https://a.com/page.html", "ftp://a.com/x.mid"):
        with pytest.raises(SystemExit):
            rmf.check_url(bad)
    assert rmf.safe_name("https://a.com/dir/My%20Song!.MID") == "My_Song.mid"


def test_midi_fetch_saves_and_refuses_overwrite(song, monkeypatch):
    import sys

    import reference_midi_fetch as rmf

    monkeypatch.setattr(rmf, "download", lambda url: b"MThd")
    url = "https://a.com/x.mid"
    monkeypatch.setattr(sys, "argv", ["f", "demo", url, "--title", "T"])
    rmf.main()
    d = song / "reference" / "midi"
    assert (d / "x.mid").read_bytes() == b"MThd" and "\"title\": \"T\"" in (d / "sources.jsonl").read_text()
    with pytest.raises(SystemExit, match="既に存在"):
        rmf.main()


def test_midi_fetch_download_rejects_non_midi(monkeypatch):
    import io

    import reference_midi_fetch as rmf

    monkeypatch.setattr(rmf.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(b"<html>"))
    with pytest.raises(SystemExit, match="MIDI ファイルではありません"):
        rmf.download("https://a.com/x.mid")


def test_separate_default_is_six_stem_model():
    import reference_separate as rs

    assert rs.MODELS["htdemucs_6s"][-2:] == ("guitar", "piano")
    assert rs.MODELS["htdemucs"] == ("drums", "bass", "other", "vocals")
