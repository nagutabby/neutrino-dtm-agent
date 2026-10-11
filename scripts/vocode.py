#!/usr/bin/env python3
"""NEUTRINO の歌声 wav を、鋸波キャリアのチャンネル・ボコーダーにかける(DSP のみ。AI・機械学習は使わない)。

  vocode.py <voice.wav> <voice.f0> --bpm 130 [--beats 16] [--lead-beats 4] [--growl 0.7] [--attack-beats 1] [--phrase-levels 0.7,0.85,1] [--vibrato 35] [--dynamics] [--out X.wav]

- NEUTRINO は譜面の前後に 1 小節の無音を足すので、--lead-beats だけ頭を捨て、--beats 拍ぶんだけ切り出す
  (Sonic Pi で live_loop に `sample` し、同じ拍数 sleep すれば小節線に揃う)。
- f0 は float32 / 10ms 刻み。無声区間(f0=0)はノイズで子音を保つ。
- --growl(0〜1): キャリアに 2 オクターブ下と ~55Hz の振幅変調(ざらつき)を足し、最後に歪ませて「唸り」を出す。
- --attack-beats: 各音符(f0 の音高・有声/無声の切れ目で検出)の頭を、その拍数かけて立ち上げる(音符の半分まで)。
- --vibrato(セント): キャリアの音高に 5.5Hz のビブラートをかける。音符の頭は遅らせて(0.25 秒後から 0.5 秒かけて)深くし、深さは曲の山(--dynamics と同じ弧)に合わせて強まる。
- --dynamics: 全体の弧(小さく始まり 75% 付近で最大、終わりは少し落とす)と、音符ごとのふくらみ(音符の中ほどが大きい)で声の強弱を付ける。休符(息継ぎ)は作らない。
- --phrase-levels: 休符(--phrase-gap 秒以上の無声区間 = 息継ぎ)で f0 をフレーズに分け、フレーズごとの音量(山のピーク比)を順に指定する。
  各フレーズは「頭は小さく → 65% 付近で山 → 終わりは息継ぎに向けて落とす」の抑揚になる。
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


def make_carrier(f0s: np.ndarray, rng: np.random.Generator, growl: float = 0.0, growl_hz: float = 55.0) -> np.ndarray:
    voiced = (f0s > 0).astype(np.float64)
    k = int(0.005 * SR)
    voiced = np.convolve(voiced, np.ones(k) / k, mode="same")  # 有声/無声の継ぎ目を滑らかに
    f = np.where(f0s > 0, f0s, 0.0)
    # 声帯らしい厚み: 基音 + わずかにデチューン + 1 オクターブ下
    tone = saw_blep(f) + 0.7 * saw_blep(f * 1.006) + 0.5 * saw_blep(f * 0.5)
    if growl > 0:
        t = np.arange(len(f0s)) / SR
        tone = tone + growl * 0.9 * saw_blep(f * 0.25)  # 2 オクターブ下の唸り
        tone *= 1 - growl * 0.6 * (0.5 + 0.5 * np.sin(2 * np.pi * growl_hz * t))  # 振幅変調のざらつき
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


def vocode(mod: np.ndarray, f0: np.ndarray, n_bands: int = 28, growl: float = 0.0) -> np.ndarray:
    rng = np.random.default_rng(0)  # ノイズ成分を毎回同じにする(版間の比較用)
    car = make_carrier(f0_per_sample(f0, len(mod)), rng, growl)
    M, C = stft(mod), stft(car)
    W = band_matrix(n_bands, 100, 12000)
    m_env = np.sqrt((np.abs(M) ** 2) @ W.T)
    c_env = np.sqrt((np.abs(C) ** 2) @ W.T)
    gain = m_env / (c_env + 1e-6)
    # 時間方向に軽く平滑(包絡のカクつきを抑える)
    gain = np.apply_along_axis(lambda g: np.convolve(g, [0.25, 0.5, 0.25], mode="same"), 0, gain)
    y = istft(C * (gain @ W), len(mod))
    if growl > 0:  # 歪ませて倍音を足す(ピークは後で揃える)
        drive = 1 + 3 * growl
        y = np.tanh(drive * y / max(np.abs(y).max(), 1e-9)) / np.tanh(drive)
    return y


def note_starts(f0: np.ndarray) -> list[int]:
    """f0(10ms 刻み)から音符の頭のフレーム番号を返す。無声→有声、または半音以上の音高変化。"""
    voiced = f0 > 0
    midi = np.where(voiced, np.round(69 + 12 * np.log2(np.maximum(f0, 1.0) / 440.0)), -1)
    k = 7  # 音符の頭のグライドで誤検出しないよう中央値で均す
    pad = np.pad(midi, (k // 2, k // 2), mode="edge")
    midi = np.array([np.median(pad[i:i + k]) for i in range(len(midi))])
    cand = [i for i in range(len(midi)) if midi[i] >= 0 and (i == 0 or midi[i] != midi[i - 1])]
    out: list[int] = []
    for i in cand:  # 近すぎる検出(グライド中の揺れ)は最初の1つにまとめる
        if not out or i - out[-1] > 15:
            out.append(i)
    return out


def global_arc(f0: np.ndarray) -> np.ndarray:
    """有声区間の最初〜最後を 0〜1 とした曲の弧: 0.6 から 75% 付近で 1.0、終わりは 0.7。フレーム単位。"""
    idx = np.flatnonzero(f0 > 0)
    arc = np.full(len(f0), 0.6)
    if len(idx) == 0:
        return arc
    pos = np.clip((np.arange(len(f0)) - idx[0]) / max(idx[-1] - idx[0], 1), 0, 1)
    return np.where(pos < 0.75, 0.6 + 0.4 * np.sin(pos / 0.75 * np.pi / 2), 1.0 - 0.3 * ((pos - 0.75) / 0.25) ** 2)


def apply_vibrato(f0: np.ndarray, cents: float, rate_hz: float = 5.5, delay_s: float = 0.25, ramp_s: float = 0.5) -> np.ndarray:
    """有声フレームの f0 にビブラートをかける。各音符の頭からの時間で深さを 0→cents に育て、曲の弧で強弱を付ける。"""
    out = f0.copy()
    starts = note_starts(f0)
    arc = global_arc(f0)
    cur = -1
    for i in range(len(f0)):
        while cur + 1 < len(starts) and starts[cur + 1] <= i:
            cur += 1
        if f0[i] <= 0 or cur < 0:
            continue
        t = (i - starts[cur]) * F0_HOP_S
        depth = cents * arc[i] * float(np.clip((t - delay_s) / ramp_s, 0, 1))
        out[i] = f0[i] * 2 ** (depth / 1200 * np.sin(2 * np.pi * rate_hz * i * F0_HOP_S))
    return out


def dynamics_envelope(f0: np.ndarray, n: int) -> np.ndarray:
    """声の強弱: 曲の弧 × 音符ごとのふくらみ(0.8〜1.0)。サンプル単位。"""
    per_frame = global_arc(f0)
    starts = note_starts(f0)
    ends = starts[1:] + [len(f0)]
    swell = np.ones(len(f0))
    for a, b in zip(starts, ends, strict=True):
        q = np.linspace(0, 1, max(b - a, 1))
        swell[a:b] = 0.8 + 0.2 * np.sin(np.pi * q)[: b - a]
    t = np.arange(n) / SR / F0_HOP_S
    return np.interp(t, np.arange(len(f0)), per_frame * swell)


def phrase_ranges(f0: np.ndarray, gap_s: float) -> list[tuple[int, int]]:
    """有声フレームを、gap_s 秒以上の無声区間(息継ぎ)で区切ったフレーズ範囲 [(開始, 終了)] にする。"""
    idx = np.flatnonzero(f0 > 0)
    if len(idx) == 0:
        return []
    gap = round(gap_s / F0_HOP_S)
    ranges, s0, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - prev > gap:
            ranges.append((int(s0), int(prev) + 1))
            s0 = i
        prev = i
    ranges.append((int(s0), int(prev) + 1))
    return ranges


def phrase_envelope(f0: np.ndarray, n: int, gap_s: float, levels: list[float]) -> tuple[np.ndarray, int]:
    """フレーズごとの抑揚。0.45 から始まり 65% 付近で山(level)、終わりは 0.4 まで落とし、最後 80ms で切る。"""
    env = np.ones(n)
    ranges = phrase_ranges(f0, gap_s)
    for k, (a, b) in enumerate(ranges):
        i0, i1 = int(a * F0_HOP_S * SR), min(int(b * F0_HOP_S * SR), n)
        pos = np.linspace(0, 1, i1 - i0)
        arch = np.where(pos < 0.65, 0.45 + 0.55 * np.sin(pos / 0.65 * np.pi / 2), 0.4 + 0.6 * np.cos((pos - 0.65) / 0.35 * np.pi / 2))
        env[i0:i1] = levels[min(k, len(levels) - 1)] * arch
        cut = min(int(0.08 * SR), i1 - i0)
        env[i1 - cut:i1] *= np.linspace(1, 0, cut)
    return env, len(ranges)


def attack_envelope(f0: np.ndarray, n: int, attack_s: float) -> np.ndarray:
    """各音符の頭を attack_s 秒(音符の半分まで)かけて 0→1 に立ち上げる包絡。"""
    env = np.ones(n)
    starts = note_starts(f0)
    ends = starts[1:] + [len(f0)]
    for s0, e0 in zip(starts, ends, strict=True):
        a = min(int(attack_s * SR), int((e0 - s0) * F0_HOP_S * SR / 2))
        i0 = int(s0 * F0_HOP_S * SR)
        if a > 0 and i0 + a <= n:
            env[i0:i0 + a] = np.linspace(0, 1, a) ** 2
    return env


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
    ap.add_argument("--growl", type=float, default=0.0, help="唸り(0〜1。既定 0 = なし)")
    ap.add_argument("--vibrato", type=float, default=0.0, help="ビブラートの深さ(セント。例 35。既定 0 = なし)")
    ap.add_argument("--dynamics", action="store_true", help="声の強弱(曲の弧 + 音符ごとのふくらみ)")
    ap.add_argument("--attack-beats", type=float, default=0.0, help="各音符の立ち上がりの拍数(既定 0 = なし)")
    ap.add_argument("--phrase-levels", default="", help="フレーズごとの音量(例 0.7,0.85,1)。空 = 抑揚なし")
    ap.add_argument("--phrase-gap", type=float, default=0.18, help="息継ぎとみなす休符の長さ(秒)")
    ap.add_argument("--peak", type=float, default=0.8, help="出力のピーク(0〜1、既定 0.8)")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    f0 = np.fromfile(args.f0, dtype="<f4").astype(np.float64)
    mod = read_wav(args.voice)
    beat = 60 / args.bpm * SR
    start, length = round(args.lead_beats * beat), round(args.beats * beat)
    y = vocode(mod, apply_vibrato(f0, args.vibrato) if args.vibrato > 0 else f0, growl=args.growl)
    if args.dynamics:
        y *= dynamics_envelope(f0, len(y))
    if args.attack_beats > 0:
        y *= attack_envelope(f0, len(y), args.attack_beats * 60 / args.bpm)
    if args.phrase_levels:
        env, n_ph = phrase_envelope(f0, len(y), args.phrase_gap, [float(v) for v in args.phrase_levels.split(",")])
        y *= env
        print(f"フレーズ数: {n_ph}(指定した音量の数 {len(args.phrase_levels.split(','))})")
    y = y[start:start + length]
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
