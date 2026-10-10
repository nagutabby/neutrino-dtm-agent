import sys

import pytest
from test_spec import set_meta


def run_apply(monkeypatch, *argv):
    import genre_apply

    monkeypatch.setattr(sys, "argv", ["genre_apply.py", *argv])
    genre_apply.main()


def write_profile(song_dir, gid, tracks, extra=""):
    """曲固有のジャンル定義(projects/<song>/genre/<id>.md)を書く。tracks は (spec, track, patch) の列。"""
    prof = song_dir / "genre"
    prof.mkdir(exist_ok=True)
    rows = "".join(f"  - {{spec: {sp}, track: {tr}, label: {tr}, patch: {pt}}}\n" for sp, tr, pt in tracks)
    (prof / f"{gid}.md").write_text(
        f"---\nid: {gid}\nname: {gid}\ntempo: {{range: [90, 140], default: 120}}\n{extra}tracks:\n{rows}---\n", encoding="utf-8"
    )


TEN = [
    ("03-drums", "drums", "kit_808"), ("04-bass", "bass", "sub808"), ("05-chords", "chords", "pad_saw"),
    ("06-melody", "melody", "bell"), ("10-hats", "hats", "kit_808"), ("11-stab", "stab", "stab"),
    ("12-arp", "arp", "synth_pluck"), ("13-choir", "choir", "choir"), ("14-fx", "fx", "riser"),
    ("15-impact", "impact", "impact"),
]


def test_no_predefined_genres():
    """ジャンル別の定義は予め用意しない(雛形のみ)。"""
    from common import ROOT

    assert [p.name for p in (ROOT / "docs" / "genres").glob("*.md")] == ["_template.md"]


def test_bars_for_length():
    import genre_apply

    assert genre_apply.bars_for(30, 130) == 16
    assert genre_apply.bars_for(120, 120) == 60


def test_genre_apply_sets_patches(song, monkeypatch, capsys):
    """ジャンルを反映すると concept と各トラック spec に patch が入り、検査が通る(終了コード 0)。"""
    import common

    write_profile(common.require_project("demo"), "dark", TEN)
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "dark", "--length-seconds", "90", "--run-mode", "step")
    assert e.value.code == 0
    assert "音色(パッチ)はすべて登録簿と一致" in capsys.readouterr().out
    specs = common.load_specs("demo")
    c = specs["00-concept"][0]
    assert c["run_mode"] == "step" and c["params"]["genre"] == "dark" and c["params"]["target_seconds"] == 90
    assert specs["04-bass"][0]["params"]["patch"] == "sub808"
    assert specs["03-drums"][0]["params"]["patch"] == "kit_808"
    assert len(c["params"]["tracks"]) >= 10 and "15-impact" in specs


def test_unknown_patch_is_an_error(song, monkeypatch, capsys):
    import common

    write_profile(common.require_project("demo"), "bad", [*TEN[:9], ("16-x", "x", "no_such_patch")])
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "bad")
    assert e.value.code == 2
    assert "no_such_patch" in capsys.readouterr().out


def test_genre_apply_changes_track_set(song, tmp_path, monkeypatch):
    """ジャンルで使うトラックが変わる: 使わない draft のトラック spec は消え、必要なものは足される。"""
    import common

    tiny = [("03-drums", "drums", "kit_acoustic"), ("10-fx", "fx", "riser"), *[(f"{n}-t{n}", f"t{n}", "synth_pluck") for n in range(11, 19)]]
    write_profile(common.require_project("demo"), "tiny", tiny)
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
    write_profile(common.require_project("demo"), "dark", TEN)
    with pytest.raises(SystemExit):
        run_apply(monkeypatch, "demo", "dark")
    assert common.load_specs("demo")["03-drums"][0]["status"] == "needs-revision"


def test_fewer_than_10_tracks_is_an_error(song, monkeypatch, capsys):
    import common

    write_profile(common.require_project("demo"), "few", TEN[:4])
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "few")
    assert e.value.code == 2 and "10 本以上" in capsys.readouterr().out
