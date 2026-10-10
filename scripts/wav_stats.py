#!/usr/bin/env python3
"""録音した wav の数値(エージェントは聴けないので、改善案とレビューの根拠にする)。

  wav_stats.py <wav> [--window 秒]

出す数値: ピーク/RMS(dBFS)、クリップ有無、左右の相関(1=モノ寄り)、帯域ごとのエネルギー比
(低 <200Hz / 低中 200-800 / 中高 0.8-4k / 高 >4k)、窓ごと(既定 2 秒)の RMS の推移。
聴感の断定はしない。数値は「聴いて確かめる箇所」の手がかり。
"""

from __future__ import annotations

import argparse
import sys
import wave

import numpy as np

BANDS = (("低 <200Hz", 0, 200), ("低中 200-800Hz", 200, 800), ("中高 0.8-4kHz", 800, 4000), ("高 >4kHz", 4000, 1e9))


def db(x: float) -> float:
    return 20 * np.log10(max(x, 1e-9))


def load(path: str) -> tuple[np.ndarray, int]:
    with wave.open(path, "rb") as w:
        n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(n)
    if sw != 2:
        sys.exit("[エラー] 16bit PCM の wav のみ(live_render.py の出力を使う)")
    a = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768
    return a.reshape(-1, ch), sr


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("wav")
    ap.add_argument("--window", type=float, default=2.0)
    a = ap.parse_args()
    x, sr = load(a.wav)
    mono = x.mean(axis=1)
    print(f"長さ {len(x) / sr:.1f} 秒 / {sr} Hz / {x.shape[1]}ch")
    peak = np.abs(x).max()
    print(f"ピーク {db(peak):.1f} dBFS" + (" ← クリップ(0 dBFS 付近)" if peak >= 0.999 else ""))
    print(f"RMS {db(np.sqrt((mono**2).mean())):.1f} dBFS")
    if x.shape[1] == 2 and x[:, 0].std() > 0 and x[:, 1].std() > 0:
        print(f"左右の相関 {np.corrcoef(x[:, 0], x[:, 1])[0, 1]:.2f}(1 に近いほどモノ寄り)")
    spec = np.abs(np.fft.rfft(mono)) ** 2
    freqs = np.fft.rfftfreq(len(mono), 1 / sr)
    tot = spec.sum() or 1.0
    print("帯域のエネルギー比: " + " / ".join(f"{n} {spec[(freqs >= lo) & (freqs < hi)].sum() / tot * 100:.0f}%" for n, lo, hi in BANDS))
    step = int(a.window * sr)
    rms = [db(np.sqrt((mono[i : i + step] ** 2).mean())) for i in range(0, len(mono) - step // 2, step)]
    print(f"{a.window:g} 秒ごとの RMS(dBFS): " + " ".join(f"{r:.0f}" for r in rms))


if __name__ == "__main__":
    main()
