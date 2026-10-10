import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*args):
    return subprocess.run(["bash", *args], cwd=ROOT, capture_output=True, text=True)


def test_render_track_rejects_path_escape():
    r = run("scripts/render_track.sh", "demo", "../other/04_bass_v1")
    assert r.returncode != 0 and ("使えません" in r.stderr or "プロジェクトがありません" in r.stderr)


def test_synth_rejects_path_escape(tmp_path):
    (ROOT / "projects" / "_guardtest").mkdir(exist_ok=True)
    try:
        r = run("scripts/synth.sh", "_guardtest", "../x")
        assert r.returncode != 0 and "使えません" in r.stderr
    finally:
        (ROOT / "projects" / "_guardtest").rmdir()


def test_mix_rejects_non_numeric_step():
    (ROOT / "projects" / "_guardtest").mkdir(exist_ok=True)
    try:
        r = run("scripts/mix_tracks.sh", "_guardtest", "1/../x")
        assert r.returncode != 0 and "数字のみ" in r.stderr
    finally:
        (ROOT / "projects" / "_guardtest").rmdir()


def test_reference_fetch_rejects_non_youtube_url():
    (ROOT / "projects" / "_guardtest").mkdir(exist_ok=True)
    try:
        r = run("scripts/reference_fetch.sh", "_guardtest", "https://example.com/x")
        assert r.returncode != 0 and "YouTube" in r.stderr
    finally:
        (ROOT / "projects" / "_guardtest").rmdir()
