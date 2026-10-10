#!/usr/bin/env python3
"""ライブコーディングのコード(Sonic Pi)を実時間で録音して wav にする。

  live_render.py <song> <file.rb> [<file.rb> ...] --seconds N [--name NAME] [--dry-run]

ファイルは曲のディレクトリからの相対パス(例: current.rb proposals/02_bass.rb)か projects/ 配下のパス。
複数渡すと順に連結して1本のコードとして鳴らす(現在のコード + 次のステムの案、など)。
live_loop は並列に走り、最後に `sleep N` で N 秒鳴らしてから止める。録音中はスピーカーから音が鳴る。
出力は projects/<song>/renders/<NAME>_vN.wav(16bit/48kHz)。既存ファイルは上書きせず版を進める。
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import sonicpi
from common import require_project


def resolve(proj: Path, f: str) -> Path:
    for base in (proj, proj.parent.parent):
        p = (base / f).resolve()
        if p.is_file():
            if proj.resolve() not in p.parents:
                sys.exit(f"[エラー] 曲のディレクトリ外のファイルは使えません: {f}")
            return p
    sys.exit(f"[エラー] ファイルがありません: {f}(曲のディレクトリ内で指定)")


def next_version(d: Path, name: str) -> int:
    vs = [int(m.group(1)) for f in d.glob(f"{name}_v*.wav") if (m := re.fullmatch(rf"{re.escape(name)}_v(\d+)\.wav", f.name))]
    return max(vs, default=0) + 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--seconds", type=float, required=True, help="鳴らす秒数(目安: 4小節 = 16拍 × 60/BPM 秒)")
    ap.add_argument("--name", help="出力名(既定: 最初のファイル名)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not 1 <= a.seconds <= 600:
        sys.exit("[エラー] --seconds は 1〜600")
    proj = require_project(a.song)
    srcs = [resolve(proj, f) for f in a.files]
    name = a.name or srcs[0].stem
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        sys.exit("[エラー] --name は英数字・_・- のみ")
    out_dir = proj / "renders"
    out = out_dir / f"{name}_v{next_version(out_dir, name)}.wav"
    code = "\n\n".join(s.read_text(encoding="utf-8") for s in srcs) + f"\n\nuse_bpm 60 # ユーザーの use_bpm に関係なく、次の sleep を秒数どおりにする\nsleep {a.seconds}\n"
    if a.dry_run:
        print(f"[dry-run] {', '.join(s.name for s in srcs)} を {a.seconds} 秒録音 -> {out.relative_to(proj.parent.parent)}")
        return
    print(f"録音中({a.seconds:.0f} 秒 + 起動・保存。音が鳴ります)…", flush=True)
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "raw.wav"
        sonicpi.record(code, a.seconds, raw)
        out_dir.mkdir(parents=True, exist_ok=True)
        if not shutil.which("ffmpeg"):
            sys.exit("[エラー] ffmpeg がありません(brew install ffmpeg)")
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-ar", "48000", "-c:a", "pcm_s16le", str(out)])
        if r.returncode != 0:
            sys.exit("[エラー] ffmpeg での変換に失敗しました")
    print(f"できました: {out.relative_to(proj.parent.parent)}")
    print(f"聴く: ! scripts/play.sh {out.relative_to(proj.parent.parent)}")


if __name__ == "__main__":
    main()
