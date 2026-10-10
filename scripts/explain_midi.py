#!/usr/bin/env python3
"""MIDI を平易な日本語で要約する(技術解説の数値根拠)。トラック単位。

--with-drums DRUMS.mid を付けると、このトラックのアタックがキック(GM 36)と
同時に鳴る割合(リズムの一体感)を出す。
"""

from __future__ import annotations

import argparse
from collections import Counter

import midi_tools
from common import midi_to_note

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
TRIADS = {(0, 4, 7): "", (0, 3, 7): "m", (0, 3, 6): "dim", (0, 4, 8): "aug", (0, 5, 7): "sus4", (0, 2, 7): "sus2"}


def estimate_key(m: midi_tools.MidiInfo) -> str:
    hist = [0.0] * 12
    for n in m.notes:
        hist[n.pitch % 12] += n.end - n.start
    best, score = ("", -2.0)
    for tonic in range(12):
        for prof, mode in ((MAJOR, "長調"), (MINOR, "短調")):
            rot = [prof[(i - tonic) % 12] for i in range(12)]
            ma, mb = sum(hist) / 12, sum(rot) / 12
            num = sum((h - ma) * (r - mb) for h, r in zip(hist, rot, strict=True))
            den = (sum((h - ma) ** 2 for h in hist) * sum((r - mb) ** 2 for r in rot)) ** 0.5
            c = num / den if den else -1
            if c > score:
                best, score = f"{NAMES[tonic]} {mode}", c
    return best


def chord_name(pitches: list[int]) -> str:
    pcs = sorted({p % 12 for p in pitches})
    for root in pcs:
        shape = tuple(sorted((p - root) % 12 for p in pcs))
        if shape in TRIADS:
            return f"{NAMES[root]}{TRIADS[shape]}"
    return "/".join(NAMES[p] for p in pcs)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("midi")
    ap.add_argument("--with-drums")
    a = ap.parse_args()
    m = midi_tools.load(a.midi)
    if not m.notes:
        print("音符がありません。")
        return
    lo, hi = m.pitch_range()  # type: ignore[misc]
    vels = [n.vel for n in m.notes]
    print(f"■ {m.path.name}")
    print(f"・{m.bpm} BPM、{m.time_sig[0]}/{m.time_sig[1]} 拍子、{m.bars} 小節、ノート {len(m.notes)} 個")
    print(f"・推定キー: {estimate_key(m)}(使われた音の長さの割合から推定)")
    print(f"・音域: {midi_to_note(lo)}〜{midi_to_note(hi)}(幅 {hi - lo} 半音)。低いほど土台、高いほど目立つ")
    print(f"・強さ(ベロシティ): {min(vels)}〜{max(vels)}、平均 {sum(vels) / len(vels):.0f}。大きいほど強く聞こえる")

    beat = m.ppq
    pos = Counter()
    for n in m.notes:
        b = (n.start % m.ticks_per_bar) / beat
        pos[int(b) + 1 if b == int(b) else None] += 1
    on_beat = sum(v for k, v in pos.items() if k is not None)
    print(f"・拍の頭(表拍)で始まる音: {on_beat / len(m.notes):.0%}(残りは裏拍・細かいリズム)")
    per_beat = {k: v for k, v in sorted(pos.items(), key=lambda x: (x[0] is None, x[0] or 0))}
    print("  拍ごとの数: " + "、".join(f"{k}拍目={v}" for k, v in per_beat.items() if k is not None))

    by_start: dict[int, list[int]] = {}
    for n in m.notes:
        by_start.setdefault(n.start, []).append(n.pitch)
    if any(len(v) >= 3 for v in by_start.values()):
        prog = []
        for s in sorted(by_start):
            if len(by_start[s]) >= 3:
                c = chord_name(by_start[s])
                if not prog or prog[-1] != c:
                    prog.append(c)
        print("・和音の流れ: " + " → ".join(prog[:16]))

    if a.with_drums:
        d = midi_tools.load(a.with_drums)
        kicks = {n.start for n in d.notes if n.pitch == 36}
        if kicks:
            hit = sum(1 for s in by_start if s in kicks)
            print(f"・キックと同時に始まる音: {hit / len(by_start):.0%}(高いほど低音とキックが一体で「タイト」)")


if __name__ == "__main__":
    main()
