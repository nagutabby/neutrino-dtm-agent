#!/usr/bin/env python3
"""NEUTRINO の調声: 中間ファイル(timing / f0 / melspec)を編集して、ボコーダー向きの歌声に作り直す。

  neutrino_tune.py <base> [--preset vocoder|robot] [オプション…] [--dry-run]

<base> は neutrino_sing.py の出力から拡張子を除いたもの(例: work/vocals/70_phonk_vocal_v1)。
同じフォルダに <名前>.json(譜面)があること。出力は <名前>_tuned_vN.* (既存は上書きしない)。
そのあと `vocode.py <出力>.wav <出力>.f0 --bpm N` に渡す。

NEUTRINO は timing → f0 → melspec → wav の順に推定する。編集した段階より後ろだけを --skip-* で作り直す:
  1. timing.lab 編集(子音を短く)   → f0・melspec を再推定
  2. f0 編集(音高を譜面へ固定)      → melspec を再推定
  3. melspec 編集(高域・子音を持ち上げ)
  4. wav を再合成(位相が毎回変わるので、wav は最後に1回だけ作る)

ボコーダー向きにする理由: キャリア(鋸波)は f0 が安定して初めて「音程のある声」に聞こえ、
子音と高域が出ていないと歌詞が潰れる。ビブラートやゆらぎは固定し、子音は短く切れよく、高域は持ち上げる。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from common import load_dotenv
from neutrino_sing import STEPS, parse_pitch

FRAME_S = 0.010  # f0 / melspec のフレーム間隔
VOWELS = {"a", "i", "u", "e", "o", "A", "I", "U", "E", "O", "N"}  # N(ん)は有声なので子音扱いしない
NON_CONS = VOWELS | {"pau", "sil", "br", "cl"}
FLOOR = -6.9  # melspec の無音フロア(-7)直上。これ以下の bin は編集しない
HF_BIN = 60  # 約 5kHz 以上(100 bin のメル軸)
CONS_BIN = 40  # 約 2kHz 以上

PRESETS = {
    "vocoder": dict(pitch_lock=0.9, glide_ms=40, smooth=3, consonant_scale=0.7, hf_boost=0.5, cons_boost=0.6),
    "robot": dict(pitch_lock=1.0, glide_ms=15, smooth=1, consonant_scale=0.6, hf_boost=0.6, cons_boost=0.8),
}


def midi_of(name: str) -> int:
    step, alter, octave = parse_pitch(name)
    return 12 * (octave + 1) + STEPS[step] + alter


def read_lab(path: Path) -> list[list]:
    return [[int(s), int(e), p] for s, e, p in (ln.split() for ln in path.read_text().splitlines() if ln.strip())]


def write_lab(path: Path, rows: list[list]) -> None:
    path.write_text("".join(f"{s} {e} {p}\n" for s, e, p in rows))


def tighten_consonants(rows: list[list], scale: float) -> list[list]:
    """子音の長さを scale 倍にする。母音の頭(=拍の位置)は動かさず、直前の音素が延びて埋める。"""
    rows = [r[:] for r in rows]
    for i in range(1, len(rows)):
        s, e, p = rows[i]
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        if p in NON_CONS or not nxt or nxt[2] not in VOWELS or nxt[0] != e or rows[i - 1][1] != s:
            continue
        ns = e - round((e - s) * scale)
        rows[i][0], rows[i - 1][1] = ns, ns
    return rows


def note_track(spec: dict, n_frames: int, lead_beats: float = 4.0):
    """フレームごとの (目標 f0 の対数, 音符の頭からの経過秒)。休符は NaN。"""
    spb = 60 / spec["bpm"]
    target = np.full(n_frames, np.nan)
    since = np.zeros(n_frames)
    t = lead_beats * spb
    for _lyric, pitch, beats in spec["notes"]:
        end = t + beats * spb
        if pitch:
            hz = 440 * 2 ** ((midi_of(pitch) - 69) / 12)
            a, b = round(t / FRAME_S), min(round(end / FRAME_S), n_frames)
            target[a:b] = np.log(hz)
            since[a:b] = (np.arange(a, b) * FRAME_S) - t
        t = end
    return target, since


def smooth_voiced(logf: np.ndarray, voiced: np.ndarray, n: int) -> np.ndarray:
    """有声区間の中だけで移動平均(無声との境目をなだらかにしない)。"""
    if n <= 1:
        return logf
    out, k = logf.copy(), np.ones(n) / n
    idx = np.flatnonzero(voiced)
    for run in np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1):
        if len(run) >= n:
            out[run] = np.convolve(np.pad(logf[run], n // 2, mode="edge"), k, mode="valid")
    return out


def lock_pitch(f0: np.ndarray, spec: dict, lock: float, glide_ms: float, smooth: int) -> np.ndarray:
    voiced = f0 > 0
    logf = np.where(voiced, np.log(np.where(voiced, f0, 1.0)), 0.0)
    target, since = note_track(spec, len(f0))
    ramp = np.clip(since / max(glide_ms / 1000, 1e-6), 0, 1)  # 音符の頭の滑らかな入りは残す
    w = np.where(voiced & ~np.isnan(target), lock * ramp, 0.0)
    logf = np.where(w > 0, (1 - w) * logf + w * np.nan_to_num(target), logf)
    logf = smooth_voiced(logf, voiced, smooth)
    return np.where(voiced, np.exp(logf), 0.0)


def cents_error(f0: np.ndarray, spec: dict) -> float:
    target, since = note_track(spec, len(f0))
    m = (f0 > 0) & ~np.isnan(target) & (since > 0.06)
    return float(np.sqrt(np.mean((1200 * (np.log(f0[m]) - target[m]) / np.log(2)) ** 2))) if m.any() else 0.0


def boost_melspec(mel: np.ndarray, timing: list[list], hf: float, cons: float) -> np.ndarray:
    mel = mel.copy()
    active = mel.max(axis=1) > FLOOR
    if hf:
        sel = mel[:, HF_BIN:]
        mel[:, HF_BIN:] = np.where(active[:, None] & (sel > FLOOR), sel + hf, sel)
    if cons:
        for s, e, p in timing:
            if p in NON_CONS:
                continue
            a, b = round(s * 1e-7 / FRAME_S), min(round(e * 1e-7 / FRAME_S) + 1, len(mel))
            sel = mel[a:b, CONS_BIN:]
            mel[a:b, CONS_BIN:] = np.where(sel > FLOOR, sel + cons, sel)
    return mel


def hf_share(wav: Path) -> float:
    import vocode
    x = vocode.read_wav(wav)
    sp = np.abs(np.fft.rfft(x)) ** 2
    return float(sp[np.fft.rfftfreq(len(x), 1 / vocode.SR) > 4000].sum() / sp.sum())


def next_out(base: Path) -> Path:
    stem = re.sub(r"_v\d+$", "", base.name) + "_tuned"
    used = [int(m.group(1)) for p in base.parent.glob(f"{stem}_v*.f0")
            if (m := re.fullmatch(rf"{re.escape(stem)}_v(\d+)\.f0", p.name))]
    return base.parent / f"{stem}_v{max(used, default=0) + 1}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("base", type=Path)
    ap.add_argument("--preset", choices=sorted(PRESETS), default="vocoder")
    ap.add_argument("--pitch-lock", type=float, help="音高を譜面へ寄せる強さ 0〜1(1 で完全固定)")
    ap.add_argument("--glide-ms", type=float, help="音符の頭の滑らかな入りを残す長さ(ms)")
    ap.add_argument("--smooth", type=int, help="f0 の移動平均(フレーム数。1 で無し)")
    ap.add_argument("--consonant-scale", type=float, help="子音の長さの倍率(1 で無変更)")
    ap.add_argument("--hf-boost", type=float, help="約 5kHz 以上の melspec に足す値(対数、0.5 前後)")
    ap.add_argument("--cons-boost", type=float, help="子音区間の約 2kHz 以上に足す値")
    ap.add_argument("--model", default="MERROW", help="neutrino_sing.py で使ったモデル")
    ap.add_argument("--phrase", type=Path, help="譜面 JSON(既定: <base から _vN を除いた名前>.json)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    load_dotenv()

    p = {**PRESETS[args.preset], **{k: v for k, v in vars(args).items() if k in PRESETS["vocoder"] and v is not None}}
    base = args.base.resolve()
    phrase = args.phrase or base.with_name(re.sub(r"_v\d+$", "", base.name) + ".json")
    src = {k: base.with_suffix(f".{k}") for k in ("full.lab", "mono.lab", "timing.lab", "f0", "melspec", "wav")}
    for k, f in [*src.items(), ("phrase", phrase)]:
        if not f.is_file():
            sys.exit(f"見つかりません: {f}({k})")
    neutrino = Path(os.environ.get("NEUTRINO_DIR", "~/neutrino")).expanduser()
    model = neutrino / "model" / args.model
    if not (neutrino / "bin/neutrino").exists() or not model.exists():
        sys.exit(f"NEUTRINO またはモデルが見つかりません: {neutrino} / {args.model}")
    spec = json.loads(phrase.read_text(encoding="utf-8"))
    out = next_out(base)
    o = {k: out.with_suffix(f".{k}") for k in src}
    print(f"出力先: {out}.*   設定: {p}")
    if args.dry_run:
        return 0

    env = {**os.environ, "DYLD_LIBRARY_PATH": f"{neutrino / 'bin'}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"}
    tmp_wav = Path(tempfile.mkdtemp()) / "unused.wav"

    def run(wav: Path, *skips: str) -> None:
        cmd = [str(neutrino / "bin/neutrino"), str(o["full.lab"]), str(o["timing.lab"]), str(o["f0"]),
               str(o["melspec"]), str(wav), f"{model}/", "-n", "4", "-s", "48000", "-b", "16", *skips]
        r = subprocess.run(cmd, env=env, cwd=neutrino, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"NEUTRINO が失敗しました({r.returncode}):\n{r.stderr or r.stdout}")

    for k in ("full.lab", "mono.lab", "timing.lab", "f0", "melspec"):
        shutil.copy(src[k], o[k])
    f0_before = np.fromfile(src["f0"], dtype="<f4").astype(np.float64)
    err_before = cents_error(f0_before, spec)

    if p["consonant_scale"] != 1:  # 1. timing を編集 → f0・melspec を推定し直す
        write_lab(o["timing.lab"], tighten_consonants(read_lab(src["timing.lab"]), p["consonant_scale"]))
        run(tmp_wav, "--skip-timing", "--skip-wav")
    if p["pitch_lock"] > 0 or p["smooth"] > 1:  # 2. f0 を編集 → melspec を推定し直す
        f0 = np.fromfile(o["f0"], dtype="<f4").astype(np.float64)
        lock_pitch(f0, spec, p["pitch_lock"], p["glide_ms"], p["smooth"]).astype("<f4").tofile(o["f0"])
        run(tmp_wav, "--skip-timing", "--skip-f0", "--skip-wav")
    if p["hf_boost"] or p["cons_boost"]:  # 3. melspec を編集
        mel = np.fromfile(o["melspec"], dtype="<f4").reshape(-1, 100)
        boost_melspec(mel, read_lab(o["timing.lab"]), p["hf_boost"], p["cons_boost"]).astype("<f4").tofile(o["melspec"])
    run(o["wav"], "--skip-timing", "--skip-f0", "--skip-melspec")  # 4. wav を1回だけ合成

    f0_after = np.fromfile(o["f0"], dtype="<f4").astype(np.float64)
    print(f"譜面の音高からのずれ(RMS): {err_before:.0f} セント → {cents_error(f0_after, spec):.0f} セント")
    print(f"4kHz 以上のエネルギー比: {hf_share(src['wav']) * 100:.1f}% → {hf_share(o['wav']) * 100:.1f}%")
    print(f"出力: {o['wav']}\n次: uv run scripts/vocode.py {o['wav']} {o['f0']} --bpm {spec['bpm']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
