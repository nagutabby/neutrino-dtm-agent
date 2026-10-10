#!/usr/bin/env python3
"""サウンドチェック: 曲のトラック計画にある全トラックの音色を、短い試奏フレーズで SuperCollider で合成する。

  patch_audition.py <song> [--dry-run] [--force]

出力: projects/<song>/audition/NN_<track>.wav(トラックごと1本。固定フレーズ=曲の中身ではない)
音楽制作(構成・和声・MIDI 生成)は、この全トラック分が揃い、ユーザーが音色を確認してから始める。
patch / patch_params を変えたトラックは --force で作り直す(既存は上書きしない)。
"""

from __future__ import annotations

import argparse
import sys

import patches
import synth_render as sr
from common import ROOT, active_keys, label_of, load_specs, require_project, track_of

# 試奏フレーズ(秒)。旋律系: 低音域は1音ずつ、それ以外はコード→単音。ドラム: キック/スネア/ハットの8分パターン
LOW = [(0.0, 0.9, 36), (1.0, 0.9, 43), (2.0, 0.9, 39), (3.0, 0.9, 36)]
CHORD = [(0.0, 1.8, n) for n in (60, 63, 67)] + [(2.0, 1.8, n) for n in (56, 60, 63)]
LINE = [(0.0, 0.4, 72), (0.5, 0.4, 75), (1.0, 0.4, 79), (1.5, 0.4, 75), (2.0, 1.0, 72)]
DRUMS = (
    [(i * 0.25, 0.1, 42) for i in range(16)]
    + [(0.0, 0.1, 36), (1.0, 0.1, 38), (2.0, 0.1, 36), (2.5, 0.1, 36), (3.0, 0.1, 38)]
    + [(3.5, 0.1, 56)]
)


def phrase(track: str, entry: dict) -> list[tuple[float, float, int]]:
    if entry["kind"] == "drums":
        return DRUMS
    if track in ("bass",):
        return LOW
    if track in ("chords", "pad", "piano"):
        return CHORD
    if track in ("fx",):
        return [(0.0, 3.0, 60)]
    return LINE


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="既存の試奏 wav を作り直す")
    a = ap.parse_args()
    proj = require_project(a.song)
    errs = patches.check(a.song)
    if errs:
        sys.exit("\n".join(f"[エラー] {e}" for e in errs) + "\n先に patch を直してください(patches.py check)")
    specs, reg = load_specs(a.song), patches.registry()
    out_dir = proj / "audition"
    made = []
    for key in active_keys(specs):
        trk = track_of(specs, key)
        if not trk or trk == "vocal":
            continue
        pid = patches.patch_id_of(specs, key)
        overrides = (specs[key][0].get("params") or {}).get("patch_params") or {}
        target = out_dir / f"{key.split('-')[0]}_{trk}.wav"
        if target.exists() and not a.force:
            print(f"- {target.name}: 既にあります(作り直すなら --force)")
            continue
        notes = [{"start": s, "end": s + d, "note": n, "vel": 100, "ch": 0} for s, d, n in phrase(trk, reg[pid])]
        voices = sr.build_voices(notes, reg[pid], overrides)
        print(f"■ {label_of(specs, key)}({trk}): パッチ {pid}")
        sr.synthesize(voices, sr.end_time(voices), target, a.dry_run)
        made.append(target)
    print("\n試聴コマンド:")
    for t in sorted(out_dir.glob("*.wav")) if out_dir.is_dir() else made:
        print(f"  ! scripts/play.sh {t.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
