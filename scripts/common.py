"""スクリプト共通: プロジェクトのパス、spec の読み書き、MIDI ノート名変換。"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = Path(os.environ.get("DTM_PROJECTS", ROOT / "projects"))

# spec 要素: ファイル名 -> (表示名, 依存, トラック名 or None)
SPECS: dict[str, tuple[str, list[str], str | None]] = {
    "00-concept": ("コンセプト", [], None),
    "01-structure": ("曲構成(キー・テンポ・小節数)", ["00-concept"], None),
    "02-harmony": ("コード進行", ["01-structure"], None),
    "03-drums": ("ドラム", ["01-structure"], "drums"),
    "04-bass": ("ベース", ["01-structure", "02-harmony"], "bass"),
    "05-chords": ("コード楽器", ["01-structure", "02-harmony"], "chords"),
    "06-melody": ("歌メロ", ["01-structure", "02-harmony"], "melody"),
    "07-lyrics": ("歌詞", ["01-structure", "06-melody"], None),
    "08-vocal": ("ボーカル合成設定", ["06-melody", "07-lyrics"], "vocal"),
    "09-mix": ("ミックス", ["03-drums", "04-bass", "05-chords", "08-vocal"], None),
}
STATUSES = ("draft", "approved", "needs-revision")

_NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def project_dir(song: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", song):
        sys.exit(f"曲名は英数字・_・- のみ使えます: {song!r}")
    return PROJECTS / song


def require_project(song: str) -> Path:
    p = project_dir(song)
    if not p.is_dir():
        sys.exit(f"プロジェクトが見つかりません: {p}(scripts/new_song.sh {song} で作成)")
    return p


def safe_ref_dir(proj: Path, ref_id: str) -> Path:
    """projects/<song>/reference/<id>/ を返す(id は動画 ID 形式のみ)。"""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", ref_id):
        sys.exit(f"参考曲 ID は英数字・_・- のみ: {ref_id!r}")
    d = proj / "reference" / ref_id
    if not d.is_dir():
        sys.exit(f"参考曲が見つかりません: {d}(reference_fetch.sh で取得)")
    return d


def reject_foreign_project(path: str | Path, song: str) -> None:
    """入力ファイルが別の曲の projects/<other>/ 配下なら拒否(曲の取り違え防止)。"""
    rp = Path(path).resolve()
    root = PROJECTS.resolve()
    if rp.is_relative_to(root):
        owner = rp.relative_to(root).parts[0] if len(rp.relative_to(root).parts) > 1 else ""
        if owner and owner != song:
            sys.exit(f"別の曲のファイルです: {path}(projects/{owner}/)。対象は '{song}' です。曲を取り違えていませんか")


def note_to_midi(name: str | int) -> int:
    """'C2' -> 36(C4=60)。数値はそのまま返す。"""
    if isinstance(name, int):
        return name
    m = re.fullmatch(r"([A-Ga-g])([#b]?)(-?\d+)", str(name).strip())
    if not m:
        raise ValueError(f"音名を解釈できません: {name!r}(例: C2, F#3)")
    n = _NOTE[m.group(1).upper()] + {"#": 1, "b": -1, "": 0}[m.group(2)]
    return (int(m.group(3)) + 1) * 12 + n


def midi_to_note(n: int) -> str:
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return f"{names[n % 12]}{n // 12 - 1}"


def read_spec(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"\A---\n(.*?)\n---\n?(.*)\Z", text, re.S)
    if not m:
        raise ValueError(f"{path.name}: YAML frontmatter(--- で囲む)がありません")
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise ValueError(f"{path.name}: frontmatter がマッピングではありません")
    return meta, m.group(2)


def write_spec(path: Path, meta: dict, body: str) -> None:
    front = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).rstrip()
    path.write_text(f"---\n{front}\n---\n{body}", encoding="utf-8")


def load_specs(song: str) -> dict[str, tuple[dict, str]]:
    d = require_project(song) / "spec"
    out = {}
    for key in SPECS:
        p = d / f"{key}.md"
        if p.exists():
            out[key] = read_spec(p)
    return out


def deps_of(specs: dict[str, tuple[dict, str]], key: str) -> list[str]:
    """spec の依存元。その spec の frontmatter に depends_on があれば曲ごとの上書きとして優先する。"""
    declared = specs.get(key, ({}, ""))[0].get("depends_on")
    if isinstance(declared, list) and all(isinstance(d, str) and d in SPECS for d in declared):
        return declared
    return SPECS[key][1]


def track_files(song: str, track: str) -> list[Path]:
    d = require_project(song) / "tracks"
    return sorted(d.glob(f"*_{track}_v*.mid")) if d.is_dir() else []


def sidecar(mid: Path) -> dict:
    p = mid.with_suffix(".json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def version_of(mid: Path) -> int:
    m = re.search(r"_v(\d+)\.mid$", mid.name)
    return int(m.group(1)) if m else 0
