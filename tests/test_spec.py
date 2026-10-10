import json

import decide  # noqa: F401  (import check)
from conftest import make_midi


def set_meta(d, key, **kv):
    import common

    p = d / "spec" / f"{key}.md"
    meta, body = common.read_spec(p)
    meta.update(kv)
    common.write_spec(p, meta, body)


def ready_all(d, keys):
    for k in keys:
        set_meta(d, k, status="ready")


def test_templates_parse_and_check_clean(song):
    import spec_check

    errors, _ = spec_check.check("demo")
    assert errors == []


def test_ready_with_unready_dep_is_error(song):
    import spec_check

    set_meta(song, "04-bass", status="ready")
    errors, _ = spec_check.check("demo")
    assert any("依存元が ready ではありません" in e for e in errors)


def test_register_requires_ready(song, tmp_path, monkeypatch):
    import subprocess
    import sys

    from conftest import ROOT

    midi = tmp_path / "b.mid"
    make_midi(midi, [(0, 1, 36, 90)])
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/register_track.py"), "demo", "04-bass", str(midi)],
        env={**__import__("os").environ, "DTM_PROJECTS": str(song.parent)},
        capture_output=True, text=True,
    )
    assert r.returncode != 0 and "ready" in (r.stderr + r.stdout)


def test_stale_and_tempo_mismatch(song):
    import spec_check

    keys = ["00-concept", "01-structure", "02-harmony", "04-bass"]
    ready_all(song, keys)
    mid = song / "tracks" / "04_bass_v1.mid"
    make_midi(mid, [(0, 1, 36, 90), (4, 1, 40, 90)], bpm=100)
    mid.with_suffix(".json").write_text(json.dumps({"spec": "04-bass", "spec_versions": {"04-bass": 1, "01-structure": 1, "02-harmony": 1}}))
    errors, warns = spec_check.check("demo")
    assert any("テンポ" in e for e in errors)
    set_meta(song, "04-bass", version=2)
    _, warns = spec_check.check("demo")
    assert any("[stale]" in w for w in warns)


def test_note_names():
    import common

    assert common.note_to_midi("C4") == 60
    assert common.note_to_midi("C1") == 24
    assert common.midi_to_note(36) == "C2"


def test_register_rejects_midi_from_other_song(song, tmp_path):
    import pytest
    import register_track

    other = tmp_path / "other" / "tracks"
    other.mkdir(parents=True)
    make_midi(other / "x.mid", [(0, 1, 36, 90)])
    with pytest.raises(SystemExit, match="別の曲"):
        import sys

        sys.argv = ["register_track.py", "demo", "03-drums", str(other / "x.mid")]
        register_track.main()


def test_depends_on_override_per_song(song):
    import common
    import spec_check
    import spec_status

    d = common.require_project("demo")
    ready_all(d, ["00-concept", "01-structure", "02-harmony", "03-drums", "04-bass", "05-chords", "06-melody"])
    assert "09-mix" not in spec_status.next_candidates(common.load_specs("demo"))
    set_meta(d, "09-mix", depends_on=["03-drums", "04-bass", "05-chords", "06-melody"])
    specs = common.load_specs("demo")
    assert common.deps_of(specs, "09-mix") == ["03-drums", "04-bass", "05-chords", "06-melody"]
    assert "09-mix" in spec_status.next_candidates(specs)
    _, warns = spec_check.check("demo")
    assert any("09-mix" in w and "上書き" in w for w in warns)


def test_instrumental_skips_vocal_specs(song):
    import common
    import spec_check
    import spec_status

    d = common.require_project("demo")
    set_meta(d, "00-concept", vocal=False)
    ready_all(d, ["00-concept", "01-structure", "02-harmony", "03-drums", "04-bass", "05-chords", "06-melody"])
    specs = common.load_specs("demo")
    assert common.active_keys(specs) == [k for k in common.SPECS if k not in common.VOCAL_ONLY]
    assert "08-vocal" not in common.deps_of(specs, "09-mix")
    assert spec_status.next_candidates(specs) == ["09-mix"]
    errors, warns = spec_check.check("demo")
    assert not errors and not any("08-vocal" in w or "07-lyrics" in w or "09-mix" in w for w in warns)


def test_genre_tracks_are_dynamic(song):
    """標準外のトラック spec(10-fx)を足しても、catalog・mix の依存・stem 名に反映される。"""
    import common
    import spec_status

    d = common.require_project("demo")
    (d / "spec" / "10-fx.md").write_text(
        "---\nstatus: draft\nversion: 1\nlabel: エフェクト\ntrack: fx\ndepends_on: [01-structure]\nparams:\n  patch: pluck\n---\n# fx\n",
        encoding="utf-8",
    )
    specs = common.load_specs("demo")
    assert common.track_of(specs, "10-fx") == "fx" and common.label_of(specs, "10-fx") == "エフェクト"
    assert "10-fx" in common.deps_of(specs, "09-mix")
    ready_all(d, ["00-concept", "01-structure"])
    assert "10-fx" in spec_status.next_candidates(common.load_specs("demo"))


def test_removed_track_spec_is_not_required(song):
    """ジャンルが使わないトラック(spec ファイルなし)は検査・依存の対象外。"""
    import common
    import spec_check

    d = common.require_project("demo")
    (d / "spec" / "05-chords.md").unlink()
    specs = common.load_specs("demo")
    assert "05-chords" not in common.deps_of(specs, "09-mix")
    errors, warns = spec_check.check("demo")
    assert not errors and not any("05-chords" in w for w in warns)


def test_decide_requires_ready_deps(song, monkeypatch):
    import sys

    import pytest

    monkeypatch.setattr(sys, "argv", ["decide.py", "demo", "02-harmony"])
    with pytest.raises(SystemExit, match="依存元"):
        decide.main()
    ready_all(song, ["00-concept", "01-structure"])
    decide.main()
    import common

    assert common.load_specs("demo")["02-harmony"][0]["status"] == "ready"
