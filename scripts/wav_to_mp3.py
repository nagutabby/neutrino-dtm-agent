#!/usr/bin/env python3
"""wav を mp3 に変換する(ffmpeg + libmp3lame)。

  wav_to_mp3.py <wav> [-o out.mp3] [--bitrate 256k] [--force]

出力の既定は入力と同じ場所の `<名>.mp3`。既存ファイルは --force がない限り上書きしない。
相対パスはカレントディレクトリ、なければ work/ 配下から探す。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from common import WORK


def resolve(p: str) -> Path:
    path = Path(p).expanduser()
    if path.is_file():
        return path
    if (WORK / p).is_file():
        return WORK / p
    sys.exit(f"[エラー] ファイルがありません: {p}")


def convert(src: Path, dst: Path, bitrate: str = "256k") -> None:
    if not shutil.which("ffmpeg"):
        sys.exit("[エラー] ffmpeg がありません(brew install ffmpeg)")
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-c:a", "libmp3lame", "-b:a", bitrate, str(dst)]
    )
    if r.returncode != 0:
        sys.exit("[エラー] ffmpeg での変換に失敗しました")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("wav")
    ap.add_argument("-o", "--output", help="出力 mp3(既定: 入力と同じ場所の .mp3)")
    ap.add_argument("--bitrate", default="256k", help="ビットレート(既定 256k)")
    ap.add_argument("--force", action="store_true", help="既存の出力を上書きする")
    a = ap.parse_args()

    src = resolve(a.wav)
    if src.suffix.lower() != ".wav":
        sys.exit(f"[エラー] wav ファイルを指定してください: {src}")
    dst = Path(a.output).expanduser() if a.output else src.with_suffix(".mp3")
    if dst.exists() and not a.force:
        sys.exit(f"[エラー] 既に存在します(上書きは --force): {dst}")
    convert(src, dst, a.bitrate)
    print(f"{dst}({dst.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
