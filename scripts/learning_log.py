#!/usr/bin/env python3
"""学習ログ(docs/learning-log.md)の索引の作り直しと検索。

  learning_log.py index              先頭の索引(<!-- INDEX:START --> と <!-- INDEX:END --> の間)を作り直す
  learning_log.py search <語> [...]   見出し・タグ・本文から探す(全部の語を含むエントリ。大文字小文字は区別しない)

エントリは `### L001 題` で始まり、`- タグ: #日本語名 #english-name …` の行を持つ(書式は learning-log.md の冒頭)。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from common import ROOT

LOG = ROOT / "docs" / "learning-log.md"
START, END = "<!-- INDEX:START -->", "<!-- INDEX:END -->"
HEAD = re.compile(r"^### (L\d+)\s+(.*)$")
TAG_LINE = re.compile(r"^- タグ:(.*)$")
TAG = re.compile(r"#[^\s#]+")


def parse(text: str) -> list[dict]:
    """エントリ(番号・題・タグ・本文)の一覧。索引より前の説明部分は含めない。"""
    entries: list[dict] = []
    for line in text.splitlines():
        m = HEAD.match(line)
        if m:
            entries.append({"id": m.group(1), "title": m.group(2).strip(), "tags": [], "body": [line]})
            continue
        if entries:
            entries[-1]["body"].append(line)
            t = TAG_LINE.match(line)
            if t:
                entries[-1]["tags"] += TAG.findall(t.group(1))
    return entries


def build_index(entries: list[dict]) -> str:
    out = ["**エントリ一覧**", "", "| 番号 | 題 | タグ |", "|---|---|---|"]
    for e in entries:
        out.append(f"| {e['id']} | {e['title']} | {' '.join(e['tags'])} |")
    by_tag: dict[str, list[str]] = {}
    for e in entries:
        for t in e["tags"]:
            by_tag.setdefault(t, []).append(e["id"])
    out += ["", "**タグ索引**(五十音・アルファベット順)", "", "| タグ | エントリ |", "|---|---|"]
    for t in sorted(by_tag, key=str.lower):
        out.append(f"| {t} | {', '.join(by_tag[t])} |")
    return "\n".join(out)


def apply_index(text: str) -> str:
    if START not in text or END not in text:
        raise SystemExit(f"{START} と {END} の目印が見つかりません")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{START}\n{build_index(parse(text))}\n{END}{tail}"


def search(entries: list[dict], words: list[str]) -> list[dict]:
    ws = [w.lower().lstrip("#") for w in words]
    hits = []
    for e in entries:
        blob = "\n".join(e["body"]).lower()
        if all(w in blob for w in ws):
            hits.append(e)
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="学習ログの索引・検索")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index", help="索引を作り直す")
    sp = sub.add_parser("search", help="語で探す")
    sp.add_argument("words", nargs="+")
    ap.add_argument("--file", default=str(LOG))
    a = ap.parse_args()
    f = Path(a.file)
    text = f.read_text(encoding="utf-8")
    if a.cmd == "index":
        new = apply_index(text)
        f.write_text(new, encoding="utf-8")
        print(f"索引を更新しました: {len(parse(text))} エントリ")
        return 0
    entries = parse(text)
    hits = search(entries, a.words)
    if not hits:
        print("見つかりませんでした(別の語、または英語名・日本語名で探す)")
        return 1
    for e in hits:
        print(f"{e['id']} {e['title']}")
        print(f"  タグ: {' '.join(e['tags'])}")
        lines = [ln.strip() for ln in e["body"][1:] if any(w.lower().lstrip('#') in ln.lower() for w in a.words)]
        for ln in lines[:3]:
            print(f"  | {ln[:110]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
