#!/usr/bin/env python3
"""歌声(メロディ)用 MIDI を NEUTRINO 向けに検証する。違反を列挙するだけで自動修正はしない。

終了コード: 0=問題なし(警告のみ含む) / 1=エラーあり
"""

from __future__ import annotations

import argparse
import sys

import midi_tools
from common import midi_to_note, note_to_midi

DEFAULT_RANGE = ("C3", "C5")  # 歌声として無理のない目安(モデル・声質で調整)
MIN_NOTE_BEATS = 0.125  # 32分音符より短い音は歌いにくい


def validate(path: str, vocal_range: tuple[str, str] = DEFAULT_RANGE) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    m = midi_tools.load(path)
    if not m.notes:
        return ["音符がありません。歌メロ用 MIDI にはノートが必要です。"], warns

    ov = midi_tools.overlaps(m.notes)
    if ov:
        a, b = ov[0]
        bar = a.start // m.ticks_per_bar + 1
        errors.append(
            f"同時に鳴る音が {len(ov)} 組あります(例: {bar}小節目 {midi_to_note(a.pitch)} と "
            f"{midi_to_note(b.pitch)})。歌声は1音ずつしか出せないため、和音や重なりを単旋律にしてください"
            "(コード楽器は別トラックへ)。"
        )
    lo, hi = note_to_midi(vocal_range[0]), note_to_midi(vocal_range[1])
    out = [n for n in m.notes if not lo <= n.pitch <= hi]
    if out:
        warns.append(
            f"音域 {vocal_range[0]}〜{vocal_range[1]} の外の音が {len(out)} 個あります"
            f"(例: {midi_to_note(out[0].pitch)})。高すぎ/低すぎは不自然になりやすいので、"
            "Transpose や移調も検討してください。"
        )
    span = max(n.pitch for n in m.notes) - min(n.pitch for n in m.notes)
    if span > 19:
        warns.append(f"音域の幅が {span} 半音あります。1オクターブ+αに収めると歌いやすくなります。")
    short = [n for n in m.notes if (n.end - n.start) / m.ppq < MIN_NOTE_BEATS]
    if short:
        warns.append(f"極端に短い音が {len(short)} 個あります(最短 {min(n.end - n.start for n in short)} ticks)。")
    # 休符(息継ぎ)の有無: 4小節以上、休符が一度も無ければ警告
    gaps = [b.start - a.end for a, b in zip(m.notes, m.notes[1:], strict=False) if b.start - a.end > 0]
    if m.bars >= 4 and not any(g >= m.ppq / 2 for g in gaps):
        warns.append("半拍以上の休符(息継ぎ)がありません。フレーズの切れ目に休符を入れてください。")
    if len({n.channel for n in m.notes}) > 1:
        warns.append("複数チャンネルのノートが含まれています。歌メロは1トラック・1チャンネルにしてください。")
    return errors, warns


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("midi")
    ap.add_argument("--range", nargs=2, metavar=("LOW", "HIGH"), default=list(DEFAULT_RANGE))
    a = ap.parse_args()
    errors, warns = validate(a.midi, tuple(a.range))
    for e in errors:
        print(f"[エラー] {e}")
    for w in warns:
        print(f"[警告] {w}")
    if not errors and not warns:
        print("問題は見つかりませんでした。")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
