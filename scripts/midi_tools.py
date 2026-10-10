"""MIDI 解析の共通処理(mido)。"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import mido


@dataclass
class Note:
    start: int
    end: int
    pitch: int
    vel: int
    channel: int


@dataclass
class MidiInfo:
    path: Path
    ppq: int
    bpm: float
    time_sig: tuple[int, int]
    notes: list[Note] = field(default_factory=list)
    track_names: list[str] = field(default_factory=list)
    num_tracks: int = 0

    @property
    def end_tick(self) -> int:
        return max((n.end for n in self.notes), default=0)

    @property
    def ticks_per_bar(self) -> int:
        num, den = self.time_sig
        return self.ppq * 4 * num // den

    @property
    def bars(self) -> int:
        return math.ceil(self.end_tick / self.ticks_per_bar) if self.notes else 0

    def pitch_range(self) -> tuple[int, int] | None:
        if not self.notes:
            return None
        return min(n.pitch for n in self.notes), max(n.pitch for n in self.notes)


def load(path: str | Path) -> MidiInfo:
    path = Path(path)
    mid = mido.MidiFile(path)
    bpm, ts = 120.0, (4, 4)
    got_tempo = got_ts = False
    notes: list[Note] = []
    names = []
    for tr in mid.tracks:
        names.append(tr.name)
        t = 0
        on: dict[tuple[int, int], tuple[int, int]] = {}
        for msg in tr:
            t += msg.time
            if msg.type == "set_tempo" and not got_tempo:
                bpm, got_tempo = mido.tempo2bpm(msg.tempo), True
            elif msg.type == "time_signature" and not got_ts:
                ts, got_ts = (msg.numerator, msg.denominator), True
            elif msg.type == "note_on" and msg.velocity > 0:
                on[(msg.channel, msg.note)] = (t, msg.velocity)
            elif msg.type in ("note_off", "note_on"):
                k = (msg.channel, msg.note)
                if k in on:
                    s, v = on.pop(k)
                    notes.append(Note(s, t, msg.note, v, msg.channel))
    notes.sort(key=lambda n: (n.start, n.pitch))
    return MidiInfo(path, mid.ticks_per_beat, round(bpm, 2), ts, notes, names, len(mid.tracks))


def overlaps(notes: list[Note]) -> list[tuple[Note, Note]]:
    """同時に鳴る音の組(単旋律の検査用)。"""
    out = []
    ordered = sorted(notes, key=lambda n: n.start)
    for a, b in zip(ordered, ordered[1:], strict=False):
        if b.start < a.end:
            out.append((a, b))
    return out
