#!/usr/bin/env python3
"""グリッド記法のコーディング規約(docs/coding-rules.md)に沿っているかの簡易検査(音は出さない)。

  check_grid.py <file.rb> [...]

見るもの(正規表現による検査なので、見落とし・誤検出がありうる):
  誤り: グリッド文字列のマス数が 16 の倍数でない(1小節 = 16マス)/ grid_chop の `from:` の個数が音の数と違う /
        `from:` が元の wav(grid_clip の拍数)をはみ出す
  警告: `define` の名前が grid_ で始まらない / live_loop に grid_play・grid_chop と `sleep` が両方ある(二重に待つ) /
        use_bpm が無い・複数ある / 演算(.mask .shift .accent .bar、グリッド文字列の `+`)の使用(必要なときだけ使う規約)

終了コード: 0 = 問題なし、1 = 警告のみ、2 = 誤り。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

GRID_CHARS = "xXo.-| "
HITS = "xXo"
STEP = 0.25  # 1マス = 16分音符 = 0.25拍
STRING = re.compile(r'"([^"\\\n]*)"')
GRID_PLAY_OR_CHOP = re.compile(r"\bgrid_(?:play|chop)\b")
OPERATOR = re.compile(r"\.(?:mask|shift|accent|bar)\s*[(\s]")


def strip_comment(line: str) -> str:
    """文字列の外にある # 以降を落とす。"""
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote and line[i - 1] != "\\":
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#":
            return line[:i]
    return line


def is_grid(s: str) -> bool:
    """グリッド文字列らしいか: 使える文字だけで、音符(x X o)を含み、8マス以上。"""
    cells = cells_of(s)
    return bool(s) and all(c in GRID_CHARS for c in s) and len(cells) >= 8 and any(c in HITS for c in cells)


def cells_of(pattern: str) -> str:
    return "".join(c for c in pattern if c not in " |\t\n")


def hit_beats(pattern: str) -> list[float]:
    """各音の長さ(拍)。音 = x X o、直後に続く - ぶんだけ伸びる。"""
    cells = cells_of(pattern)
    out = []
    for i, c in enumerate(cells):
        if c in HITS:
            n = 1
            while i + n < len(cells) and cells[i + n] == "-":
                n += 1
            out.append(n * STEP)
    return out


def live_loop_bodies(lines: list[str]) -> list[tuple[int, str]]:
    """(開始行番号, 本文) の一覧。do / end の入れ子を数えて対応する end まで。"""
    out, i = [], 0
    while i < len(lines):
        if re.match(r"\s*live_loop\s+:\w+", strip_comment(lines[i])):
            depth, j, body = 0, i, []
            while j < len(lines):
                code = strip_comment(lines[j])
                opens = len(re.findall(r"\bdo\b", code))
                opens += 1 if re.match(r"\s*(if|unless|case|while|until|begin)\b", code) else 0
                opens += len(re.findall(r"=\s*(?:if|unless|case)\b", code))
                depth += opens - len(re.findall(r"\bend\b", code))
                body.append(code)
                if depth <= 0 and j > i:
                    break
                j += 1
            out.append((i + 1, "\n".join(body)))
            i = j
        i += 1
    return out


def check(text: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    lines = text.splitlines()
    code_lines = [strip_comment(raw) for raw in lines]
    code = "\n".join(code_lines)

    # 1. グリッド文字列のマス数(16 の倍数)
    for n, line in enumerate(code_lines, 1):
        for m in STRING.finditer(line):
            s = m.group(1)
            if is_grid(s) and len(cells_of(s)) % 16:
                errors.append(f"{n}行目: グリッド \"{s}\" は {len(cells_of(s))} マス(1小節 = 16マス。16 の倍数にする)")

    # 2. grid_chop: from: の個数と範囲
    clips = {m.group(1): float(m.group(2)) for m in re.finditer(r"(\w+)\s*=\s*grid_clip\s+[^,\n]+,\s*([\d.]+)", code)}
    chop = re.compile(r'grid_chop\s+(\w+)\s*,\s*(?:"([^"]*)"|(\w+))\s*(?:,\s*from:\s*\[([^\]]*)\])?')
    pats = {m.group(1): m.group(2) for m in re.finditer(r'(\w+)\s*=\s*"([^"\n]*)"', code)}
    for m in chop.finditer(code):
        n = code.count("\n", 0, m.start()) + 1
        clip, lit, var, frm = m.groups()
        pattern = lit if lit is not None else pats.get(var or "")
        if pattern is None or frm is None:
            continue
        try:
            froms = [float(x) for x in frm.split(",") if x.strip()]
        except ValueError:
            continue  # 数値以外(式など)は検査しない
        beats = hit_beats(pattern)
        if len(froms) != len(beats):
            errors.append(f"{n}行目: grid_chop の from: は {len(froms)} 個、音は {len(beats)} 個(同じ個数にする)")
            continue
        total = clips.get(clip)
        for k, (f, ln) in enumerate(zip(froms, beats, strict=True), 1):
            if f < 0 or (total is not None and f + ln > total + 1e-9):
                limit = f"元の長さ {total:g} 拍" if total is not None else "0 以上"
                errors.append(f"{n}行目: grid_chop の {k} 番目の音 from: {f:g}(長さ {ln:g} 拍)が {limit} をはみ出す")

    # 3. define の名前
    for n, line in enumerate(code_lines, 1):
        m = re.match(r"\s*define\s+:(\w+)", line)
        if m and not m.group(1).startswith("grid_"):
            warnings.append(f"{n}行目: define :{m.group(1)} は grid_ で始まる固有の名前にする(Sonic Pi の API と衝突させない)")

    # 4. live_loop: grid_play / grid_chop と sleep の二重待ち
    loops = live_loop_bodies(lines)
    for n, body in loops:
        if GRID_PLAY_OR_CHOP.search(body) and re.search(r"\bsleep\b", body):
            warnings.append(f"{n}行目: live_loop に grid_play / grid_chop と sleep が両方あります(パターンの長さぶん自分で待つので、sleep は要りません)")

    # 5. use_bpm
    bpm = len(re.findall(r"^\s*use_bpm\b", code, re.M))
    if loops and bpm == 0:
        warnings.append("use_bpm がありません(テンポは先頭の 1 箇所に書く)")
    elif bpm > 1:
        warnings.append(f"use_bpm が {bpm} 箇所あります(テンポは先頭の 1 箇所に書く)")

    # 6. 演算(必要なときだけ使う規約)
    for n, line in enumerate(code_lines, 1):
        if OPERATOR.search(line):
            warnings.append(f"{n}行目: グリッドの演算(.mask .shift .accent .bar)は、必要なときだけ使う規約です")
        for m in STRING.finditer(line):
            if is_grid(m.group(1)) and re.match(r"\s*[+*]", line[m.end():]):
                warnings.append(f"{n}行目: グリッド文字列の連結・繰り返し(+ *)は、必要なときだけ使う規約です。長いなら4小節ぶん書き並べる")
    return errors, warnings


def main() -> None:
    files = sys.argv[1:]
    if not files:
        sys.exit(__doc__)
    worst = 0
    for f in files:
        errors, warnings = check(Path(f).read_text(encoding="utf-8"))
        for e in errors:
            print(f"{f}: 誤り: {e}")
        for w in warnings:
            print(f"{f}: 警告: {w}")
        if not errors and not warnings:
            print(f"{f}: 問題なし")
        worst = max(worst, 2 if errors else 1 if warnings else 0)
    sys.exit(worst)


if __name__ == "__main__":
    main()
