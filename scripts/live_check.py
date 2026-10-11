#!/usr/bin/env python3
"""Sonic Pi のコードの簡易検査(音は出さない)。

  live_check.py <file.rb> [...]

見るもの: シンセ名(use_synth / synth)・FX 名(with_fx)が内蔵にあるか、同じ行の引数名がそのシンセ/FX の
引数にあるか、`sleep` の無い live_loop(Sonic Pi がハングする典型)。正規表現による検査なので、
見落とし・誤検出がありうる(最終判断は Sonic Pi 本体のエラー表示)。問題があれば終了コード 2。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import sonicpi

COMMON = {"amp", "pan", "attack", "decay", "sustain", "release", "attack_level", "decay_level", "sustain_level",
          "env_curve", "cutoff", "res", "note", "slide", "note_slide", "amp_slide", "pan_slide", "cutoff_slide"}
USE_SYNTH = re.compile(r"\b(?:use_synth|synth)\s+:(\w+)(.*)")
WITH_FX = re.compile(r"\bwith_fx\s+:(\w+)(.*?)\bdo\b")
OPT = re.compile(r"\b(\w+):\s")


def check(text: str, info: dict) -> list[str]:
    problems = []
    lines = text.splitlines()
    for i, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0]
        for kind, rx, table in (("シンセ", USE_SYNTH, info["synths"]), ("FX", WITH_FX, info["fx"])):
            for m in rx.finditer(line):
                name, rest = m.group(1), m.group(2)
                if name not in table:
                    problems.append(f"{i}行目: 内蔵に無い{kind} :{name}(`sonicpi.py {'synths' if kind == 'シンセ' else 'fx'}` で一覧)")
                    continue
                if "use_synth" in line:
                    continue  # 引数は次の play 側にあるので検査しない
                allowed = set(table[name]) | COMMON
                for o in OPT.findall(rest + " "):
                    if o not in allowed and not o.endswith(("_slide", "_slide_shape", "_slide_curve")):
                        problems.append(f"{i}行目: :{name} に引数 {o}: はありません")
    # live_loop ... do ... end に sleep / sync があるか(ネストを数えて対応する end まで)
    i = 0
    while i < len(lines):
        if re.match(r"\s*live_loop\s+:\w+", lines[i]):
            depth, j, body = 0, i, []
            while j < len(lines):
                code = lines[j].split("#", 1)[0]
                # do ブロックに加え、行頭の if/unless/case/while/begin と `x = if ...` も end で閉じる
                opens = len(re.findall(r"\bdo\b", code))
                opens += 1 if re.match(r"\s*(if|unless|case|while|until|begin)\b", code) else 0
                opens += len(re.findall(r"=\s*(?:if|unless|case)\b", code))
                depth += opens - len(re.findall(r"\bend\b", code))
                body.append(code)
                if depth <= 0 and j > i:
                    break
                j += 1
            if not re.search(r"\b(sleep|sync|wait)\b", "\n".join(body)):
                problems.append(f"{i + 1}行目: live_loop に sleep(または sync)がありません。実行するとハングします")
            i = j
        i += 1
    return problems


def main() -> None:
    files = sys.argv[1:]
    if not files:
        sys.exit(__doc__)
    info = sonicpi.info()
    bad = False
    for f in files:
        probs = check(Path(f).read_text(encoding="utf-8"), info)
        for p in probs:
            print(f"{f}: {p}")
        bad = bad or bool(probs)
        if not probs:
            print(f"{f}: 問題なし")
    sys.exit(2 if bad else 0)


if __name__ == "__main__":
    main()
