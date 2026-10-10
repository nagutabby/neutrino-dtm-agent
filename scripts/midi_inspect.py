#!/usr/bin/env python3
"""MIDI の基本情報(テンポ・拍子・小節数・音域・最短音長など)を表示する。"""

from __future__ import annotations

import argparse

import midi_tools
from common import midi_to_note


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("midi")
    a = ap.parse_args()
    m = midi_tools.load(a.midi)
    print(f"ファイル: {m.path}")
    print(f"テンポ: {m.bpm} BPM / 拍子: {m.time_sig[0]}/{m.time_sig[1]} / 分解能: {m.ppq} ticks/拍")
    print(f"トラック数: {m.num_tracks} / ノート数: {len(m.notes)} / 小節数: {m.bars}")
    rng = m.pitch_range()
    if rng:
        print(f"音域: {midi_to_note(rng[0])}({rng[0]}) 〜 {midi_to_note(rng[1])}({rng[1]})")
        shortest = min(n.end - n.start for n in m.notes)
        print(f"最短音長: {shortest} ticks({shortest / m.ppq:.3f} 拍)")
        print(f"重なり(同時発音)組数: {len(midi_tools.overlaps(m.notes))}")


if __name__ == "__main__":
    main()
