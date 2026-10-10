#!/usr/bin/env python3
"""Web 検索で見つけた類似曲の MIDI ファイル(直リンク)を参考用に保存する。私的な分析専用。

使い方: reference_midi_fetch.py <song> <https://…/file.mid> [--title 題名] [--note 出典メモ] [--dry-run]
  保存先: projects/<song>/reference/midi/<ファイル名>.mid、出典は同フォルダの sources.jsonl に追記
守ること: 直リンクを1ファイルずつ取得するだけ(サイトの巡回・一括取得はしない)。利用条件が分かれば --note に残す。
          取得物は .gitignore 済み(projects/*/reference/)。コミット・公開・再配布しない。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse

from common import require_project

MAX_BYTES = 1_000_000  # MIDI は通常数十 KB。大きすぎるものは別物とみなして拒否


def safe_name(url: str) -> str:
    base = Path(unquote(urlparse(url).path)).name
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(base).stem).strip("_")[:60]
    return f"{stem or 'midi'}.mid"


def check_url(url: str) -> None:
    u = urlparse(url)
    if u.scheme != "https" or not u.hostname:
        sys.exit(f"https の URL のみ対応です: {url!r}")
    if not u.path.lower().endswith((".mid", ".midi")):
        sys.exit(f".mid / .midi への直リンクのみ対応です: {url!r}(ページの URL ではなくファイルの URL を渡す)")


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "neutrino-dtm-agent/0.1 (private analysis)"})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (https のみ check_url で検査済み)
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        sys.exit(f"ファイルが大きすぎます(上限 {MAX_BYTES // 1000} KB): {url}")
    if not data.startswith(b"MThd"):
        sys.exit(f"MIDI ファイルではありません(先頭が MThd でない): {url}")
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("url")
    ap.add_argument("--title", default="")
    ap.add_argument("--note", default="", help="利用条件・ライセンス・どこが似ているか等")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    proj = require_project(a.song)
    check_url(a.url)
    out = proj / "reference" / "midi" / safe_name(a.url)
    if out.exists():
        sys.exit(f"既に存在します(上書きしません): {out}")
    print(f"取得: {a.url} → {out}")
    if a.dry_run:
        print("[dry-run] 保存しません")
        return
    data = download(a.url)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    with (out.parent / "sources.jsonl").open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {"file": out.name, "url": a.url, "title": a.title, "note": a.note},
                ensure_ascii=False,
            )
            + "\n"
        )
    print(f"保存: {out}({len(data)} bytes)")


if __name__ == "__main__":
    main()
