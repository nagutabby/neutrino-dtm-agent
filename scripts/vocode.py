#!/usr/bin/env python3
"""NEUTRINO の歌声 wav を、鋸波キャリアのチャンネル・ボコーダーにかける(DSP のみ。AI・機械学習は使わない)。

  vocode.py <voice.wav> <voice.f0> --bpm 130 [--beats 16] [--lead-beats 4] [--out X.wav]

- NEUTRINO は譜面の前後に 1 小節の無音を足すので、--lead-beats だけ頭を捨て、--beats 拍ぶんだけ切り出す
  (Sonic Pi で live_loop に `sample` し、同じ拍数 sleep すれば小節線に揃う)。
- f0 は float32 / 10ms 刻み。無声区間(f0=0)はノイズで子音を保つ。
- 出力は 48kHz / 16bit / モノ。既定の出力名は <voice>_voc.wav(既存は上書きせず版を進める)。
"""

import argparse
import re
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
N_FFT, HOP = 2048, 512
F0_HOP_S = 0.010  # NEUTRINO の f0 フレーム間隔


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        if w.getsampwidth() != 2 or w.getframerate() != SR:
            sys.exit(f"16bit/{SR}Hz の wav のみ対応: {path}")
        ch = w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768
    return x.reshape(-1, ch).mean(axis=1)


def write_wav(path: Path, x: np.ndarray) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def f0_per_sample(f0: np.ndarray, n: int) -> np.ndarray:
    """10ms 刻みの f0 をサンプル単位に補間(無声フレームは 0 のまま階段にする)。"""
    t = np.arange(n) / SR / F0_HOP_S
    idx = np.clip(np.floor(t).astype(int), 0, len(f0) - 1)
    nxt = np.clip(idx + 1, 0, len(f0) - 1)
    a, b = f0[idx], f0[nxt]
    frac = t - np.floor(t)
    both = (a > 0) & (b > 0)
    return np.where(both, a + (b - a) * frac, a)


def saw_blep(freq: np.ndarray) -> np.ndarray:
    """PolyBLEP 付きの鋸波(折り返しノイズを抑える)。"""
    dt = np.maximum(freq, 1.0) / SR
    p = np.cumsum(dt) % 1.0
    s = 2 * p - 1
    lo = p < dt
    t = p[lo] / dt[lo]
    s[lo] -= 2 * t - t * t - 1
    hi = p > 1 - dt
    t = (p[hi] - 1) / dt[hi]
    s[hi] -= t * t + 2 * t + 1
    return s


def make_carrier(f0s: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    voiced = (f0s > 0).astype(np.float64)
    k = int(0.005 * SR)
    voiced = np.convolve(voiced, np.ones(k) / k, mode="same")  # 有声/無声の継ぎ目を滑らかに
    f = np.where(f0s > 0, f0s, 0.0)
    # 声帯らしい厚み: 基音 + わずかにデチューン + 1 オクターブ下
    tone = saw_blep(f) + 0.7 * saw_blep(f * 1.006) + 0.5 * saw_blep(f * 0.5)
    noise = rng.standard_normal(len(f0s)) * 0.6
    return tone * voiced / 2.2 + noise * (1 - voiced)


def stft(x: np.ndarray) -> np.ndarray:
    pad = np.pad(x, (N_FFT, N_FFT))
    n_fr = 1 + (len(pad) - N_FFT) // HOP
    idx = np.arange(N_FFT)[None, :] + HOP * np.arange(n_fr)[:, None]
    return np.fft.rfft(pad[idx] * np.hanning(N_FFT), axis=1)


def istft(S: np.ndarray, n: int) -> np.ndarray:
    out = np.zeros(N_FFT + HOP * (S.shape[0] - 1))
    norm = np.zeros_like(out)
    win = np.hanning(N_FFT)
    for i, fr in enumerate(np.fft.irfft(S, axis=1)):
        out[i * HOP:i * HOP + N_FFT] += fr * win
        norm[i * HOP:i * HOP + N_FFT] += win**2
    out /= np.maximum(norm, 1e-9)
    return out[N_FFT:N_FFT + n]


def band_matrix(n_bands: int, f_lo: float, f_hi: float) -> np.ndarray:
    """対数間隔の三角フィルタバンク(bands × bins)。各 bin の重みの合計が 1 になるよう正規化。"""
    freqs = np.fft.rfftfreq(N_FFT, 1 / SR)
    edges = np.geomspace(f_lo, f_hi, n_bands + 2)
    W = np.zeros((n_bands, len(freqs)))
    for b in range(n_bands):
        lo, c, hi = edges[b], edges[b + 1], edges[b + 2]
        W[b] = np.clip(np.minimum((freqs - lo) / (c - lo), (hi - freqs) / (hi - c)), 0, None)
    return W / np.maximum(W.sum(axis=0), 1e-9)


def vocode(mod: np.ndarray, f0: np.ndarray, n_bands: int = 28) -> np.ndarray:
    rng = np.random.default_rng(0)  # ノイズ成分を毎回同じにする(版間の比較用)
    car = make_carrier(f0_per_sample(f0, len(mod)), rng)
    M, C = stft(mod), stft(car)
    W = band_matrix(n_bands, 100, 12000)
    m_env = np.sqrt((np.abs(M) ** 2) @ W.T)
    c_env = np.sqrt((np.abs(C) ** 2) @ W.T)
    gain = m_env / (c_env + 1e-6)
    # 時間方向に軽く平滑(包絡のカクつきを抑える)
    gain = np.apply_along_axis(lambda g: np.convolve(g, [0.25, 0.5, 0.25], mode="same"), 0, gain)
    return istft(C * (gain @ W), len(mod))


def next_out(voice: Path) -> Path:
    stem = re.sub(r"_v\d+$", "", voice.stem)
    ver = re.search(r"_v(\d+)$", voice.stem)
    n = int(ver.group(1)) if ver else 1
    return voice.with_name(f"{stem}_voc_v{n}.wav")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("voice", type=Path)
    ap.add_argument("f0", type=Path)
    ap.add_argument("--bpm", type=float, required=True)
    ap.add_argument("--beats", type=float, default=16.0, help="切り出す拍数(既定 16 = 4 小節)")
    ap.add_argument("--lead-beats", type=float, default=4.0, help="頭の無音の拍数(NEUTRINO は 1 小節)")
    ap.add_argument("--peak", type=float, default=0.8, help="出力のピーク(0〜1、既定 0.8)")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    f0 = np.fromfile(args.f0, dtype="<f4").astype(np.float64)
    mod = read_wav(args.voice)
    beat = 60 / args.bpm * SR
    start, length = round(args.lead_beats * beat), round(args.beats * beat)
    y = vocode(mod, f0)[start:start + length]
    y = np.pad(y, (0, length - len(y)))
    fade = int(0.02 * SR)
    y[-fade:] *= np.linspace(1, 0, fade)  # ループ継ぎ目のクリック防止
    y *= args.peak / max(np.abs(y).max(), 1e-9)

    out = args.out or next_out(args.voice)
    if out.exists():
        sys.exit(f"既存のファイルは上書きしません: {out}")
    write_wav(out, y)
    print(f"出力: {out}({len(y) / SR:.3f} 秒 = {args.beats} 拍 @ {args.bpm} BPM)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
