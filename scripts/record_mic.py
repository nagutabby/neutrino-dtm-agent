#!/usr/bin/env python3
"""マイクをキー入力で録音して mp3 にする(ffmpeg + avfoundation。macOS)。

  record_mic.py [-o out.mp3] [--device 0] [--list-devices] [--bitrate 192k] [--force]
                [--bpm N [--count-in 1] [--max-bars 32] [--count-only]]

Enter で録音開始 → もう一度 Enter で停止。出力の既定は work/recordings/rec_vN.mp3(版を進める)。
初回は、ターミナルにマイクの許可が要る(システム設定 → プライバシーとセキュリティ → マイク)。
--bpm を付けると、スピーカーからキック(低音のドン)を拍ごとに鳴らす。最初の --count-in 小節ぶんは数えるだけ
(4拍 × 小節数)で、その次の拍から歌う。キックは録音に入り、あとで melody_from_audio.py が
拍の位置を求めて低音を削る(横の <名>.json に BPM と数える拍数を残す)。--count-only なら数えのキックだけで止まる(叩くリズムを録るとき用)。イヤホンだとキックが入らず、拍合わせはできない。
ハミング・口笛・単音の楽器向け(メロディの取り出しは melody_from_audio.py)。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

import numpy as np
from common import require_work


def list_devices() -> None:
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
        capture_output=True,
        text=True,
    )
    out = r.stderr.splitlines()
    on = False
    for line in out:
        if "AVFoundation audio devices" in line:
            on = True
            continue
        if on and "]" in line:
            print(line.split("] ", 1)[-1] if line.count("]") > 1 else line)


def kick_track(bpm: float, bars: int, sr: int = 48000) -> np.ndarray:
    """4/4 で毎拍キック(約110→45Hz に下がる正弦波、約0.3秒)が鳴る音。先頭が1拍目。"""
    beat = int(round(60.0 / bpm * sr))
    t = np.arange(int(0.3 * sr)) / sr
    phase = 2 * np.pi * (45 * t + 65 * 0.03 * (1 - np.exp(-t / 0.03)))
    env = np.minimum(1.0, t / 0.003) * np.exp(-t / 0.1)
    kick = 0.9 * np.sin(phase) * env
    out = np.zeros(beat * 4 * bars + len(kick))
    for b in range(4 * bars):
        out[b * beat : b * beat + len(kick)] += kick
    return out


def write_wav(path: Path, x: np.ndarray, sr: int = 48000) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32000).astype("<i2").tobytes())


def next_path(d: Path) -> Path:
    vs = [int(m.group(1)) for f in d.glob("rec_v*.mp3") if (m := re.fullmatch(r"rec_v(\d+)\.mp3", f.name))]
    return d / f"rec_v{max(vs, default=0) + 1}.mp3"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("-o", "--output", help="出力 mp3(既定: work/recordings/rec_vN.mp3)")
    ap.add_argument("--device", default="0", help="音声入力デバイスの番号(既定 0。--list-devices で確認)")
    ap.add_argument("--list-devices", action="store_true", help="音声入力デバイスを表示して終了")
    ap.add_argument("--bitrate", default="192k", help="mp3 のビットレート(既定 192k)")
    ap.add_argument("--bpm", type=float, help="キックで拍を鳴らす(録音に入り、あとで除去・拍合わせに使う)")
    ap.add_argument("--count-in", type=int, default=1, help="歌う前に数える小節数(既定 1 = 4拍)")
    ap.add_argument("--count-only", action="store_true", help="数えのキックだけ鳴らして止める(叩いたリズムを録るとき。キックが録音に混ざらない)")
    ap.add_argument("--max-bars", type=int, default=32, help="キックを鳴らす最大の小節数(既定 32)")
    ap.add_argument("--force", action="store_true", help="既存の出力を上書きする")
    a = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("[エラー] ffmpeg がありません(brew install ffmpeg)")
    if a.list_devices:
        list_devices()
        return

    if a.output:
        dst = Path(a.output).expanduser()
    else:
        d = require_work() / "recordings"
        d.mkdir(exist_ok=True)
        dst = next_path(d)
    if dst.exists() and not a.force:
        sys.exit(f"[エラー] 既に存在します(上書きは --force): {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)

    kick_proc = None
    if a.bpm:
        if not shutil.which("afplay"):
            sys.exit("[エラー] afplay がありません(macOS のみ)")
        if not 30 <= a.bpm <= 300 or a.count_in < 1 or (not a.count_only and a.max_bars < a.count_in + 1):
            sys.exit("[エラー] --bpm は 30〜300、--count-in は 1 以上、--max-bars は --count-in より大きく")
        kick_wav = Path(tempfile.mkdtemp()) / "kick.wav"
        write_wav(kick_wav, kick_track(a.bpm, a.count_in if a.count_only else a.max_bars))
    print(f"出力: {dst}\nEnter で録音開始(Sonic Pi を鳴らすなら、音が入らないようイヤホンで)。Ctrl+C で中止")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        sys.exit("\n中止しました")

    log = tempfile.TemporaryFile()
    p = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "avfoundation", "-i", f":{a.device}",
         "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", a.bitrate, str(dst)],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=log,
    )
    time.sleep(0.8)  # 起動に失敗したか(マイク未許可・デバイス違い)を確かめる
    if p.poll() is not None:
        log.seek(0)
        sys.exit(f"[エラー] 録音を始められません(マイクの許可・--device を確認):\n{log.read().decode(errors='replace')}")

    t0 = time.monotonic()
    if a.bpm:
        kick_proc = subprocess.Popen(["afplay", str(kick_wav)])
        print(f"♪ キック開始(BPM {a.bpm:g})。{a.count_in * 4} 拍数えて、次の拍から歌う")
    print("● 録音中... もう一度 Enter で停止")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass
    sec = time.monotonic() - t0
    if kick_proc:
        kick_proc.terminate()
    try:
        assert p.stdin
        p.stdin.write(b"q")  # ffmpeg に正常終了を頼む(mp3 の終端が書かれる)
        p.stdin.flush()
        p.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
        sys.exit("[エラー] ffmpeg が終了しませんでした")
    if not dst.is_file() or dst.stat().st_size == 0:
        sys.exit("[エラー] 録音ファイルができませんでした")
    print(f"■ 停止({sec:.1f} 秒) → {dst}({dst.stat().st_size / 1e3:.0f} KB)")
    if a.bpm:
        dst.with_suffix(".json").write_text(
            json.dumps({"bpm": a.bpm, "count_in_beats": a.count_in * 4}, ensure_ascii=False), encoding="utf-8"
        )
        print(f"次: uv run scripts/melody_from_audio.py {dst} --key \"F minor\"   (BPM・キックは {dst.with_suffix('.json').name} から)")
    else:
        print(f"次: uv run scripts/melody_from_audio.py {dst} --key \"F minor\" --bpm 100")


if __name__ == "__main__":
    main()
