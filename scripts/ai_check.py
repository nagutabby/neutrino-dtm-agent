#!/usr/bin/env python3
"""AI 生成音楽にありがちな問題(docs/ai-music-pitfalls.md)を数値でチェックする。

使い方:
  ai_check.py <song> --mix mix/step14_v1.wav     ミックス(音声)の検査。要 `uv run --group reference`
  ai_check.py <song> --midi tracks/04_bass_v1.mid ...  トラック MIDI の検査(複数可)
  ai_check.py <song> --all                       最新ミックスと tracks/ の最新版 MIDI を全部検査
警告は「何が/なぜ/直し方」で出す。聴感の判断はせず、数値の目安だけ(最終判断はユーザーの耳)。
--strict で警告があれば終了コード 2。
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import midi_tools
from common import require_project


def warn(msgs: list[str], what: str, why: str, fix: str) -> None:
    msgs.append(f"⚠ {what}\n    なぜ: {why}\n    直し方: {fix}")


def check_mix(path: Path) -> list[str]:
    import librosa
    import numpy as np

    y, sr = librosa.load(path, sr=None, mono=False)
    y = y if y.ndim == 2 else np.stack([y, y])
    m = y.mean(0)
    out: list[str] = []

    win = sr * 4
    db = np.array([20 * np.log10(np.sqrt((m[i:i + win] ** 2).mean()) + 1e-9) for i in range(0, len(m) - win, win)])
    mid = db[1:-1] if len(db) > 4 else db
    spread = float(np.percentile(mid, 95) - np.percentile(mid, 5)) if len(mid) else 0.0
    if spread < 6:
        warn(out, f"曲の起伏が小さい(4秒ごとの音量の幅 {spread:.1f}dB、目安 6dB 以上)",
             "AI 生成はどの区間も同じ密度で鳴りがち。山と谷がなく平板に聞こえる",
             "区間ごとに鳴らすトラックを変える(谷の区間は半分以下)。spec の rhythm に区間を書く")

    S = np.abs(librosa.stft(m, n_fft=4096)) ** 2
    f = librosa.fft_frequencies(sr=sr, n_fft=4096)
    e = S.mean(1)
    tot = e.sum()
    hi = e[f >= 2000].sum() / tot
    low_mid = e[(f >= 150) & (f < 500)].sum() / tot
    if hi < 0.05:
        warn(out, f"高域(2kHz 以上)が少ない({hi:.1%}、目安 5% 以上)", "高域の抜け・空気感がなく、こもって聞こえやすい",
             "旋律系の cutoff を上げる/倍音(index)を増やす/ハットを足す")
    if low_mid > 0.4:
        warn(out, f"中低域(150〜500Hz)に集中({low_mid:.1%}、目安 40% 以下)", "ベース・パッド・コードが同じ帯域で重なり濁る",
             "ベースの drive/decay を下げる、コードやパッドの音域・cutoff を分ける")

    corr = float(np.corrcoef(y[0], y[1])[0, 1])
    if corr > 0.95:
        warn(out, f"ステレオがほぼモノラル(左右相関 {corr:.2f}、目安 0.95 以下)", "全パートが中央付近に置かれ、広がりがない",
             "09-mix の pan で pad/arp/voxchop などを ±0.3〜0.5 に振る")

    hop = sr // 2
    mf = librosa.feature.mfcc(y=m, sr=sr, hop_length=hop)
    n = mf.shape[1] // 16 * 16
    if n >= 32:
        seg = mf[:, :n].T.reshape(-1, 16 * mf.shape[0])
        sim = np.corrcoef(seg)
        np.fill_diagonal(sim, np.nan)
        rep = float(np.nanmean(sim))
        if rep > 0.85:
            warn(out, f"8秒区間どうしが似すぎ(音色相関 {rep:.2f}、目安 0.85 以下)", "同じループの貼り合わせで、展開が感じられない",
                 "区間ごとに素材・音域・密度を変える。サビ相当は音域を上げる/トラックを足す")

    peak = float(np.abs(y).max())
    if peak >= 0.99:
        warn(out, f"ピークが 0dBFS 付近({peak:.3f})", "クリップの恐れ", "09-mix の loudness_lufs を下げる")
    head = float(np.sqrt((m[: sr * 2] ** 2).mean()))
    if head > 0.05:
        warn(out, "冒頭 2 秒がすでに大音量", "導入(静→動)がなく唐突", "intro は少ないトラックで始める")
    return out or ["✔ ミックスに目立つ問題なし"]


def check_midi(path: Path) -> list[str]:
    import statistics

    m = midi_tools.load(path)
    out: list[str] = []
    if not m.notes:
        return ["(ノートなし)"]
    vels = [n.vel for n in m.notes]
    if len(set(vels)) <= 2 and len(vels) > 16:
        warn(out, f"ベロシティがほぼ一定(種類 {len(set(vels))}、値 {sorted(set(vels))})", "機械的で、強弱の抑揚(拍・フレーズ)がない",
             "強拍を強く・裏拍や装飾音を弱く、フレーズ頭と終わりで ±8〜12 つける")
    elif len(vels) > 16 and statistics.pstdev(vels) < 3:
        warn(out, f"ベロシティの揺れが小さい(標準偏差 {statistics.pstdev(vels):.1f})", "機械的に聞こえる", "拍位置で強弱を付ける")

    bar = m.ppq * 4 * m.time_sig[0] // m.time_sig[1]
    sigs: dict[int, list[tuple[int, int]]] = {}
    for n in m.notes:
        sigs.setdefault(n.start // bar, []).append((n.start % bar, n.pitch))
    keys = [tuple(sorted(v)) for _, v in sorted(sigs.items())]
    if len(keys) >= 8:
        top, cnt = Counter(keys).most_common(1)[0]
        if cnt / len(keys) > 0.7:
            warn(out, f"同一小節の繰り返しが {cnt}/{len(keys)} 小節", "AI 生成は1小節パターンのコピーで済ませがち。単調になる",
                 "4小節ごとに音を1〜2個変える/終止の小節だけ別パターンにする(複製ではなく変化を足す)")

    pitches = [n.pitch for n in m.notes]
    if len(m.notes) > 16 and max(pitches) - min(pitches) < 5:
        warn(out, f"音域が狭い({max(pitches) - min(pitches)} 半音)", "旋律の山がなく平坦", "区間ごとに音域を上下させる")

    total_end = max(n.end for n in m.notes)
    covered = len({t for n in m.notes for t in range(n.start // 30, max(n.start // 30 + 1, n.end // 30))}) * 30
    if total_end and covered / total_end > 0.97 and len(m.notes) > 16 and "perc" not in path.name and "pad" not in path.name \
            and "strings" not in path.name and "bass" not in path.name:
        warn(out, "休符がほとんどない", "息継ぎ・間がなく窮屈", "フレーズ末に 1 拍以上の休符を入れる")

    starts = [n.start % (m.ppq // 4) for n in m.notes]
    if all(s == 0 for s in starts) and len(m.notes) > 32:
        out.append("ℹ 全ノートが 16 分グリッド上(人間味の揺れなし)。ジャンルが機械的ノリ(ハウス等)なら問題なし、"
                   "そうでなければ微小な前後ずれ(±5〜15 tick)を検討")
    return out or ["✔ 目立つ問題なし"]


def latest(files: list[Path]) -> list[Path]:
    best: dict[str, Path] = {}
    for p in sorted(files):
        key = re.sub(r"_v\d+$", "", p.stem)
        ver = int(re.search(r"_v(\d+)$", p.stem).group(1)) if re.search(r"_v(\d+)$", p.stem) else 0
        cur = best.get(key)
        if cur is None or ver >= (int(re.search(r"_v(\d+)$", cur.stem).group(1)) if re.search(r"_v(\d+)$", cur.stem) else 0):
            best[key] = p
    return list(best.values())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("--mix")
    ap.add_argument("--midi", nargs="*", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    root = require_project(a.song)
    mixes = [root / a.mix] if a.mix else []
    midis = [root / p for p in a.midi]
    if a.all:
        mx = sorted((root / "mix").glob("step*_v*.wav"), key=lambda p: int(re.search(r"step(\d+)", p.stem).group(1)))
        mixes = mx[-1:] if mx else []
        midis = latest(list((root / "tracks").glob("*.mid")))
    if not mixes and not midis:
        sys.exit("検査対象がありません(--mix / --midi / --all)")
    bad = 0
    for p in mixes:
        print(f"## {p.relative_to(root)}")
        res = check_mix(p)
        bad += sum(r.startswith("⚠") for r in res)
        print("\n".join(res), "\n")
    for p in midis:
        print(f"## {p.relative_to(root)}")
        res = check_midi(p)
        bad += sum(r.startswith("⚠") for r in res)
        print("\n".join(res), "\n")
    print(f"警告 {bad} 件(目安であり、最終判断はユーザーの耳)")
    if a.strict and bad:
        sys.exit(2)


if __name__ == "__main__":
    main()
