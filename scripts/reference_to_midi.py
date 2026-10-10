#!/usr/bin/env python3
"""参考曲の音声を MIDI に書き起こす(Basic Pitch / ONNX)。分析の素材であり、複製用ではない。

使い方: reference_to_midi.py <song> <video-id> [--dry-run]
  projects/<song>/reference/<id>/audio.wav → transcription.mid
複数楽器が混ざった音声の書き起こしは不完全(音の抜け・余計な音が出る)。
大まかな音域・密度・リズムの傾向を見るために使う。
"""

from __future__ import annotations

import argparse
import sys

from common import require_project, safe_ref_dir


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("ref_id")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ref = safe_ref_dir(require_project(a.song), a.ref_id)
    audio, out = ref / "audio.wav", ref / "transcription.mid"
    if not audio.exists():
        sys.exit(f"音声がありません: {audio}(reference_fetch.sh で取得)")
    if out.exists():
        sys.exit(f"既に存在します(上書きしません): {out}")
    print(f"書き起こし: {audio.name} → {out.name}")
    if a.dry_run:
        return
    try:
        from basic_pitch.inference import predict
    except ImportError:
        sys.exit("basic-pitch がありません。`uv run --group reference ...` で実行してください")
    _, midi, _ = predict(str(audio))
    midi.write(str(out))
    print(f"保存: {out}")


if __name__ == "__main__":
    main()
