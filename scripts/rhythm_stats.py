#!/usr/bin/env python3
"""MIDI のリズム型を数値で出す(読み取り専用)。使い方: rhythm_stats.py <song> [track ...]

出力: 音数 / 拍頭に乗る割合 / 裏拍(8分裏・16分)の割合 / 最頻の音価とその割合 / ベロシティの種類数と幅。
目安は docs/mix-review-viewpoints.md の #13。判定はしない(聴感はユーザー)。
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

import mido

ROOT = Path(__file__).resolve().parent.parent


def latest(tracks: Path) -> dict[str, Path]:
    found: dict[str, tuple[int, Path]] = {}
    for f in tracks.glob("*_v*.mid"):
        m = re.fullmatch(r"\d{2}_([a-z0-9-]+)_v(\d+)\.mid", f.name)
        if m and (m[1] not in found or int(m[2]) > found[m[1]][0]):
            found[m[1]] = (int(m[2]), f)
    return {k: v[1] for k, v in sorted(found.items())}


def stats(path: Path) -> str:
    m = mido.MidiFile(str(path))
    tpb = m.ticks_per_beat
    ons = []
    for tr in m.tracks:
        t = 0
        for e in tr:
            t += e.time
            if e.type == "note_on" and e.velocity > 0:
                ons.append((t, e.velocity))
    ons.sort()
    if not ons:
        return "音なし"
    n = len(ons)
    on_beat = sum(1 for t, _ in ons if t % tpb == 0) / n
    off8 = sum(1 for t, _ in ons if t % tpb == tpb // 2) / n
    sub16 = sum(1 for t, _ in ons if t % (tpb // 2) != 0) / n
    ioi = collections.Counter(b[0] - a[0] for a, b in zip(ons, ons[1:], strict=False) if b[0] > a[0])
    top, cnt = ioi.most_common(1)[0] if ioi else (0, 0)
    vel = [v for _, v in ons]
    return (f"音数{n} 拍頭{on_beat:.0%} 8分裏{off8:.0%} 16分/3連の位置{sub16:.0%} "
            f"最頻の間隔{top / tpb:.2f}拍({cnt / max(1, sum(ioi.values())):.0%}) "
            f"ベロシティ{len(set(vel))}種 {min(vel)}-{max(vel)}")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    d = ROOT / "projects" / sys.argv[1] / "tracks"
    want = set(sys.argv[2:])
    for name, f in latest(d).items():
        if not want or name in want:
            print(f"{f.name}: {stats(f)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
