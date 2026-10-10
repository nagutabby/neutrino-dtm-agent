#!/usr/bin/env python3
"""NEUTRINO に渡す MusicXML を検査する(パート数・テンポ・歌詞・和音・1音1音節)。

終了コード: 0=エラーなし / 1=エラーあり
"""

from __future__ import annotations

import argparse
import sys

from lxml import etree


def validate(path: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    root = etree.parse(path).getroot()
    parts = root.findall("part")
    if len(parts) != 1:
        errors.append(f"パートが {len(parts)} 個あります。歌声用の MusicXML は1パートにしてください。")
    if root.find(".//sound[@tempo]") is None and root.find(".//metronome") is None:
        warns.append("テンポ指定(<sound tempo> か <metronome>)がありません。意図しないテンポになる可能性があります。")
    notes = [n for n in root.iter("note") if n.find("rest") is None]
    if not notes:
        errors.append("音符がありません。")
    chord = [n for n in notes if n.find("chord") is not None]
    if chord:
        errors.append(f"和音(<chord/>)の音符が {len(chord)} 個あります。歌声は単旋律にしてください。")
    no_lyric = []
    for n in notes:
        if n.find("grace") is not None:
            continue
        tie_stop = any(t.get("type") == "stop" for t in n.findall("tie"))
        if tie_stop:
            continue
        ly = n.findall("lyric")
        if not ly:
            no_lyric.append(n)
        elif len(ly) > 1:
            warns.append("1音符に複数の歌詞があります(1音符1音節が基本です)。")
    if no_lyric:
        errors.append(f"歌詞のない音符が {len(no_lyric)} 個あります(lyrics_inject.py で付与できます)。")
    return errors, warns


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("musicxml")
    a = ap.parse_args()
    errors, warns = validate(a.musicxml)
    for e in errors:
        print(f"[エラー] {e}")
    for w in warns:
        print(f"[警告] {w}")
    if not errors and not warns:
        print("問題は見つかりませんでした。")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
