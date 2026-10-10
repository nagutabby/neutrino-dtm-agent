#!/usr/bin/env python3
"""spec の params.accent に従って MIDI のベロシティに抑揚を付ける(生成時に適用。MIDI を直接直さない)。

使い方: apply_accent.py <song> <spec-key> <in.mid> <out.mid>
accent(いずれも加減値。結果は 40〜127 に収める):
  downbeat:   小節頭のノート
  offbeat:    拍の途中(拍頭でない)のノート
  phrase_arc: 4小節フレーズ内の小節ごとの加減 [b1,b2,b3,b4](平均 0 に近づけると全体の音量が動かない)
"""

from __future__ import annotations

import argparse

import midi_tools
import mido
from common import load_specs, require_project


def apply(in_mid: str, out_mid: str, accent: dict) -> int:
    m = midi_tools.load(in_mid)
    ppq, bar = m.ppq, m.ppq * 4 * m.time_sig[0] // m.time_sig[1]
    arc = accent.get("phrase_arc") or [0, 0, 0, 0]
    off: dict[tuple[int, int], int] = {}
    for n in m.notes:
        d = 0
        if n.start % bar == 0:
            d += int(accent.get("downbeat", 0))
        elif n.start % ppq != 0:
            d += int(accent.get("offbeat", 0))
        d += int(arc[(n.start // bar) % len(arc)])
        off[(n.start, n.pitch)] = d
    src = mido.MidiFile(in_mid)
    out = mido.MidiFile(ticks_per_beat=src.ticks_per_beat)
    for tr in src.tracks:
        nt = mido.MidiTrack()
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                msg = msg.copy(velocity=max(40, min(127, msg.velocity + off.get((t, msg.note), 0))))
            nt.append(msg)
        out.tracks.append(nt)
    out.save(out_mid)
    return len(m.notes)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("spec")
    ap.add_argument("in_mid")
    ap.add_argument("out_mid")
    a = ap.parse_args()
    require_project(a.song)
    meta = load_specs(a.song)[a.spec][0]
    accent = (meta.get("params") or {}).get("accent")
    if not accent:
        raise SystemExit(f"{a.spec} に params.accent がありません")
    print(f"{apply(a.in_mid, a.out_mid, accent)} ノートに抑揚を適用: {accent}")


if __name__ == "__main__":
    main()
