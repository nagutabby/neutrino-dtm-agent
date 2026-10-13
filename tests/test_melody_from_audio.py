import melody_from_audio as m
import numpy as np
import pytest

SR = m.SR


def tone(notes, bpm=120, detune_cents=0.0, gap=0.04):
    """[(MIDI, 拍)] から倍音つきの音を作る(音の間に短い無音)。"""
    sec = 60 / bpm
    parts = []
    for midi, beats in notes:
        f = 440 * 2 ** ((midi - 69 + detune_cents / 100) / 12)
        t = np.arange(int(SR * (beats * sec - gap))) / SR
        w = sum(np.sin(2 * np.pi * f * h * t) / h for h in (1, 2, 3))
        parts += [0.3 * w, np.zeros(int(SR * gap))]
    return np.concatenate([np.zeros(int(SR * 0.3)), *parts, np.zeros(int(SR * 0.3))])


def run(x, key="F minor", bpm=120):
    f0, rms = m.yin_track(x)
    notes, info = m.extract_notes(f0, rms, m.parse_key(key), 0.1)
    return m.to_beats(notes, bpm, 4, 0.0), info


def test_parse_key():
    k = m.parse_key("F minor")
    assert k.tonic_pc == 5 and k.scale == "minor" and k.use_flats
    assert m.parse_key("C# major").tonic_pc == 1
    assert m.parse_key("Bb dorian").use_flats
    assert m.parse_key("A").scale == "major"
    with pytest.raises(ValueError):
        m.parse_key("H minor")
    with pytest.raises(ValueError):
        m.parse_key("F foo")


def test_snap_to_scale():
    pcs = m.parse_key("F minor").pcs  # F G Ab Bb C Db Eb
    assert m.snap_to_scale(68.0, pcs) == 68  # Ab は音階内
    assert m.snap_to_scale(69.0, pcs) == 68  # A は Ab と Bb の真ん中 → 低い方
    assert m.snap_to_scale(64.2, pcs) == 65  # E 寄りの F 側 → F


def test_melody_roundtrip():
    seq = [(65, 1), (65, 1), (68, 1), (72, 1), (70, 1), (68, 1), (67, 1), (65, 1)]
    beats, info = run(tone(seq))
    assert [b[1] for b in beats] == [65, 65, 68, 72, 70, 68, 67, 65]
    assert [round(b[0]) for b in beats] == list(range(8))
    assert all(0.7 <= b[2] <= 1.0 for b in beats)
    assert info["in_key"] > 0.95


def test_out_of_key_note_is_snapped_and_flat_singer_is_corrected():
    seq = [(72, 1), (74, 1), (79, 1)]  # 2音目 D は C マイナーペンタの外(Eb が近い)
    beats, info = run(tone(seq, detune_cents=-35), key="C minor_pentatonic")
    assert [b[1] for b in beats] == [72, 75, 79]
    assert info["tune_cents"] == pytest.approx(-35, abs=8)
    assert info["in_key"] < 0.8


def test_octave_placement_and_names():
    beats = [(0, 53, 1), (1, 56, 1)]
    assert m.place_octave(beats, 60, 84, None) == 12
    assert m.place_octave(beats, 60, 84, -1) == -12
    assert m.note_name(68, True) == "ab4" and m.note_name(68, False) == "gs4"


def test_ruby_output_has_time_warp_and_sleep():
    code = m.render_ruby([(0, 65, 1), (1.5, 68, 0.5)], 0, m.parse_key("F minor"), 100, "rec.mp3", "audio_melody", 4)
    assert "[0, :f4, 1]" in code and "[1.5, :ab4, 0.5]" in code
    assert "time_warp pos" in code and "sleep audio_melody_beats" in code


def test_kick_grid_and_removal():
    import record_mic

    bpm, beat = 100, 0.6
    latency = 0.37  # 録音の頭とキックの頭のずれ
    kick = record_mic.kick_track(bpm, 6, sr=SR)  # 6小節 = 14.4秒
    # 4拍(1小節)数えたあと、拍 0 から「F F Ab C Bb Ab G F」を1拍ずつ。歌い出しは30ms遅れ
    seq = [(53, 1), (53, 1), (56, 1), (60, 1), (58, 1), (56, 1), (55, 1), (53, 1)]
    voice = tone(seq, bpm=bpm)[int(0.3 * SR) :]  # 先頭の無音を除く
    n = int((latency + 4 * beat + 8 * beat + 1) * SR)
    x = np.zeros(n)
    x[int(latency * SR) : int(latency * SR) + len(kick)] += kick[: n - int(latency * SR)]
    v0 = int((latency + 4 * beat + 0.03) * SR)
    x[v0 : v0 + len(voice)] += voice[: n - v0]

    found = m.find_kick_grid(x, bpm)
    assert found is not None and found[1] >= 3
    assert found[0] == pytest.approx(latency, abs=0.02)

    y = m.highpass(x, 130)
    f0, rms = m.yin_track(y, fmin=100.0)
    notes, _ = m.extract_notes(f0, rms, m.parse_key("F minor"), 0.1)
    beats = m.to_beats(notes, bpm, 4, 0.0, t0=found[0] + 4 * beat)
    assert [b[1] for b in beats] == [53, 53, 56, 60, 58, 56, 55, 53]
    assert [round(b[0]) for b in beats] == list(range(8))
    assert all(abs(b[0] - round(b[0])) < 1e-9 for b in beats)  # 拍に揃う
