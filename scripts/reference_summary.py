#!/usr/bin/env python3
"""参考曲(ユーザーが挙げた3曲以上)の分析結果を1枚にまとめる。few-shot の「例」として spec 立案に使う。

使い方: reference_summary.py <song>
  入力: projects/<song>/reference/<id>/analysis.json(reference_run.sh が作る)、source.json
  出力: projects/<song>/reference/summary.md(曲ごとの数値表+共通点・違い)
抽象的な特徴(テンポ・キー・コード機能・盛り上がり・パート比)だけを扱う。旋律・歌詞・音符列は出さない。
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

from common import require_project


def load_refs(ref_root: Path) -> list[dict]:
    refs = []
    for d in sorted(p for p in ref_root.iterdir() if p.is_dir()) if ref_root.is_dir() else []:
        a = d / "analysis.json"
        if not a.is_file():
            continue
        src_p = d / "source.json"
        src = json.loads(src_p.read_text(encoding="utf-8").splitlines()[0]) if src_p.is_file() else {}
        refs.append({"id": d.name, "src": src, "r": json.loads(a.read_text(encoding="utf-8"))})
    return refs


def summarize(refs: list[dict]) -> str:
    rs = [x["r"] for x in refs]
    lines = ["# 参考曲まとめ(few-shot の例。私的な分析用・非公開)", ""]
    lines += ["| 曲 | テンポ | キー | よく出る4小節 | 明るさ(Hz) | 刻み(/秒) |", "|---|---|---|---|---|---|"]
    for x in refs:
        r, t = x["r"], x["src"].get("title", x["id"])
        loop = " - ".join(r["loop_4bars"][0]) if r.get("loop_4bars") else "-"
        lines.append(f"| {t} | {r['tempo_bpm']:g} | {r['key']} | {loop} | {r['brightness_hz']} | {r['onsets_per_sec']} |")
    lines += ["", "## 共通点(複数の例に共通する傾向だけを次の spec に反映する)", ""]
    if len(rs) >= 2:
        bpm = [r["tempo_bpm"] for r in rs]
        lines.append(f"- テンポ: {min(bpm):g}〜{max(bpm):g} BPM(中央値 {statistics.median(bpm):g}。倍/半分の誤検出に注意)")
    else:
        lines.append(f"- テンポ: {rs[0]['tempo_bpm']:g} BPM(例が1曲のみ。傾向とは言えない)")
    modes = Counter(r["key"].split()[-1] for r in rs)
    lines.append("- 長調/短調: " + "、".join(f"{m} {n}曲" for m, n in modes.most_common()))
    funcs = Counter()
    for r in rs:
        funcs.update({k: 1 for k, _ in (r.get("common_roman") or [])})
    common = [f"{k}({n}/{len(rs)}曲)" for k, n in funcs.most_common(6)]
    lines.append("- よく使われるコード機能: " + ("、".join(common) or "-"))
    loops = Counter(" - ".join(r["loop_4bars"][0]) for r in rs if r.get("loop_4bars"))
    if loops:
        lines.append("- 4小節の進行: " + "、".join(f"{k}({n}曲)" for k, n in loops.most_common(3)))
    curves = [r["energy_by_eighth"] for r in rs if r.get("energy_by_eighth")]
    if curves:
        mean = [round(statistics.mean(c[i] for c in curves), 2) for i in range(min(map(len, curves)))]
        lines.append("- 盛り上がりの形(曲を8分割した平均音量、最大=1): " + " → ".join(f"{v:g}" for v in mean))
    bal = [r["part_balance"] for r in rs if r.get("part_balance")]
    if bal:
        keys = sorted({k for b in bal for k in b})
        lines.append("- パート比の平均(分離後): " + "、".join(f"{k} {statistics.mean(b.get(k, 0) for b in bal):.0%}" for k in keys))
    lines += ["", "## 使い方", "",
              "- 例どうしの共通点は「このジャンル・雰囲気の型」として spec 立案の根拠に、違いは「ユーザーが選ぶ余地」として提示する。",
              "- 推定には誤差がある(テンポの倍/半分、コードの取り違え)。ユーザーの耳で確認してから spec に反映する。",
              "- 旋律・歌詞・特徴的なリズムパターンは複製しない。"]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    a = ap.parse_args()
    root = require_project(a.song) / "reference"
    refs = load_refs(root)
    if not refs:
        sys.exit(f"分析済みの参考曲がありません: {root}(reference_run.sh <song> <url> で取得・分析)")
    out = root / "summary.md"
    out.write_text(summarize(refs), encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
