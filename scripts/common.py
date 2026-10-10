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


def load_dotenv() -> None:
    """リポジトリ直下の .env(KEY=VALUE)を環境変数の既定値として読む(シェル側は lib.sh が読む)。"""
    f = ROOT / ".env"
    if not f.is_file():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), os.path.expandvars(v.strip().strip("\"'")))

# 標準 spec 要素: ファイル名 -> (表示名, 依存, トラック名 or None)
# ジャンルによってはトラック spec を足す/省く(例: 10-fx)。曲に実在する spec ファイルが対象で、
# 標準にないキーは frontmatter の track / label / depends_on から読む(catalog 参照)。
SPECS: dict[str, tuple[str, list[str], str | None]] = {
    "00-concept": ("コンセプト", [], None),
    "01-structure": ("曲構成(キー・テンポ・小節数)", ["00-concept"], None),
    "02-harmony": ("コード進行", ["01-structure"], None),
    "03-drums": ("ドラム", ["01-structure"], "drums"),
    "04-bass": ("ベース", ["01-structure", "02-harmony"], "bass"),
    "05-chords": ("コード楽器", ["01-structure", "02-harmony"], "chords"),
    "06-melody": ("歌メロ/リード", ["01-structure", "02-harmony"], "melody"),
    "07-lyrics": ("歌詞", ["01-structure", "06-melody"], None),
    "08-vocal": ("ボーカル合成設定", ["06-melody", "07-lyrics"], "vocal"),
    "09-mix": ("ミックス", [], None),  # 依存の既定は「曲にあるトラック spec すべて」(deps_of)
}
REQUIRED_SPECS = ("00-concept", "01-structure", "02-harmony", "09-mix")
SPEC_KEY_RE = re.compile(r"\d{2}-[a-z0-9-]+")
# draft=未決 / ready=決定済み(この spec から生成してよい) / needs-revision=見直し中
STATUSES = ("draft", "ready", "needs-revision")
READY = "ready"

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
    """曲の spec/ にある NN-name.md をすべて読む(キー順)。"""
    d = require_project(song) / "spec"
    out = {}
    for p in sorted(d.glob("*.md")):
        if SPEC_KEY_RE.fullmatch(p.stem):
            out[p.stem] = read_spec(p)
    return out


VOCAL_ONLY = ("07-lyrics", "08-vocal")


def vocal_enabled(specs: dict[str, tuple[dict, str]]) -> bool:
    """00-concept の vocal が false ならインスト曲(歌詞・ボーカルの spec は対象外)。"""
    return specs.get("00-concept", ({}, ""))[0].get("vocal", True) is not False


def active_keys(specs: dict[str, tuple[dict, str]]) -> list[str]:
    on = vocal_enabled(specs)
    return [k for k in specs if on or k not in VOCAL_ONLY]


def catalog_entry(specs: dict[str, tuple[dict, str]], key: str) -> tuple[str, str | None]:
    """spec 1個の (表示名, トラック名 or None)。標準外のキーは frontmatter の label / track から。"""
    if key in SPECS:
        label, _, track = SPECS[key]
        return label, track
    meta = specs.get(key, ({}, ""))[0]
    return str(meta.get("label") or key), str(meta.get("track") or key.split("-", 1)[1])


def label_of(specs: dict[str, tuple[dict, str]], key: str) -> str:
    return catalog_entry(specs, key)[0]


def track_of(specs: dict[str, tuple[dict, str]], key: str) -> str | None:
    return catalog_entry(specs, key)[1]


def standard_deps(specs: dict[str, tuple[dict, str]], key: str) -> list[str]:
    if key == "09-mix":
        return [k for k in specs if k != key and track_of(specs, k)]
    return list(SPECS[key][1]) if key in SPECS else ["01-structure", "02-harmony"]


def deps_of(specs: dict[str, tuple[dict, str]], key: str) -> list[str]:
    """spec の依存元。その spec の frontmatter に depends_on があれば曲ごとの上書きとして優先する。
    インスト曲(vocal: false)では歌詞・ボーカルを依存から除く。"""
    declared = specs.get(key, ({}, ""))[0].get("depends_on")
    if isinstance(declared, list) and all(isinstance(d, str) and SPEC_KEY_RE.fullmatch(d) for d in declared):
        deps = declared
    else:
        deps = standard_deps(specs, key)
    return deps if vocal_enabled(specs) else [d for d in deps if d not in VOCAL_ONLY]


def concept_tracks(specs: dict[str, tuple[dict, str]]) -> list[dict]:
    """00-concept.params.tracks(ジャンルから決めたトラック計画)。"""
    t = (specs.get("00-concept", ({}, ""))[0].get("params") or {}).get("tracks")
    return [x for x in t if isinstance(x, dict)] if isinstance(t, list) else []


def track_files(song: str, track: str) -> list[Path]:
    d = require_project(song) / "tracks"
    return sorted(d.glob(f"*_{track}_v*.mid")) if d.is_dir() else []


def sidecar(mid: Path) -> dict:
    p = mid.with_suffix(".json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def version_of(mid: Path) -> int:
    m = re.search(r"_v(\d+)\.mid$", mid.name)
    return int(m.group(1)) if m else 0
