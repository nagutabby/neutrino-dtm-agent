"""スクリプト共通: 作業ディレクトリのパス、.env の読み込み。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(os.environ.get("SONICPI_WORK", ROOT / "work"))


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


def require_work() -> Path:
    if not WORK.is_dir():
        sys.exit(f"作業ディレクトリが見つかりません: {WORK}(mkdir work)")
    return WORK
