#!/usr/bin/env python3
"""Sonic Pi のコードの簡易検査(音は出さない)。Sonic Pi の API の検査と、グリッド記法の規約(docs/coding-rules.md)の検査。

  live_check.py <file.rb> [...]

Sonic Pi の API(誤り): サンプル名(`sample :bd_haus`、`grid_voice :sample, :名前`)・コード名(`chord(:c3, :minor7)`、`[:f3, :minor7]`)・スケール名が
  内蔵にあるか(config/sonicpi_catalog.json)、シンセ名(use_synth / synth)・FX 名(with_fx)が内蔵にあるか、同じ行の引数名がそのシンセ/FX の
  引数にあるか、`sleep` の無い live_loop(Sonic Pi がハングする典型。grid_play / grid_chop / grid_each / grid_roll /
  grid_ticks / grid_rest は中で sleep するので可)。
グリッド記法(docs/live-grid.rb):
  誤り: 立ち上がり・立ち下がりの言葉(attack: / release: / env:)が知らない言葉 / グリッド文字列のマス数が 1小節のマス数の
        倍数でない(grid_res × grid_meter。既定 4 × 4 = 16)/ grid_res・grid_meter が正の整数でない /
        grid_chop の `from:` の個数が音の数と違う / `from:` が元の wav(grid_clip の拍数)をはみ出す
  警告: `define` の名前が grid_ で始まらない / live_loop に grid_play・grid_chop と `sleep` が両方ある(二重に待つ) /
        grid_res・grid_meter が複数の値で書かれている(1曲で1つに固定)/ use_bpm が無い・複数ある /
        演算(.mask .shift .accent .bar、グリッド文字列の `+`)の使用(必要なときだけ使う規約)
正規表現による検査なので、見落とし・誤検出がありうる(最終判断は Sonic Pi 本体のエラー表示)。
終了コード: 0 = 問題なし、1 = 警告のみ、2 = 誤り。
"""

from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

import sonicpi

COMMON = {"amp", "pan", "attack", "decay", "sustain", "release", "attack_level", "decay_level", "sustain_level",
          "env_curve", "cutoff", "res", "note", "slide", "note_slide", "amp_slide", "pan_slide", "cutoff_slide"}
USE_SYNTH = re.compile(r"\b(?:use_synth|synth)\s+:(\w+)(.*)")
WITH_FX = re.compile(r"\bwith_fx\s+:(\w+)(.*?)\bdo\b")
OPT = re.compile(r"\b(\w+):\s")
SAMPLE = re.compile(r"\bsample\s+:(\w+)|\bgrid_voice\s+:sample\s*,\s*:(\w+)")
CHORD = re.compile(r"\bchord\(?\s*[^,()]+,\s*(?::(\w+)|['\"]([^'\"]+)['\"])")
CHORD_PAIR = re.compile(r"\[\s*:[a-gA-G][sb#]?-?\d?\s*,\s*(?::(\w+)|['\"]([^'\"]+)['\"])\s*\]")  # [:f3, :minor7]
SCALE = re.compile(r"\bscale\(?\s*[^,()]+,\s*:(\w+)")


GRID_CHARS = "xXo123456789.-| "
HITS = "xXo123456789"
SYMBOLS = "xXo.-"  # 数字だけの文字列をグリッドと間違えないための目印
DEFAULT_RES = 4  # 1拍あたりのマス数(4 = 16分音符)
DEFAULT_METER = 4  # 1小節の拍数(4/4)
ATTACKS = {"instant", "fast", "mid", "slow"}
RELEASES = {"cut", "short", "mid", "long"}
ENVS = {"pluck", "stab", "pad", "swell"}
ENV_WORDS = {"attack": ATTACKS, "release": RELEASES, "env": ENVS}
WORD = re.compile(r"\b(attack|release|env):\s*:(\w+)")
SETTING = re.compile(r"^\s*grid_(res|meter)\s+(\S+)", re.M)
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
    """グリッド文字列らしいか: 使える文字だけで、音符(x X o 1〜9)と記号(x X o . -)を含み、6マス以上。"""
    cells = cells_of(s)
    return (
        bool(s)
        and all(c in GRID_CHARS for c in s)
        and len(cells) >= 6
        and any(c in HITS for c in cells)
        and any(c in SYMBOLS for c in cells)
    )


def cells_of(pattern: str) -> str:
    return "".join(c for c in pattern if c not in " |\t\n")


def hit_beats(pattern: str, res: int = DEFAULT_RES) -> list[float]:
    """各音の長さ(拍)。音 = x X o、直後に続く - ぶんだけ伸びる。1マス = 1/res 拍。"""
    cells = cells_of(pattern)
    out = []
    for i, c in enumerate(cells):
        if c in HITS:
            n = 1
            while i + n < len(cells) and cells[i + n] == "-":
                n += 1
            out.append(n / res)
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
    # サンプル・コード・スケールの名前(カタログに入っているものだけ検査する)
    samples = {n for names in info.get("samples", {}).values() for n in names}
    for i, raw in enumerate(lines, 1):
        line = strip_comment(raw)
        for kind, rx, valid, cmd in (("サンプル", SAMPLE, samples, "samples"), ("コード", CHORD, set(info.get("chords", [])), "chords"),
                                    ("コード", CHORD_PAIR, set(info.get("chords", [])), "chords"), ("スケール", SCALE, set(info.get("scales", [])), "scales")):
            if not valid:
                continue
            for m in rx.finditer(line):
                name = next(g for g in m.groups() if g)
                if name not in valid:
                    near = difflib.get_close_matches(name, valid, n=3)
                    hint = f"もしかして: {' '.join(near)}。" if near else ""
                    problems.append(f"{i}行目: 内蔵に無い{kind} {name}。{hint}(`sonicpi.py {cmd}` で一覧)")
    # live_loop ... do ... end に sleep / sync があるか(grid_* も中で sleep する)
    for n, body in live_loop_bodies(lines):
        if not re.search(r"\b(sleep|sync|wait|grid_play|grid_chop|grid_each|grid_roll|grid_ticks|grid_rest)\b", body):
            problems.append(f"{n}行目: live_loop に sleep(または sync)がありません。実行するとハングします")
    return problems


def check_grid(text: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    lines = text.splitlines()
    code_lines = [strip_comment(raw) for raw in lines]
    code = "\n".join(code_lines)

    # 0. 解像度と拍子(grid_res / grid_meter)
    settings: dict[str, list[int]] = {"res": [], "meter": []}
    for m in SETTING.finditer(code):
        n = code.count("\n", 0, m.start()) + 1
        if m.group(2).isdigit() and int(m.group(2)) > 0:
            settings[m.group(1)].append(int(m.group(2)))
        else:
            errors.append(f"{n}行目: grid_{m.group(1)} は正の整数で書く(例: grid_{m.group(1)} {DEFAULT_RES if m.group(1) == 'res' else DEFAULT_METER})")
    for key, vals in settings.items():
        if len(set(vals)) > 1:
            warnings.append(f"grid_{key} が複数の値({', '.join(map(str, vals))})で書かれています(1曲で1つに固定する。違う拍子は別の曲・別のファイルに分ける)")
    res = settings["res"][-1] if settings["res"] else DEFAULT_RES
    bar = res * (settings["meter"][-1] if settings["meter"] else DEFAULT_METER)

    # 1. グリッド文字列のマス数(1小節のマス数の倍数)
    for n, line in enumerate(code_lines, 1):
        for m in STRING.finditer(line):
            s = m.group(1)
            if is_grid(s) and len(cells_of(s)) % bar:
                errors.append(f"{n}行目: グリッド \"{s}\" は {len(cells_of(s))} マス(1小節 = {bar}マス。{bar} の倍数にする)")

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
        beats = hit_beats(pattern, res)
        if len(froms) != len(beats):
            errors.append(f"{n}行目: grid_chop の from: は {len(froms)} 個、音は {len(beats)} 個(同じ個数にする)")
            continue
        total = clips.get(clip)
        for k, (f, ln) in enumerate(zip(froms, beats, strict=True), 1):
            if f < 0 or (total is not None and f + ln > total + 1e-9):
                limit = f"元の長さ {total:g} 拍" if total is not None else "0 以上"
                errors.append(f"{n}行目: grid_chop の {k} 番目の音 from: {f:g}(長さ {ln:g} 拍)が {limit} をはみ出す")

    # 2b. 立ち上がり・立ち下がりの言葉(attack: / release: / env:)
    for n, line in enumerate(code_lines, 1):
        if "grid_voice" not in line and "grid_chop" not in line:
            continue
        for m in WORD.finditer(line):
            if m.group(2) not in ENV_WORDS[m.group(1)]:
                known = " ".join(sorted(ENV_WORDS[m.group(1)]))
                errors.append(f"{n}行目: {m.group(1)}: :{m.group(2)} は知らない言葉です({known})")

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
    info = sonicpi.info()
    worst = 0
    for f in files:
        text = Path(f).read_text(encoding="utf-8")
        errors = check(text, info)
        grid_errors, warnings = check_grid(text)
        errors += grid_errors
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
