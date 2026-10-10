import json

import approve  # noqa: F401  (import check)
from conftest import make_midi


def set_meta(d, key, **kv):
    import common

    p = d / "spec" / f"{key}.md"
    meta, body = common.read_spec(p)
    meta.update(kv)
    common.write_spec(p, meta, body)


def approve_all(d, keys):
    for k in keys:
        set_meta(d, k, status="approved")


def test_templates_parse_and_check_clean(song):
    import spec_check

    errors, _ = spec_check.check("demo")
    assert errors == []


def test_approved_with_unapproved_dep_is_error(song):
    import spec_check

    set_meta(song, "04-bass", status="approved")
    errors, _ = spec_check.check("demo")
    assert any("依存元が未承認" in e for e in errors)


def test_register_requires_approved(song, tmp_path, monkeypatch):
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
    assert r.returncode != 0 and "approved" in (r.stderr + r.stdout)


def test_stale_and_tempo_mismatch(song):
    import spec_check

    keys = ["00-concept", "01-structure", "02-harmony", "04-bass"]
    approve_all(song, keys)
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
