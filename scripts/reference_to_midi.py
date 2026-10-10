#!/usr/bin/env python3
"""参考曲の音声を MIDI に書き起こす(MuScriptor、多楽器対応の専用モデル)。分析の素材であり、複製用ではない。

使い方: reference_to_midi.py <song> <video-id> [--model small|medium|large] [--dry-run]
  projects/<song>/reference/<id>/audio.wav(ミックス全体)→ transcription.mid(楽器ごとのトラック+ドラム)

事前準備(初回のみ。認証はユーザー自身が実行する):
  1. Hugging Face で https://huggingface.co/MuScriptor/muscriptor-medium のライセンス(CC BY-NC 4.0)に同意
  2. uvx hf auth login
`uvx` で版を固定して実行するため、プロジェクトの Python 環境とは分離される。初回は重みを取得する。
CPU では曲の長さの 0.6〜3 倍かかる(medium。実測: 42秒の曲で約2分、191秒の曲で約110秒)。書き起こしは完全ではない。傾向を見る目安として使う。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

from common import require_project, safe_ref_dir

MUSCRIPTOR = "muscriptor==0.3.0"  # 再現性のため版を固定(更新は動作確認のうえ)


def build_cmd(audio, out, model: str) -> list[str]:
    return [
        "uvx",
        "--from",
        MUSCRIPTOR,
        "muscriptor",
        "transcribe",
        str(audio),
        "-o",
        str(out),
        "--model",
        model,
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("ref_id")
    ap.add_argument("--model", choices=["small", "medium", "large"], default="medium")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ref = safe_ref_dir(require_project(a.song), a.ref_id)
    audio, out = ref / "audio.wav", ref / "transcription.mid"
    if not audio.exists():
        sys.exit(f"音声がありません: {audio}(reference_fetch.sh で取得)")
    if out.exists():
        sys.exit(f"既に存在します(上書きしません): {out}")
    cmd = build_cmd(audio, out, a.model)
    print(f"書き起こし({a.model}): {audio.name} → {out.name}")
    if a.dry_run:
        print("[dry-run] " + " ".join(cmd))
        return
    if shutil.which("uvx") is None:
        sys.exit("uvx がありません(brew install uv)")
    r = subprocess.run(cmd, check=False)
    if r.returncode != 0 or not out.exists():
        sys.exit(
            "MuScriptor の実行に失敗しました。認証エラーの場合は、ご自身で次を実行してください:\n"
            "  1) https://huggingface.co/MuScriptor/muscriptor-medium でライセンスに同意\n"
            "  2) uvx hf auth login"
        )
    print(f"保存: {out}")


if __name__ == "__main__":
    main()
