#!/usr/bin/env python3
"""MusicXML の音符に歌詞(1音1音節)を割り当てて <lyric> を追加する。

歌詞ファイル: 1行1フレーズ、音節はスペース区切りのひらがな/カタカナ(例: 「き ら き ら ひ か る」)。
拗音は1音節として書く(例: 「きゃ」)。休符・タイで繋がる後続音は割り当てない。
音符数と音節数が一致しなければエラー(自動で詰めたり切ったりしない)。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lxml import etree


def syllables(path: Path) -> list[str]:
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.extend(line.split())
    return out


def singable_notes(root: etree._Element) -> list[etree._Element]:
    notes = []
    for n in root.iter("note"):
        if n.find("rest") is not None or n.find("grace") is not None:
            continue
        tie_stop = any(t.get("type") == "stop" for t in n.findall("tie"))
        if tie_stop and not any(t.get("type") == "start" for t in n.findall("tie")):
            continue
        notes.append(n)
    return notes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("musicxml")
    ap.add_argument("lyrics")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()

    tree = etree.parse(a.musicxml)
    root = tree.getroot()
    syls = syllables(Path(a.lyrics))
    notes = singable_notes(root)
    if len(syls) != len(notes):
        sys.exit(
            f"[エラー] 歌える音符が {len(notes)} 個、音節が {len(syls)} 個で一致しません。"
            "1音符1音節になるよう、歌詞かメロディのどちらを直すか決めてください(spec 07-lyrics / 06-melody)。"
        )
    for n, s in zip(notes, syls, strict=True):
        for old in n.findall("lyric"):
            n.remove(old)
        ly = etree.SubElement(n, "lyric", number="1")
        etree.SubElement(ly, "syllabic").text = "single"
        etree.SubElement(ly, "text").text = s
    tree.write(a.output, encoding="UTF-8", xml_declaration=True)
    print(f"歌詞 {len(syls)} 音節を割り当てました → {a.output}")


if __name__ == "__main__":
    main()
