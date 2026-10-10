#!/usr/bin/env python3
"""参考曲の音声を 4 パート(drums / bass / other / vocals)に分離する(Demucs htdemucs)。

使い方: reference_separate.py <song> <video-id> [--dry-run]
  projects/<song>/reference/<id>/audio.wav → stems/{drums,bass,other,vocals}.wav
MIDI 書き起こしの前段。混ざった音のままより、パートごとの方が書き起こし・コード推定が安定する。
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

PARTS = ("drums", "bass", "other", "vocals")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("ref_id")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ref = safe_ref_dir(require_project(a.song), a.ref_id)
    audio, out = ref / "audio.wav", ref / "stems"
    if not audio.exists():
        sys.exit(f"音声がありません: {audio}(reference_fetch.sh で取得)")
    if out.exists() and any(out.glob("*.wav")):
        sys.exit(f"既に存在します(上書きしません): {out}")
    print(f"音源分離: {audio.name} → stems/{{{','.join(PARTS)}}}.wav(数分かかります)")
    if a.dry_run:
        return
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [sys.executable, "-m", "demucs", "-n", "htdemucs", "-o", tmp, str(audio)]
        r = subprocess.run(cmd, check=False)
        if r.returncode != 0:
            sys.exit("Demucs の実行に失敗しました。`uv run --group reference` で実行しているか確認してください")
        src = Path(tmp) / "htdemucs" / audio.stem
        missing = [p for p in PARTS if not (src / f"{p}.wav").exists()]
        if missing:
            sys.exit(f"分離結果が不足しています: {', '.join(missing)}")
        out.mkdir(exist_ok=True)
        for p in PARTS:
            shutil.move(str(src / f"{p}.wav"), out / f"{p}.wav")
    print(f"保存: {out}")


if __name__ == "__main__":
    main()
