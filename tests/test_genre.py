import sys

import pytest
from test_spec import set_meta


def run_apply(monkeypatch, *argv):
    import genre_apply

    monkeypatch.setattr(sys, "argv", ["genre_apply.py", *argv])
    genre_apply.main()


def write_profile(song_dir, gid, extra=""):
    """曲固有のジャンル定義(projects/<song>/genre/<id>.md)を書く。トラックと音はユーザー指定なので持たない。"""
    prof = song_dir / "genre"
    prof.mkdir(exist_ok=True)
    (prof / f"{gid}.md").write_text(
        f"---\nid: {gid}\nname: {gid}\ntempo: {{range: [90, 140], default: 120}}\n{extra}---\n", encoding="utf-8"
    )


def write_inputs(song_dir, tracks, progression=()):
    """ユーザーの最初の指示(user_inputs.yaml)を書く。tracks は (spec, track, patch) の列。"""
    import yaml

    data = {
        "progression": [{"bars": b, "chord": c} for b, c in progression],
        "tracks": [{"spec": sp, "track": tr, "label": tr, "sound": f"{tr} の音", "patch": pt} for sp, tr, pt in tracks],
    }
    (song_dir / "user_inputs.yaml").write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


TRACKS = [("03-drums", "drums", "kit"), ("04-bass", "bass", "lowsaw"), ("06-melody", "melody", "keys")]


@pytest.fixture
def demo(song_with_patches):
    return song_with_patches


def test_no_predefined_genres():
    """ジャンル別の定義は予め用意しない(雛形のみ)。"""
    from common import ROOT

    assert [p.name for p in (ROOT / "docs" / "genres").glob("*.md")] == ["_template.md"]


def test_bars_for_length():
    import genre_apply

    assert genre_apply.bars_for(30, 130) == 16
    assert genre_apply.bars_for(120, 120) == 60


def test_genre_apply_uses_only_user_tracks_and_progression(demo, monkeypatch, capsys):
    """トラック・音・コード進行はユーザー指定だけが反映され、検査が通る(終了コード 0)。"""
    import common

    write_profile(demo, "dark")
    write_inputs(demo, TRACKS, [(2, "Am"), (2, "F")])
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "dark", "--length-seconds", "90", "--run-mode", "step")
    assert e.value.code == 0
    assert "この曲の登録簿と一致" in capsys.readouterr().out
    specs = common.load_specs("demo")
    c = specs["00-concept"][0]
    assert c["run_mode"] == "step" and c["params"]["genre"] == "dark" and c["params"]["target_seconds"] == 90
    assert [t["track"] for t in c["params"]["tracks"]] == ["drums", "bass", "melody"]
    assert specs["04-bass"][0]["params"]["patch"] == "lowsaw" and specs["04-bass"][0]["sound"] == "bass の音"
    assert "05-chords" not in specs  # ユーザーが指定していないトラックは作らない(draft は消える)
    assert specs["02-harmony"][0]["progression"] == [{"bars": 2, "chord": "Am"}, {"bars": 2, "chord": "F"}]


def test_genre_tracks_are_ignored(demo, monkeypatch):
    """ジャンル定義にトラック案があっても使わない(AI はサジェストしない)。"""
    import common

    write_profile(demo, "dark", extra="tracks:\n  - {spec: 05-chords, track: chords, patch: keys}\n")
    write_inputs(demo, TRACKS[:1])
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "dark")
    assert e.value.code == 0
    assert [t["track"] for t in common.load_specs("demo")["00-concept"][0]["params"]["tracks"]] == ["drums"]


def test_no_user_tracks_is_an_error(demo, monkeypatch, capsys):
    write_profile(demo, "dark")
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "dark")
    assert e.value.code == 2 and "ユーザーが指示" in capsys.readouterr().out


def test_track_without_patch_is_an_error(demo, monkeypatch, capsys):
    write_profile(demo, "dark")
    write_inputs(demo, [("04-bass", "bass", "")])
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "dark")
    assert e.value.code == 2 and "patch がありません" in capsys.readouterr().out


def test_no_progression_leaves_harmony_untouched(demo, monkeypatch):
    import common

    write_profile(demo, "dark")
    write_inputs(demo, TRACKS)
    with pytest.raises(SystemExit):
        run_apply(monkeypatch, "demo", "dark")
    assert not common.load_specs("demo")["02-harmony"][0]["progression"]


def test_unknown_patch_is_an_error(demo, monkeypatch, capsys):
    write_profile(demo, "bad")
    write_inputs(demo, [*TRACKS, ("16-x", "x", "no_such_patch")])
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "bad")
    assert e.value.code == 2
    assert "no_such_patch" in capsys.readouterr().out


def test_other_projects_patch_is_not_reused(song, monkeypatch, capsys):
    """この曲の登録簿に無い音色は、リポジトリ共通の音色があっても使えない。"""
    write_profile(song, "dark")
    write_inputs(song, [("04-bass", "bass", "sub808")])
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "dark")
    assert e.value.code == 2 and "流用しない" in capsys.readouterr().out


def test_user_can_add_extra_tracks(demo, monkeypatch):
    import common

    write_profile(demo, "tiny")
    write_inputs(demo, [("03-drums", "drums", "kit"), ("10-fx", "fx", "keys")])
    with pytest.raises(SystemExit) as e:
        run_apply(monkeypatch, "demo", "tiny")
    assert e.value.code == 0
    specs = common.load_specs("demo")
    assert specs["10-fx"][0]["track"] == "fx"
    assert "04-bass" not in specs and "05-chords" not in specs and "06-melody" not in specs


def test_changing_patch_of_ready_spec_needs_revision(demo, monkeypatch):
    import common

    set_meta(demo, "03-drums", status="ready", params={"patch": "keys"})
    write_profile(demo, "dark")
    write_inputs(demo, TRACKS)
    with pytest.raises(SystemExit):
        run_apply(monkeypatch, "demo", "dark")
    assert common.load_specs("demo")["03-drums"][0]["status"] == "needs-revision"


def test_changed_progression_of_ready_harmony_needs_revision(demo, monkeypatch):
    import common

    set_meta(demo, "02-harmony", status="ready", progression=[{"bars": 4, "chord": "C"}])
    write_profile(demo, "dark")
    write_inputs(demo, TRACKS, [(4, "Am")])
    with pytest.raises(SystemExit):
        run_apply(monkeypatch, "demo", "dark")
    h = common.load_specs("demo")["02-harmony"][0]
    assert h["status"] == "needs-revision" and h["progression"] == [{"bars": 4, "chord": "Am"}]
