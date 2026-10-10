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


def test_genre_apply_sets_patches(song, monkeypatch, capsys):
    """ジャンルを反映すると concept と各トラック spec に patch が入り、検査が通る(終了コード 0)。"""
    import common

    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "phonk", "--length-seconds", "90", "--run-mode", "step")
    assert e.value.code == 0
    assert "音色(パッチ)はすべて登録簿と一致" in capsys.readouterr().out
    specs = common.load_specs("demo")
    c = specs["00-concept"][0]
    assert c["run_mode"] == "step" and c["params"]["genre"] == "phonk" and c["params"]["target_seconds"] == 90
    assert specs["04-bass"][0]["params"]["patch"] == "sub808"
    assert specs["03-drums"][0]["params"]["patch"] == "kit_808"


def test_unknown_patch_is_an_error(song, monkeypatch, capsys):
    import common

    prof = common.require_project("demo") / "genre"
    prof.mkdir()
    (prof / "bad.md").write_text(
        "---\nid: bad\nname: Bad\ntempo: {range: [90, 110], default: 100}\n"
        "tracks:\n  - {spec: 04-bass, track: bass, patch: no_such_patch}\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "bad")
    assert e.value.code == 2
    assert "no_such_patch" in capsys.readouterr().out


def test_genre_apply_changes_track_set(song, tmp_path, monkeypatch):
    """ジャンルで使うトラックが変わる: 使わない draft のトラック spec は消え、必要なものは足される。"""
    import common

    prof = common.require_project("demo") / "genre"
    prof.mkdir()
    (prof / "tiny.md").write_text(
        "---\nid: tiny\nname: Tiny\ntempo: {range: [90, 110], default: 100}\n"
        "tracks:\n  - {spec: 03-drums, track: drums, patch: kit_acoustic}\n  - {spec: 10-fx, track: fx, label: FX, patch: riser}\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "tiny")
    assert e.value.code == 0
    specs = common.load_specs("demo")
    assert "10-fx" in specs and specs["10-fx"][0]["track"] == "fx"
    assert "04-bass" not in specs and "05-chords" not in specs and "06-melody" not in specs
    import patches

    assert patches.patch_id_of(specs, "10-fx") == "riser"


def test_changing_patch_of_ready_spec_needs_revision(song, monkeypatch):
    import common

    set_meta(common.require_project("demo"), "03-drums", status="ready", params={"patch": "kit_acoustic"})
    with pytest.raises(SystemExit):
        run_apply(monkeypatch, "demo", "phonk")
    assert common.load_specs("demo")["03-drums"][0]["status"] == "needs-revision"
