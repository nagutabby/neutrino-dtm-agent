#!/usr/bin/env python3
"""参考曲の音声をパートに分離する(Demucs)。既定は 6 パート版 htdemucs_6s。

使い方: reference_separate.py <song> <video-id> [--model htdemucs_6s|htdemucs] [--dry-run]
  projects/<song>/reference/<id>/audio.wav → stems/{drums,bass,other,vocals,guitar,piano}.wav
  (--model htdemucs なら guitar / piano を含まない 4 パート。ピアノ・ギターは other に入る)
6 パート版は guitar / piano を分けられるが、開発元が実験的としており、特に piano は精度が低い。
混ざった音のままより、パートごとに分けた方がコード・キー・リズムの推定が安定する(MIDI への書き起こしはしない)。
初回はモデル(約 80MB)をダウンロードする。CPU で曲の長さの 0.5〜1 倍程度の時間がかかる。
分離した音声は私的な分析用で、コミット・公開しない。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from common import require_project, safe_ref_dir

MODELS = {
    "htdemucs_6s": ("drums", "bass", "other", "vocals", "guitar", "piano"),
    "htdemucs": ("drums", "bass", "other", "vocals"),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("ref_id")
    ap.add_argument("--model", choices=list(MODELS), default="htdemucs_6s")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ref = safe_ref_dir(require_project(a.song), a.ref_id)
    audio, out = ref / "audio.wav", ref / "stems"
    if not audio.exists():
        sys.exit(f"音声がありません: {audio}(reference_fetch.sh で取得)")
    if out.exists() and any(out.glob("*.wav")):
        sys.exit(f"既に存在します(上書きしません): {out}")
    parts = MODELS[a.model]
    print(f"音源分離({a.model}): {audio.name} → stems/{{{','.join(parts)}}}.wav(数十秒〜数分)")
    if a.dry_run:
        return
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [sys.executable, "-m", "demucs", "-n", a.model, "-o", tmp, str(audio)]
        r = subprocess.run(cmd, check=False)
        if r.returncode != 0:
            sys.exit(
                "Demucs の実行に失敗しました。`uv run --group reference` で実行しているか確認してください"
            )
        src = Path(tmp) / a.model / audio.stem
        missing = [p for p in parts if not (src / f"{p}.wav").exists()]
        if missing:
            sys.exit(f"分離結果が不足しています: {', '.join(missing)}")
        out.mkdir(exist_ok=True)
        for p in parts:
            shutil.move(str(src / f"{p}.wav"), out / f"{p}.wav")
    print(f"保存: {out}")


if __name__ == "__main__":
    main()
