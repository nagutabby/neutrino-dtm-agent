#!/usr/bin/env python3
"""参考曲の音声を MIDI に書き起こす(Basic Pitch / ONNX)。分析の素材であり、複製用ではない。

使い方: reference_to_midi.py <song> <video-id> [--dry-run]
  stems/ があれば bass / other / vocals を個別に書き起こす → transcription_<part>.mid
  (drums は音程が無いので書き起こさない)。無ければ audio.wav 全体 → transcription.mid
複数楽器が混ざった音声の書き起こしは不完全(音の抜け・余計な音が出る)。
大まかな音域・密度・リズムの傾向を見るために使う。
"""

from __future__ import annotations

import argparse
import sys

from common import require_project, safe_ref_dir


def _rms(path) -> float:
    import soundfile as sf

    data, _ = sf.read(str(path), always_2d=True)
    return float((data**2).mean() ** 0.5) if data.size else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("ref_id")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ref = safe_ref_dir(require_project(a.song), a.ref_id)
    stems = ref / "stems"
    if stems.is_dir() and any(stems.glob("*.wav")):
        jobs = [(stems / f"{p}.wav", ref / f"transcription_{p}.mid") for p in ("bass", "other", "vocals")]
        jobs = [(i, o) for i, o in jobs if i.exists()]
        # ほぼ無音のパート(例: 歌なし曲の vocals)は他楽器の混ざり込みで偽の音が出るので書き起こさない
        quiet = [i.stem for i, _ in jobs if _rms(i) < 0.15 * _rms(stems / "other.wav")]
        for q in quiet:
            print(f"スキップ: {q}(ほぼ無音のため書き起こしません)")
        jobs = [(i, o) for i, o in jobs if i.stem not in quiet]
    else:
        jobs = [(ref / "audio.wav", ref / "transcription.mid")]
    for audio, _ in jobs:
        if not audio.exists():
            sys.exit(f"音声がありません: {audio}(reference_fetch.sh で取得)")
    for _, out in jobs:
        if out.exists():
            sys.exit(f"既に存在します(上書きしません): {out}")
    for audio, out in jobs:
        print(f"書き起こし: {audio.relative_to(ref)} → {out.name}")
    if a.dry_run:
        return
    try:
        from basic_pitch.inference import predict
    except ImportError:
        sys.exit("basic-pitch がありません。`uv run --group reference ...` で実行してください")
    for audio, out in jobs:
        _, midi, _ = predict(str(audio))
        midi.write(str(out))
        print(f"保存: {out}")


if __name__ == "__main__":
    main()
