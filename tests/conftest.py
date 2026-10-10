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


PATCHES = """patches:
  lowsaw:
    {name: 低音, kind: melodic, synth: tb303, mono: true, params: {amp: 0.5, pan: 0, cutoff: 80, release: 0.12}}
  keys:
    name: 鍵盤
    kind: melodic
    synth: fm
    params: {amp: 0.4, pan: 0, depth: 1.6, release: 0.3}
    fx: [{name: reverb, params: {room: 0.6, mix: 0.3}}]
  kit:
    name: キット
    kind: drums
    pieces:
      kick: {notes: [36], synth: sc808_bassdrum, params: {amp: 0.8, pan: 0, decay: 0.5}, sweep: {note: 30, time: 0.1}}
      tick: {notes: [56], synth: sc808_closed_hihat, params: {amp: 0.4, pan: 0, decay: 0.2}}
"""


def write_patches(d, patches_yaml=PATCHES):
    (d / "synth" / "patches.yaml").write_text(patches_yaml, encoding="utf-8")


@pytest.fixture
def song_with_patches(song):
    write_patches(song)
    return song
