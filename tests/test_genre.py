import sys

import pytest
from test_spec import set_meta


def run_apply(monkeypatch, *argv):
    import genre_apply

    monkeypatch.setattr(sys, "argv", ["genre_apply.py", *argv])
    genre_apply.main()


def test_genre_profiles_parse():
    from common import ROOT, read_spec

    for p in (ROOT / "docs" / "genres").glob("*.md"):
        meta, _ = read_spec(p)
        assert meta["id"] == p.stem or p.stem == "_template"
        assert meta["tracks"] and meta["tempo"]["range"][0] <= meta["tempo"]["default"] <= meta["tempo"]["range"][1]


def test_bars_for_length():
    import genre_apply

    assert genre_apply.bars_for(30, 130) == 16
    assert genre_apply.bars_for(120, 120) == 60


def test_missing_soundfont_stops_with_requirements(song, tmp_path, monkeypatch, capsys):
    """phonk 専用 SoundFont が無い環境では、必要な内容を表示して終了コード 3(作業を中断)。"""
    monkeypatch.setenv("SOUNDFONT_DIR", str(tmp_path / "empty"))
    monkeypatch.delenv("SF_PHONK", raising=False)
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "phonk", "--length-seconds", "90", "--run-mode", "step")
    assert e.value.code == 3
    out = capsys.readouterr().out
    assert "足りない SoundFont" in out and "phonk" in out and "808" in out and "中断" in out
    import common

    c = common.load_specs("demo")["00-concept"][0]
    assert c["run_mode"] == "step" and c["params"]["genre"] == "phonk" and c["params"]["target_seconds"] == 90


def test_soundfont_found_by_keyword(song, tmp_path, monkeypatch, capsys):
    d = tmp_path / "sf"
    d.mkdir()
    (d / "My-Phonk-Kit.sf2").write_bytes(b"x")
    monkeypatch.setenv("SOUNDFONT_DIR", str(d))
    monkeypatch.delenv("SF_PHONK", raising=False)
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "phonk")
    assert e.value.code == 0
    assert "My-Phonk-Kit.sf2" in capsys.readouterr().out


def test_genre_apply_changes_track_set(song, tmp_path, monkeypatch):
    """ジャンルで使うトラックが変わる: 使わない draft のトラック spec は消え、必要なものは足される。"""
    import common

    monkeypatch.setenv("SOUNDFONT_DIR", str(tmp_path))
    monkeypatch.setenv("SF_GM", str(tmp_path / "gm.sf2"))
    (tmp_path / "gm.sf2").write_bytes(b"x")
    prof = common.require_project("demo") / "genre"
    prof.mkdir()
    (prof / "tiny.md").write_text(
        "---\nid: tiny\nname: Tiny\ntempo: {range: [90, 110], default: 100}\n"
        "tracks:\n  - {spec: 03-drums, track: drums, soundfont: gm}\n  - {spec: 10-fx, track: fx, label: FX, soundfont: gm}\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "tiny")
    assert e.value.code == 0
    specs = common.load_specs("demo")
    assert "10-fx" in specs and specs["10-fx"][0]["track"] == "fx"
    assert "04-bass" not in specs and "05-chords" not in specs and "06-melody" not in specs
    assert common.soundfont_id_of(specs, "10-fx") == "gm"


def test_changing_soundfont_of_ready_spec_needs_revision(song, tmp_path, monkeypatch):
    import common

    monkeypatch.setenv("SOUNDFONT_DIR", str(tmp_path))
    (tmp_path / "phonk.sf2").write_bytes(b"x")
    set_meta(common.require_project("demo"), "03-drums", status="ready", params={"soundfont": "gm"})
    with pytest.raises(SystemExit):
        run_apply(monkeypatch, "demo", "phonk")
    assert common.load_specs("demo")["03-drums"][0]["status"] == "needs-revision"
