"""スクリプト共通: プロジェクトのパス、.env の読み込み。"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

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


def project_dir(song: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", song):
        sys.exit(f"曲名は英数字・_・- のみ使えます: {song!r}")
    return PROJECTS / song


def require_project(song: str) -> Path:
    p = project_dir(song)
    if not p.is_dir():
        sys.exit(f"プロジェクトが見つかりません: {p}(scripts/new_session.sh で日付-連番の名前で作成)")
    return p
