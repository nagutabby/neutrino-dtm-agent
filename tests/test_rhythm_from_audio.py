import numpy as np
import record_mic
import rhythm_from_audio as r

SR = r.SR


def hit(amp=1.0):
    """低い胴鳴り + 短い頭の打撃音(キックや机を叩いた音のイメージ)。"""
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(1)
    body = np.sin(2 * np.pi * (45 * t + 65 * 0.03 * (1 - np.exp(-t / 0.03)))) * np.exp(-t / 0.08)
    click = rng.standard_normal(n) * np.exp(-t / 0.004) * 0.15
    return amp * 0.8 * (body + click)


def stem(pattern, bpm=100, start=0.5):
    cell = 60 / bpm / 4
    x = np.zeros(int((start + len(pattern) * cell + 0.5) * SR))
    for i, c in enumerate(pattern):
        if c != ".":
            h = hit(1.0 if c == "x" else 0.4)
            a = int((start + i * cell) * SR)
            x[a : a + len(h)] += h
    return x


def quantize(x, bpm=100, bars=None):
    onsets = r.detect_onsets(x)
    k = bpm / 60 * 4 / SR
    hits = [(round((a - onsets[0]) * k), r.peak_after(x, a)) for a in onsets]
    return r.build_pattern(hits, 4, 4, bars)


def test_roundtrip_one_stem():
    want = "x... ..x. x... ..x."
    got, nb = quantize(stem(want.replace(" ", "")))
    assert nb == 1
    assert [i for i, c in enumerate(got.replace(" ", "")) if c != "."] == [0, 6, 8, 14]


def test_two_bars_and_weak_hits():
    p = "x...o...x...o...x...o...x...o..."  # 2小節
    got, nb = quantize(stem(p))
    assert nb == 2
    cells = got.replace(" ", "").replace("|", "")
    assert [i for i, c in enumerate(cells) if c != "."] == [0, 4, 8, 12, 16, 20, 24, 28]
    assert all(cells[i] == "o" for i in (4, 12, 20, 28))
    assert all(cells[i] in "Xx" for i in (0, 8, 16, 24))


def test_build_pattern_format_and_levels():
    got, nb = r.build_pattern([(0, 1.0), (4, 0.5), (9, 0.2)], 4, 4, 2)
    assert nb == 2
    assert got == "X... x... .o.. .... | .... .... .... ...."


def test_ruby_output():
    code = r.render_ruby("x... .... .... ....", "hat", 100, "a.mp3", 4, 4, 1)
    assert 'audio_hat_rhythm = "x... .... .... ...."' in code
    assert ":drum_cymbal_closed" in code
    assert "grid_play audio_hat_voice, audio_hat_rhythm" in code
    assert "sleep" not in code


def test_count_only_kick_track_is_one_bar():
    assert len(record_mic.kick_track(100, 1, sr=SR)) < SR * 3
