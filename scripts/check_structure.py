#!/usr/bin/env python3
"""曲の構成(セクションごとのコード進行・内容)を、ユーザーと確認したか検査する(音は出さない)。

  check_structure.py [work/structure.md] [--final] [--min-sections 3]

`work/structure.md` の表(1行 = 1セクション)を読む。書式は docs/structure-template.md。

  | セクション | 小節 | 雰囲気・役割 | コード進行 | 鳴らす楽器 | つなぎ | 確認 |
  |---|---|---|---|---|---|---|
  | イントロ | 1-8 | 静かに漂う | Fm7→Fm7→Dbmaj7→Dbmaj7 | ピアノ | riser | ✔ 2026-10-12 |

見るもの:
  - 必須の列が埋まっているか(セクション・小節・雰囲気・進行・楽器。「つなぎ」は空だと警告)
  - 「確認」の列に ✔(ユーザーが確認した印)があるか。無ければ、途中は警告、--final(完成前)では誤り
  - セクションが --min-sections 個以上あるか
  - 小節の範囲が重なっていないか(重なりは誤り、抜けは警告)
  - 単調でないか: 全セクションが同じ進行なら誤り、進行の種類が少ない・隣のセクションと進行も楽器も同じなら警告

終了コード: 0 = 問題なし、1 = 警告のみ、2 = 誤り(直す、またはユーザーに聞く)。
"""

from __future__ import annotations

import argparse
import re
import sys
from math import ceil
from pathlib import Path

from common import WORK

COLUMNS = ["セクション", "小節", "雰囲気・役割", "コード進行", "鳴らす楽器", "つなぎ", "確認"]
ARROW = re.compile(r"\s*(?:→|->|＞|>)\s*")
BARS = re.compile(r"^(\d+)\s*(?:[-〜~]\s*(\d+))?$")


def parse(text: str) -> list[dict]:
    """表の行を、列名をキーにした dict の一覧にする(ヘッダと区切り行は除く)。"""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.fullmatch(r"\|[\s:|-]+\|?", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0] == COLUMNS[0]:
            continue
        cells += [""] * (len(COLUMNS) - len(cells))
        rows.append(dict(zip(COLUMNS, cells, strict=False)))
    return rows


def bars_of(cell: str) -> tuple[int, int] | None:
    m = BARS.match(cell.replace(" ", ""))
    if not m:
        return None
    a = int(m.group(1))
    b = int(m.group(2) or a)
    return (a, b) if a <= b else None


def progression_of(cell: str) -> tuple[str, ...]:
    return tuple(c.lower().replace(" ", "") for c in ARROW.split(cell.strip()) if c.strip())


def check(rows: list[dict], final: bool, min_sections: int) -> tuple[list[str], list[str]]:
    """(誤り, 警告)を返す。"""
    errors: list[str] = []
    warns: list[str] = []
    if len(rows) < min_sections:
        errors.append(f"セクションが {len(rows)} 個しかありません({min_sections} 個以上を、ユーザーと決めてください)")
    ranges = []
    for r in rows:
        name = r["セクション"] or "(名前なし)"
        for col in ("セクション", "小節", "雰囲気・役割", "コード進行", "鳴らす楽器"):
            if not r[col]:
                errors.append(f"{name}: 「{col}」が空です(ユーザーに聞いて埋める)")
        if not r["つなぎ"]:
            warns.append(f"{name}: 「つなぎ」が空です(次のセクションへのつなぎ方。なければ「なし」と書く)")
        b = bars_of(r["小節"]) if r["小節"] else None
        if r["小節"] and b is None:
            errors.append(f"{name}: 「小節」を読めません({r['小節']!r}。例: 1-8)")
        elif b:
            ranges.append((b, name))
        if "✔" not in r["確認"]:
            msg = f"{name}: ユーザーの確認(✔)がありません"
            (errors if final else warns).append(msg)
    ranges.sort()
    for (a, b), (a2, b2) in zip((x[0] for x in ranges), (x[0] for x in ranges[1:]), strict=False):
        if a2 <= b:
            errors.append(f"小節の範囲が重なっています: {a}-{b} と {a2}-{b2}")
        elif a2 > b + 1:
            warns.append(f"小節 {b + 1}-{a2 - 1} がどのセクションにも入っていません")
    progs = [progression_of(r["コード進行"]) for r in rows if r["コード進行"]]
    if len(progs) >= 3 and len(set(progs)) == 1:
        errors.append("全セクションが同じコード進行です。単調になるので、セクションごとの変化をユーザーと決めてください")
    elif len(progs) >= 3 and len(set(progs)) < ceil(len(progs) / 2):
        warns.append(f"コード進行の種類が少ないです({len(set(progs))} 種 / {len(progs)} セクション)")
    for prev, cur in zip(rows, rows[1:], strict=False):
        if (prev["コード進行"] and prev["コード進行"] == cur["コード進行"]
                and prev["鳴らす楽器"] == cur["鳴らす楽器"]):
            warns.append(f"{prev['セクション']} → {cur['セクション']}: 進行も楽器も同じです(変化を付けるか、聞く)")
    return errors, warns


def main() -> int:
    ap = argparse.ArgumentParser(description="曲の構成をユーザーと確認したか検査する")
    ap.add_argument("file", nargs="?", default=str(WORK / "structure.md"))
    ap.add_argument("--final", action="store_true", help="完成前の検査(未確認や表なしを誤りにする)")
    ap.add_argument("--min-sections", type=int, default=3)
    a = ap.parse_args()
    f = Path(a.file)
    if not f.is_file():
        msg = f"{f} がありません。セクションごとの進行と内容をユーザーに聞いて、docs/structure-template.md の書式で作ってください"
        print(("誤り: " if a.final else "警告: ") + msg)
        return 2 if a.final else 1
    rows = parse(f.read_text(encoding="utf-8"))
    errors, warns = check(rows, a.final, a.min_sections)
    total = max((bars_of(r["小節"])[1] for r in rows if bars_of(r["小節"])), default=0)
    confirmed = sum("✔" in r["確認"] for r in rows)
    print(f"{f}: {len(rows)} セクション / {total} 小節 / 確認済み {confirmed}/{len(rows)}")
    for e in errors:
        print(f"誤り: {e}")
    for w in warns:
        print(f"警告: {w}")
    if not errors and not warns:
        print("問題なし")
    return 2 if errors else (1 if warns else 0)


if __name__ == "__main__":
    sys.exit(main())
