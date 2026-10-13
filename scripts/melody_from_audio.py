#!/usr/bin/env python3
"""録音(mp3/wav)から単音のメロディを取り出し、曲のキーに合わせた Sonic Pi のコードにする。

  melody_from_audio.py <audio> --key "F minor" [--bpm 100] [--grid 4] [--low 60 --high 84]
                       [--octave N] [--min-note 0.1] [--start-beat 0] [-o out.rb]

流れ: ffmpeg で 22.05kHz モノラルに変換 → YIN でフレームごとの基本周波数 → 全体の音程ずれ(チューニング)を補正
      → 各フレームをキーの音階に最も近い音へ寄せる → 中央値フィルタで揺れを均す → 同じ音の連なりを1音符に
      → 拍に量子化(1マス = 1/grid 拍)→ 音域に収まるオクターブへ → `[拍の位置, 音名, 長さ]` の並びを書き出す。
キー: 「F minor」「C# major」「Bb dorian」「Fm」など。音階は --list-scales で一覧。
BPM: 省略すると work/current.rb の use_bpm を読む。
最初の音の位置が --start-beat(既定 0)になるよう全体をずらす(頭を小節線に合わせたい録音向け)。
キック: record_mic.py --bpm N で録ると、キックの録音(.mp3)の横に <名>.json ができる。あれば自動で、
  録音に入ったキックから拍の位置を求め(カウントのあとが拍 0)、130Hz 以下を削って(キック除去)メロディだけを取り出す。
出力の既定は work/proposals/<音声の名前>_melody.rb(既存は --force がない限り上書きしない)。
単音のみ対応(和音・伴奏つきの録音は誤検出する)。結果は聴いて確かめること。
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from common import WORK

SR = 22050
WIN = 1024  # YIN の窓(約46ms)
HOP = 256  # フレーム間隔(約11.6ms)
FMIN, FMAX = 70.0, 1000.0

SCALES: dict[str, tuple[int, ...]] = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
    "major_pentatonic": (0, 2, 4, 7, 9),
    "minor_pentatonic": (0, 3, 5, 7, 10),
    "blues": (0, 3, 5, 6, 7, 10),
}
ALIASES = {"maj": "major", "ionian": "major", "min": "minor", "aeolian": "minor", "m": "minor", "": "major"}
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
SHARP_NAMES = ["c", "cs", "d", "ds", "e", "f", "fs", "g", "gs", "a", "as", "b"]
FLAT_NAMES = ["c", "db", "d", "eb", "e", "f", "gb", "g", "ab", "a", "bb", "b"]


@dataclass
class Key:
    tonic_pc: int
    scale: str
    use_flats: bool

    @property
    def pcs(self) -> set[int]:
        return {(self.tonic_pc + i) % 12 for i in SCALES[self.scale]}

    def label(self) -> str:
        names = FLAT_NAMES if self.use_flats else SHARP_NAMES
        return f"{names[self.tonic_pc].capitalize()} {self.scale}"


def parse_key(text: str) -> Key:
    m = re.fullmatch(r"\s*([A-Ga-g])([#b♯♭]?)\s*([A-Za-z_ ]*)\s*", text)
    if not m:
        raise ValueError(f"キーを読めません: {text!r}(例: \"F minor\" \"C# major\" \"Bb dorian\")")
    letter, acc, mode = m.group(1).upper(), m.group(2), m.group(3).strip().lower().replace(" ", "_")
    mode = ALIASES.get(mode, mode)
    if mode not in SCALES:
        raise ValueError(f"知らない音階です: {mode!r}(--list-scales で一覧)")
    pc = PC[letter] + {"#": 1, "♯": 1, "b": -1, "♭": -1, "": 0}[acc]
    minorish = SCALES[mode][2] == 3
    flat_tonics = {"D", "G", "C", "F"} if minorish else {"F"}
    use_flats = acc in ("b", "♭") or (acc == "" and letter in flat_tonics)
    return Key(pc % 12, mode, use_flats)


def decode(path: Path) -> np.ndarray:
    if not shutil.which("ffmpeg"):
        sys.exit("[エラー] ffmpeg がありません(brew install ffmpeg)")
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True,
    )
    if r.returncode != 0 or not r.stdout:
        sys.exit(f"[エラー] 音声を読めません: {path}\n{r.stderr.decode(errors='replace')}")
    return np.frombuffer(r.stdout, dtype="<f4").astype(np.float64)


def yin_track(x: np.ndarray, sr: int = SR, thr: float = 0.2, fmin: float = FMIN) -> tuple[np.ndarray, np.ndarray]:
    """フレームごとの (周波数 Hz, rms)。無声(音程なし)の周波数は nan。"""
    tau_min, tau_max = int(sr / FMAX), int(sr / fmin)
    size = WIN + tau_max
    n = max(0, 1 + (len(x) - size) // HOP)
    f0 = np.full(n, np.nan)
    rms = np.zeros(n)
    nfft = 1 << (size * 2 - 1).bit_length()
    taus = np.arange(1, tau_max + 1)
    for i in range(n):
        fr = x[i * HOP : i * HOP + size]
        c = WIN // 2  # 窓の中央の1ホップぶんの音量(音の切れ目を細かく見る)
        rms[i] = math.sqrt(float(np.mean(fr[c - HOP // 2 : c + HOP // 2] ** 2)))
        if rms[i] < 1e-4:
            continue
        sq = np.concatenate(([0.0], np.cumsum(fr**2)))
        e0 = sq[WIN]
        etau = sq[WIN + taus] - sq[taus]
        acf = np.fft.irfft(np.conj(np.fft.rfft(fr[:WIN], nfft)) * np.fft.rfft(fr, nfft), nfft)[1 : tau_max + 1]
        d = e0 + etau - 2 * acf
        cm = d * taus / np.maximum(np.cumsum(d), 1e-12)
        cand = np.where(cm[tau_min - 1 :] < thr)[0]
        if len(cand) == 0:
            continue
        t = cand[0] + tau_min - 1  # 添字 t = ラグ t+1
        while t + 1 < len(cm) and cm[t + 1] < cm[t]:
            t += 1
        lag = float(t + 1)
        if 0 < t < len(cm) - 1:  # 放物線補間
            a, b, c = cm[t - 1], cm[t], cm[t + 1]
            den = a - 2 * b + c
            if abs(den) > 1e-12:
                lag += 0.5 * (a - c) / den
        f0[i] = sr / lag
    return f0, rms


def highpass(x: np.ndarray, fc: float, sr: int = SR, order: int = 4) -> np.ndarray:
    """周波数領域のバターワース型ハイパス(位相は動かさない)。fc 以下のキックの低音を削る。"""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / sr)
    gain = 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-9)) ** (2 * order))
    return np.fft.irfft(spec * gain, len(x))


def find_kick_grid(x: np.ndarray, bpm: float, sr: int = SR, fc: float = 120.0) -> tuple[float, float] | None:
    """録音に入ったキックから拍の位相を求める。(最初のキックの時刻 秒, 確かさ)。見つからなければ None。

    120Hz 以下を取り出した音量の立ち上がりを、拍の間隔(60/bpm 秒)の櫛で2ms刻みに探し、最も合う位相を取る。
    確かさ = 最良の得点 / 平均の得点(3 未満は、キックが入っていないとみなす)。
    """
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / sr)
    low = np.fft.irfft(spec * (f <= fc), len(x))
    k = max(1, int(0.005 * sr))
    env = np.convolve(np.abs(low), np.ones(k) / k, mode="same")
    lag = int(0.008 * sr)
    onset = np.maximum(0.0, env[lag:] - env[:-lag])
    period = 60.0 / bpm * sr
    if len(onset) < period * 3:
        return None
    phases = np.arange(0, period, 0.002 * sr)
    score = np.empty(len(phases))
    for j, ph in enumerate(phases):
        idx = (ph + period * np.arange(int((len(onset) - ph) // period))).astype(int)
        score[j] = onset[idx].sum()
    best = int(np.argmax(score))
    conf = float(score[best] / max(float(score.mean()), 1e-12))
    ph = phases[best]
    idx = (ph + period * np.arange(int((len(onset) - ph) // period))).astype(int)
    # 最初に鳴ったキック: 拍ごとの低音の大きさ(拍の頭からの 0.25 秒)が、全体の目安の 35% を超える最初の拍
    # (立ち上がりの強さでは、歌い出しの低音のほうが大きく出て、数えのキックを見落とすため)
    w = int(0.25 * sr)
    level = np.array([np.sqrt(np.mean(low[i : i + w] ** 2)) for i in idx if i + w <= len(low)])
    first = int(np.argmax(level >= 0.35 * np.percentile(level, 75))) if len(level) else 0
    return float((ph + first * period) / sr), conf


def hz_to_midi(f: np.ndarray) -> np.ndarray:
    return 69 + 12 * np.log2(f / 440.0)


def snap_to_scale(m: float, pcs: set[int]) -> int:
    """m に最も近いキー内の整数音(同じ近さなら低い方)。"""
    base = int(math.floor(m))
    best, best_d = base, 1e9
    for c in range(base - 6, base + 8):
        if c % 12 in pcs:
            d = abs(c - m)
            if d < best_d - 1e-9 or (abs(d - best_d) <= 1e-9 and c < best):
                best, best_d = c, d
    return best


def median_filter(v: np.ndarray, k: int) -> np.ndarray:
    out = v.copy()
    h = k // 2
    for i in range(len(v)):
        if np.isnan(v[i]):
            continue
        w = v[max(0, i - h) : i + h + 1]
        out[i] = np.median(w[~np.isnan(w)])
    return out


@dataclass
class Note:
    start: float  # 秒
    end: float
    midi: int


def extract_notes(f0: np.ndarray, rms: np.ndarray, key: Key, min_note: float, tune: bool = True) -> tuple[list[Note], dict]:
    hop_s = HOP / SR
    voiced = ~np.isnan(f0)
    if voiced.any():
        gate = max(0.003, 0.12 * float(np.percentile(rms[voiced], 95)))
        voiced &= rms >= gate
    midi = np.where(voiced, hz_to_midi(np.where(voiced, f0, 440.0)), np.nan)
    info: dict = {"frames": len(f0), "voiced": int(voiced.sum()), "tune_cents": 0.0, "in_key": float("nan")}
    if not voiced.any():
        return [], info
    mv = midi[voiced]
    dev = mv - np.round(mv)
    tune_off = float(np.median(dev)) if tune else 0.0
    info["tune_cents"] = tune_off * 100
    mv = mv - tune_off
    midi[voiced] = mv
    info["in_key"] = float(np.mean([int(round(x)) % 12 in key.pcs for x in mv]))
    # 先に半音単位で音符に区切り(揺れを均す)、そのあと音符ごとの中央値をキーの音階へ寄せる
    rounded = median_filter(np.where(voiced, np.round(midi), np.nan), 7)
    runs: list[list] = []  # [丸めた音, 開始フレーム, 終了フレーム(含む)]
    for i, v in enumerate(rounded):
        if np.isnan(v):
            continue
        if runs and runs[-1][0] == int(v) and i - runs[-1][2] <= 3:  # 欠け2フレーム(約23ms)までは同じ音。それ以上の息継ぎ・切れ目は音を分ける
            runs[-1][2] = i
        else:
            runs.append([int(v), i, i])
    seg: list[Note] = []
    for _, s_, e_ in runs:
        if (e_ - s_ + 1) * hop_s < min_note:
            continue
        pitch = float(np.nanmedian(midi[s_ : e_ + 1]))
        n = Note(s_ * hop_s, (e_ + 1) * hop_s, snap_to_scale(pitch, key.pcs))
        if seg and seg[-1].midi == n.midi and n.start - seg[-1].end <= hop_s:  # 寄せた結果が同じ音で、隙間なく続くときだけ1音に(同じ音の連打は残す)
            seg[-1].end = n.end
        else:
            seg.append(n)
    return seg, info



def to_beats(
    notes: list[Note], bpm: float, grid: int, start_beat: float, t0: float | None = None
) -> list[tuple[float, int, float]]:
    """(拍の位置, midi, 長さ拍)。1マス = 1/grid 拍に量子化し、重ならないようにする。

    t0(秒)を渡すと、その時刻を拍 0 とする(キーが拍を示したとき)。拍 0 より前の音は捨てる。
    渡さなければ、最初の音を start_beat に置く。
    """
    if not notes:
        return []
    fixed = t0 is not None
    if t0 is None:
        t0 = notes[0].start
    k = bpm / 60.0

    def q(sec: float) -> int:
        return round(sec * k * grid)

    out: list[tuple[int, int, int]] = []
    for n in notes:
        s, e = q(n.start - t0), q(n.end - t0)
        if fixed and s < 0:
            continue
        e = max(e, s + 1)
        if out and s <= out[-1][0]:  # 同じマスに始まる音は長い方を残す
            if e - s > out[-1][2]:
                out[-1] = (out[-1][0], n.midi, e - out[-1][0])
            continue
        if out and out[-1][0] + out[-1][2] > s:  # 前の音が次の頭にかぶらないよう詰める
            out[-1] = (out[-1][0], out[-1][1], s - out[-1][0])
        out.append((s, n.midi, e - s))
    off = 0.0 if fixed else start_beat
    return [(off + s / grid, m, ln / grid) for s, m, ln in out]


def place_octave(beats: list[tuple[float, int, float]], low: int, high: int, octave: int | None) -> int:
    if not beats:
        return 0
    if octave is not None:
        return 12 * octave
    med = float(np.median([m for _, m, _ in beats]))
    return 12 * round(((low + high) / 2 - med) / 12)


def note_name(m: int, flats: bool) -> str:
    return f"{(FLAT_NAMES if flats else SHARP_NAMES)[m % 12]}{m // 12 - 1}"


def fmt(x: float) -> str:
    return f"{x:.4f}".rstrip("0").rstrip(".") if x != int(x) else str(int(x))


def render_ruby(
    beats: list[tuple[float, int, float]], shift: int, key: Key, bpm: float, src: str, label: str, loop_beats: int
) -> str:
    rows = ",\n".join(
        f"  [{fmt(p)}, :{note_name(m + shift, key.use_flats)}, {fmt(ln)}]" for p, m, ln in beats
    )
    return f"""# 録音 {src} から自動採譜(melody_from_audio.py)。キー {key.label()} に寄せた。BPM {fmt(bpm)} / {loop_beats} 拍ごとに繰り返す
# 形式: [拍の位置, 音名, 長さ(拍)]。use_bpm は current.rb 側に書いてある前提(ここでは書かない)
{label} = [
{rows}
]
{label}_beats = {loop_beats}

live_loop :{label} do
  use_synth :saw
  {label}.each do |pos, n, len|
    time_warp pos do
      play n, amp: 0.8, attack: 0.01, release: [len * 0.9, 0.1].max, cutoff: 100
    end
  end
  sleep {label}_beats
end
"""


def read_bpm() -> float | None:
    f = WORK / "current.rb"
    if f.is_file():
        m = re.search(r"^\s*use_bpm\s+([0-9.]+)", f.read_text(encoding="utf-8"), re.M)
        if m:
            return float(m.group(1))
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("audio", nargs="?", help="録音(mp3 / wav など。ffmpeg で読めるもの)")
    ap.add_argument("--key", help='曲のキー(例: "F minor")')
    ap.add_argument("--bpm", type=float, help="曲のテンポ(省略: work/current.rb の use_bpm)")
    ap.add_argument("--grid", type=int, default=4, help="1拍のマス数(既定 4 = 16分音符。3連符は 3)")
    ap.add_argument("--low", type=int, default=60, help="音域の下限 MIDI(既定 60 = C4)")
    ap.add_argument("--high", type=int, default=84, help="音域の上限 MIDI(既定 84 = C6)")
    ap.add_argument("--octave", type=int, help="オクターブを手動で動かす(自動配置をやめる。例: 1 / -1)")
    ap.add_argument("--min-note", type=float, default=0.1, help="これより短い音は捨てる(秒。既定 0.1)")
    ap.add_argument("--start-beat", type=float, default=0.0, help="最初の音を置く拍(既定 0)")
    ap.add_argument("--bars", type=int, help="ループの小節数(省略: 最後の音を含む小節数)")
    ap.add_argument("--no-kick", action="store_true", help="録音のキー(.json)があっても使わない(除去も拍合わせもしない)")
    ap.add_argument("--kick-hp", type=float, default=130.0, help="キー除去のハイパス周波数 Hz(既定 130)")
    ap.add_argument("--no-tune-fix", action="store_true", help="全体の音程ずれ(チューニング)を補正しない")
    ap.add_argument("--name", help="コード中の変数名・live_loop 名(既定 audio_melody)")
    ap.add_argument("-o", "--output", help="出力 .rb(既定: work/proposals/<名前>_melody.rb)")
    ap.add_argument("--force", action="store_true", help="既存の出力を上書きする")
    ap.add_argument("--list-scales", action="store_true", help="使える音階を表示して終了")
    a = ap.parse_args()

    if a.list_scales:
        print("\n".join(SCALES))
        return
    if not a.audio or not a.key:
        ap.error("audio と --key が必要です")
    try:
        key = parse_key(a.key)
    except ValueError as e:
        sys.exit(f"[エラー] {e}")
    src = Path(a.audio).expanduser()
    if not src.is_file():
        src = next((p for p in (WORK / a.audio, WORK / "recordings" / a.audio) if p.is_file()), src)
    if not src.is_file():
        sys.exit(f"[エラー] ファイルがありません: {a.audio}")
    meta = None  # record_mic.py --bpm が横に置く <名>.json(キーの BPM と頭出しの拍数)
    side = src.with_suffix(".json")
    if side.is_file() and not a.no_kick:
        try:
            meta = json.loads(side.read_text(encoding="utf-8"))
            float(meta["bpm"]), float(meta["count_in_beats"])
        except (ValueError, KeyError, TypeError):
            sys.exit(f"[エラー] {side} を読めません(record_mic.py --bpm が作る形式)")
    bpm = a.bpm or (float(meta["bpm"]) if meta else None) or read_bpm()
    if not bpm:
        sys.exit("[エラー] --bpm を指定してください(work/current.rb に use_bpm もありません)")
    if meta and abs(bpm - float(meta["bpm"])) > 0.01:
        sys.exit(f"[エラー] --bpm {fmt(bpm)} が録音時の BPM {fmt(float(meta['bpm']))} と違います。拍合わせが崩れます")
    label = a.name or "audio_melody"
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", label):
        sys.exit("[エラー] --name は小文字・数字・_ だけ")
    out = Path(a.output).expanduser() if a.output else WORK / "proposals" / f"{src.stem}_melody.rb"
    if out.exists() and not a.force:
        sys.exit(f"[エラー] 既に存在します(上書きは --force): {out}")

    x = decode(src)
    t0: float | None = None
    fmin = FMIN
    if meta:
        grid_found = find_kick_grid(x, bpm)
        if grid_found and grid_found[1] >= 3.0:
            t0 = grid_found[0] + float(meta["count_in_beats"]) * 60.0 / bpm
            x = highpass(x, a.kick_hp)
            fmin = 100.0  # キックの低音(~60Hz)を音程と取り違えないよう下限を上げる
            print(f"キー: 最初の拍 {grid_found[0]:.2f} 秒 / 確かさ {grid_found[1]:.1f} → {a.kick_hp:.0f}Hz 以下を削り、拍 {fmt(float(meta['count_in_beats']))} から数える", file=sys.stderr)
        else:
            print("[警告] 録音にキックが見つかりません(イヤホンだと入らない / 音が小さい)。最初の音を拍 0 にして続けます", file=sys.stderr)
    f0, rms = yin_track(x, fmin=fmin)
    notes, info = extract_notes(f0, rms, key, a.min_note, tune=not a.no_tune_fix)
    if not notes:
        sys.exit("[エラー] 音程のある音が見つかりません(小さすぎる・雑音が多い・短すぎる)。静かな場所で、はっきり「ら〜」と発声して録り直してください")
    beats = to_beats(notes, bpm, a.grid, a.start_beat, t0)
    if not beats:
        sys.exit("[エラー] カウントのあとに歌った音がありません(キックの拍 0 より前の音は捨てます)")
    shift = place_octave(beats, a.low, a.high, a.octave)
    end = max(p + ln for p, _, ln in beats)
    loop_beats = 4 * (a.bars or max(1, math.ceil(end / 4 - 1e-9)))
    code = render_ruby(beats, shift, key, bpm, src.name, label, loop_beats)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(code, encoding="utf-8")

    pitches = [m + shift for _, m, _ in beats]
    print(f"録音: {len(x) / SR:.1f} 秒 / 音程あり {info['voiced'] / max(info['frames'], 1) * 100:.0f}% のフレーム", file=sys.stderr)
    print(f"チューニングのずれ: {info['tune_cents']:+.0f} セント" + ("(補正済み)" if not a.no_tune_fix else "(補正なし)"), file=sys.stderr)
    print(f"もともとキー内だったフレーム: {info['in_key'] * 100:.0f}%(低いほど、寄せた量が多い)", file=sys.stderr)
    print(f"音符: {len(beats)} 個 / 音域 {note_name(min(pitches), key.use_flats)}〜{note_name(max(pitches), key.use_flats)}(オクターブ {shift // 12:+d})", file=sys.stderr)
    print(f"ループ: {loop_beats} 拍({loop_beats // 4} 小節)/ キー {key.label()} / BPM {fmt(bpm)}", file=sys.stderr)
    print(f"出力: {out}", file=sys.stderr)
    print(f"確認: uv run scripts/live_check.py {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
