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
    shutil.copytree(ROOT / "docs/templates/synth", d / "synth")  # 曲専用の音色(空の雛形)
    (d / "samples").mkdir()
    shutil.copy(ROOT / "docs/templates/user_inputs.yaml", d / "user_inputs.yaml")
    return d


SYNTHDEFS = """[
SynthDef(\\lowsaw, { |out=0, freq=60, amp=0.5, pan=0, gate=1, cutoff=900, rel=0.12| }),
SynthDef(\\keys, { |out=0, freq=261.6, amp=0.4, pan=0, gate=1, index=1.6, rel=0.3| }),
SynthDef(\\thump, { |out=0, amp=0.8, pan=0, tune=50, decay=0.5| }),
SynthDef(\\tick, { |out=0, amp=0.4, pan=0, tune=540, decay=0.2| }),
SynthDef(\\player, { |out=0, buf=0, rate=1, amp=0.5, pan=0, gate=1| }),
]
"""

PATCHES = """patches:
  lowsaw:
    {name: 低音, kind: melodic, synthdef: lowsaw, mono: true, params: {amp: 0.5, pan: 0, cutoff: 900, rel: 0.12}}
  keys:
    {name: 鍵盤, kind: melodic, synthdef: keys, params: {amp: 0.4, pan: 0, index: 1.6, rel: 0.3}}
  kit:
    name: キット
    kind: drums
    pieces:
      kick: {notes: [36], synthdef: thump, params: {amp: 0.8, pan: 0, tune: 50, decay: 0.5}}
      tick: {notes: [56], synthdef: tick, params: {amp: 0.4, pan: 0, tune: 540, decay: 0.2}}
"""


def write_patches(d, patches_yaml=PATCHES, synthdefs=SYNTHDEFS):
    (d / "synth" / "patches.yaml").write_text(patches_yaml, encoding="utf-8")
    (d / "synth" / "synthdefs.scd").write_text(synthdefs, encoding="utf-8")


@pytest.fixture
def song_with_patches(song):
    write_patches(song)
    return song
