#!/usr/bin/env python3
"""spec と生成物の整合性を検査する(日本語で結果表示)。

検査: frontmatter / 依存関係の充足 / stale(spec が生成物より新しい) /
      未承認 spec のトラック / MIDI が spec のテンポ・拍子・小節数・音域に合っているか。
終了コード: 0=エラーなし / 1=エラーあり
"""

from __future__ import annotations

import argparse
import sys

import midi_tools
from common import (
    SPECS,
    STATUSES,
    load_specs,
    midi_to_note,
    note_to_midi,
    require_project,
    sidecar,
    track_files,
    version_of,
)


def check(song: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    require_project(song)
    specs = load_specs(song)

    for key, (_, deps, _) in SPECS.items():
        if key not in specs:
            warns.append(f"{key}.md がありません(new_song.sh で雛形を展開できます)")
            continue
        meta = specs[key][0]
        if meta.get("status") not in STATUSES:
            errors.append(f"{key}: status は {'/'.join(STATUSES)} のいずれかにしてください(現在: {meta.get('status')!r})")
        if not isinstance(meta.get("version"), int):
            errors.append(f"{key}: version は整数にしてください")
        declared = meta.get("depends_on", [])
        if sorted(declared) != sorted(deps):
            warns.append(f"{key}: depends_on {declared} が標準の依存 {deps} と異なります")
        if meta.get("status") == "approved":
            not_ok = [d for d in deps if specs.get(d, ({}, ""))[0].get("status") != "approved"]
            if not_ok:
                errors.append(f"{key} は approved ですが、依存元が未承認です: {', '.join(not_ok)}")

    struct = specs.get("01-structure", ({}, ""))[0].get("params", {}) or {}
    for key, (_label, _deps, track) in SPECS.items():
        if not track:
            continue
        files = track_files(song, track)
        if not files:
            continue
        latest = files[-1]
        meta = specs.get(key, ({}, ""))[0]
        if meta.get("status") != "approved":
            errors.append(f"{latest.name}: 対応する spec {key} が approved ではありません(spec が先です)")
        side = sidecar(latest)
        if not side:
            warns.append(f"{latest.name}: spec_version の記録(.json)がありません。register_track.py で登録してください")
        else:
            for k, v in side.get("spec_versions", {}).items():
                cur = specs.get(k, ({}, ""))[0].get("version")
                if cur != v:
                    warns.append(f"[stale] {latest.name}: {k} が v{v} → v{cur} に変わっています。再生成が必要です")
        if track == "vocal":
            continue
        try:
            m = midi_tools.load(latest)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{latest.name}: MIDI を読めません: {e}")
            continue
        if "tempo" in struct and abs(m.bpm - float(struct["tempo"])) > 0.5:
            errors.append(f"{latest.name}: テンポ {m.bpm} が spec の {struct['tempo']} と違います")
        if "time_signature" in struct:
            n, d = (int(x) for x in str(struct["time_signature"]).split("/"))
            if m.time_sig != (n, d):
                errors.append(f"{latest.name}: 拍子 {m.time_sig[0]}/{m.time_sig[1]} が spec の {n}/{d} と違います")
        if "bars" in struct and m.notes and m.bars != int(struct["bars"]):
            warns.append(f"{latest.name}: 小節数 {m.bars} が spec の {struct['bars']} と違います")
        rng = (meta.get("params", {}) or {}).get("range")
        if rng and m.notes:
            lo, hi = note_to_midi(rng[0]), note_to_midi(rng[1])
            out = [n for n in m.notes if not lo <= n.pitch <= hi]
            if out:
                warns.append(
                    f"{latest.name}: spec の音域 {rng[0]}〜{rng[1]} の外に {len(out)} 音あります"
                    f"(例: {midi_to_note(out[0].pitch)})"
                )
    return errors, warns


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("song")
    a = ap.parse_args()
    errors, warns = check(a.song)
    for e in errors:
        print(f"[エラー] {e}")
    for w in warns:
        print(f"[警告] {w}")
    if not errors and not warns:
        print("spec と生成物は整合しています。")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    _ = version_of  # re-export for tests
    main()
