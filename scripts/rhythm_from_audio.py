#!/usr/bin/env python3
"""録音(手拍子・机を叩く音・口のビートボックス)から、1本のリズム(1ステム)をグリッド記法にする。

  rhythm_from_audio.py <audio> [--stem kick|snare|hat|clap] [--bpm N] [--grid 4] [--bars N] [-o out.rb]

1回の録音に入れるのは1本のリズムだけ(キックだけ・ハイハットだけ、など)。種類の自動判定はしない。
流れ: ffmpeg で 22.05kHz モノラルに変換 → スペクトルフラックス(各周波数の急な立ち上がり)で音の頭を検出
      → 音量の立ち上がりまで戻って頭の時刻を決める → 最大音量で強さ(X / x / o)
      → 拍に量子化(1マス = 1/grid 拍)→ `x... .... x... ....` のパターンと grid_play の live_loop を書き出す。
録音のしかた: `record_mic.py --bpm N --count-only` で、数えのキックだけ鳴らして止まる(叩いた音とキックが混ざらない)。
  横の <名>.json があれば、BPM と拍の位置(カウントのあとが拍 0)を自動で使う。なければ最初の音が拍 0。
  `--bpm` を省くと work/current.rb の use_bpm を読む。
--stem は鳴らす音の選択(kick = bd_haus / snare = sn_dub / hat = drum_cymbal_closed / clap = drum_cowbell)。既定は kick。
出力の既定は work/proposals/<音声の名前>_rhythm.rb。ヘルパー(docs/live-grid.rb)を current.rb の先頭に貼ってある前提。
聴いて確かめること(エージェントは聴けない)。
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from common import WORK
from melody_from_audio import SR, decode, find_kick_grid, fmt, read_bpm

NFFT, HOP = 1024, 256
STEMS = {  # 名前: (サンプル, amp)
    "kick": ("bd_haus", 1.0),
    "snare": ("sn_dub", 0.9),
    "hat": ("drum_cymbal_closed", 0.7),
    "clap": ("drum_cowbell", 0.8),
}


def stft_mag(x: np.ndarray) -> np.ndarray:
    n = max(0, 1 + (len(x) - NFFT) // HOP)
    if n == 0:
        return np.zeros((0, NFFT // 2 + 1))
    idx = np.arange(NFFT)[None, :] + HOP * np.arange(n)[:, None]
    return np.abs(np.fft.rfft(x[idx] * np.hanning(NFFT), axis=1))


def refine_onset(x: np.ndarray, t: int) -> int:
    """フラックスのピーク(フレーム t)から、音量の立ち上がりの頭(サンプル番号)まで戻る。"""
    lo = max(0, t * HOP - int(0.03 * SR))
    hi = min(len(x), t * HOP + NFFT + int(0.1 * SR))
    k = max(1, int(0.004 * SR))
    env = np.convolve(np.abs(x[lo:hi]), np.ones(k) / k, mode="same")
    p = int(np.argmax(env))
    below = np.where(env[:p] < 0.15 * env[p])[0]
    return lo + (int(below[-1]) + 1 if len(below) else 0)


def detect_onsets(x: np.ndarray, threshold: float = 0.25, min_gap: float = 0.08) -> list[int]:
    """音の頭のサンプル番号。スペクトルフラックスの局所最大のうち、強い方(上位10%目安)の threshold 倍以上。"""
    mag = stft_mag(x)
    if len(mag) < 8:
        return []
    lg = np.log1p(1000.0 * mag / max(float(mag.max()), 1e-12))
    flux = np.concatenate(([0.0], np.maximum(0.0, np.diff(lg, axis=0)).sum(axis=1)))
    cand = [t for t in range(3, len(flux) - 3) if flux[t] == flux[t - 3 : t + 4].max() and flux[t] > 0]
    if not cand:
        return []
    ref = float(np.percentile(flux[cand], 90))
    keep = [t for t in cand if flux[t] >= threshold * ref]
    gap = max(1, int(min_gap * SR / HOP))
    out: list[int] = []
    for t in keep:  # 近すぎる頭(余韻の揺れ)は強い方だけ
        if out and t - out[-1] < gap:
            if flux[t] > flux[out[-1]]:
                out[-1] = t
        else:
            out.append(t)
    return sorted({refine_onset(x, t) for t in out})


def peak_after(x: np.ndarray, a: int) -> float:
    return float(np.max(np.abs(x[a : a + int(0.08 * SR)]))) if a < len(x) else 0.0


def level_char(peak: float, ref: float) -> str:
    r = peak / max(ref, 1e-12)
    return "X" if r >= 0.8 else "x" if r >= 0.45 else "o"


def build_pattern(hits: list[tuple[int, float]], grid: int, meter: int, bars: int | None) -> tuple[str, int]:
    """hits = [(マス, 音量)] → 文字列。小節は ' | '、拍は空白で区切る。(文字列, 小節数)"""
    cpb = grid * meter
    last = max((c for c, _ in hits), default=0)
    nb = bars or max(1, math.ceil((last + 1) / cpb))
    ref = max((v for _, v in hits), default=1.0)
    peak: dict[int, float] = {}
    for c, v in hits:
        if c < nb * cpb and v > peak.get(c, -1.0):  # 同じマスは大きい方
            peak[c] = v
    ch = ["."] * (nb * cpb)
    for c, v in peak.items():
        ch[c] = level_char(v, ref)
    beats = ["".join(ch[i : i + grid]) for i in range(0, len(ch), grid)]
    return " | ".join(" ".join(beats[b * meter : (b + 1) * meter]) for b in range(nb)), nb


def render_ruby(pattern: str, stem: str, bpm: float, src: str, grid: int, meter: int, nb: int) -> str:
    sample, amp = STEMS[stem]
    head = [
        f"# 録音 {src} から自動採譜(rhythm_from_audio.py)。ステム {stem} / BPM {fmt(bpm)} / {nb} 小節 / 1小節 = {meter}拍 × {grid}マス",
        "# 先頭に docs/live-grid.rb のヘルパーと use_bpm がある前提。X = 強 x = ふつう o = 弱 . = 休み",
    ]
    if grid != 4 or meter != 4:
        head.append(f"# grid_res {grid} / grid_meter {meter} を use_bpm の次に書くこと")
    return "\n".join(
        [
            *head,
            "",
            f'audio_{stem}_rhythm = "{pattern}"',
            f"audio_{stem}_voice = grid_voice :sample, :{sample}, amp: {amp}",
            f"live_loop :audio_{stem} do",
            f"  grid_play audio_{stem}_voice, audio_{stem}_rhythm",
            "end",
            "",
        ]
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("audio", help="録音(mp3 / wav など。ffmpeg で読めるもの)")
    ap.add_argument("--stem", choices=list(STEMS), default="kick", help="このリズムを鳴らすステム(既定 kick)")
    ap.add_argument("--bpm", type=float, help="曲のテンポ(省略: <名>.json、なければ work/current.rb の use_bpm)")
    ap.add_argument("--grid", type=int, default=4, help="1拍のマス数(既定 4 = 16分音符。3連符は 3)")
    ap.add_argument("--meter", type=int, default=4, help="1小節の拍数(既定 4)")
    ap.add_argument("--bars", type=int, help="小節数(省略: 最後の音を含む小節数)")
    ap.add_argument("--threshold", type=float, default=0.25, help="音の頭の検出の厳しさ(既定 0.25。小さいほど弱い音も拾う)")
    ap.add_argument("--no-kick", action="store_true", help="<名>.json があっても使わない(最初の音を拍 0 にする)")
    ap.add_argument("-o", "--output", help="出力 .rb(既定: work/proposals/<名前>_rhythm.rb)")
    ap.add_argument("--force", action="store_true", help="既存の出力を上書きする")
    a = ap.parse_args()

    src = Path(a.audio).expanduser()
    if not src.is_file():
        src = next((p for p in (WORK / a.audio, WORK / "recordings" / a.audio) if p.is_file()), src)
    if not src.is_file():
        sys.exit(f"[エラー] ファイルがありません: {a.audio}")
    meta = None
    side = src.with_suffix(".json")
    if side.is_file() and not a.no_kick:
        try:
            meta = json.loads(side.read_text(encoding="utf-8"))
            float(meta["bpm"]), float(meta["count_in_beats"])
        except (ValueError, KeyError, TypeError):
            sys.exit(f"[エラー] {side} を読めません(record_mic.py --bpm が作る形式)")
    bpm = a.bpm or (float(meta["bpm"]) if meta else None) or read_bpm()
    if not bpm:
        sys.exit("[エラー] --bpm を指定してください")
    if meta and abs(bpm - float(meta["bpm"])) > 0.01:
        sys.exit(f"[エラー] --bpm {fmt(bpm)} が録音時の BPM {fmt(float(meta['bpm']))} と違います")
    out = Path(a.output).expanduser() if a.output else WORK / "proposals" / f"{src.stem}_rhythm.rb"
    if out.exists() and not a.force:
        sys.exit(f"[エラー] 既に存在します(上書きは --force): {out}")

    x = decode(src)
    onsets = detect_onsets(x, a.threshold)
    if not onsets:
        sys.exit("[エラー] 音の頭が見つかりません(小さすぎる・つながっている)。はっきり叩いて/発音して録り直すか、--threshold を下げてください")
    t0 = onsets[0] / SR
    if meta:
        g = find_kick_grid(x, bpm)
        if g and g[1] >= 3.0:
            t0 = g[0] + float(meta["count_in_beats"]) * 60.0 / bpm
            print(f"キック: 最初の拍 {g[0]:.2f} 秒 / 確かさ {g[1]:.1f} → カウントのあと(拍 {fmt(float(meta['count_in_beats']))})が拍 0", file=sys.stderr)
        else:
            print("[警告] 録音にキックが見つかりません。最初の音を拍 0 にして続けます", file=sys.stderr)

    k = bpm / 60.0 * a.grid
    rows, hits, skipped = [], [], 0
    for a_ in onsets:
        cell = round((a_ / SR - t0) * k)
        if cell < 0:
            skipped += 1
            continue
        pk = peak_after(x, a_)
        rows.append((a_ / SR, cell / a.grid, pk))
        hits.append((cell, pk))
    if not hits:
        sys.exit("[エラー] カウントのあとに叩いた音がありません(拍 0 より前の音は捨てます)")
    pattern, nb = build_pattern(hits, a.grid, a.meter, a.bars)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_ruby(pattern, a.stem, bpm, src.name, a.grid, a.meter, nb), encoding="utf-8")

    print(f"録音: {len(x) / SR:.1f} 秒 / 音の頭 {len(onsets)} 個(カウント内で捨てた {skipped} 個)/ {nb} 小節 / BPM {fmt(bpm)} / ステム {a.stem}", file=sys.stderr)
    print("  時刻    拍    音量", file=sys.stderr)
    for tm, beat, pk in rows:
        print(f"  {tm:5.2f}s {beat:5.2f}  {pk:.2f}", file=sys.stderr)
    print(f"  {pattern}", file=sys.stderr)
    print(f"出力: {out}", file=sys.stderr)
    print(f"確認: uv run scripts/live_check.py {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
