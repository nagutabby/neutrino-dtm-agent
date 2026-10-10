import shutil
from pathlib import Path

import mido
import pytest

ROOT = Path(__file__).resolve().parent.parent


def make_midi(path: Path, notes, bpm=120, ts=(4, 4), ppq=480, channel=0):
    """notes: [(start_beat, dur_beat, pitch, vel)]"""
    mid = mido.MidiFile(ticks_per_beat=ppq)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    tr.append(mido.MetaMessage("time_signature", numerator=ts[0], denominator=ts[1], time=0))
    ev = []
    for s, d, p, v in notes:
        ev.append((round(s * ppq), 1, p, v))
        ev.append((round((s + d) * ppq), 0, p, 0))
    ev.sort(key=lambda e: (e[0], e[1]))
    t = 0
    for tick, on, p, v in ev:
        tr.append(mido.Message("note_on" if on else "note_off", note=p, velocity=v, time=tick - t, channel=channel))
        t = tick
    mid.save(path)


@pytest.fixture
def song(tmp_path, monkeypatch):
    monkeypatch.setenv("DTM_PROJECTS", str(tmp_path))
    import importlib

    import common

    importlib.reload(common)
    d = tmp_path / "demo"
    (d / "tracks").mkdir(parents=True)
    shutil.copytree(ROOT / "docs/templates/spec", d / "spec")
    return d
