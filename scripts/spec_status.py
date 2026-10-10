#!/usr/bin/env python3
"""spec の状態を一覧表示し、「次に決めること」を示す。"""

from __future__ import annotations

import argparse

from common import READY, active_keys, deps_of, label_of, load_specs, vocal_enabled


def next_candidates(specs: dict) -> list[str]:
    out = []
    for key in active_keys(specs):
        deps = deps_of(specs, key)
        st = specs.get(key, ({"status": "draft"}, ""))[0].get("status", "draft")
        if st == READY:
            continue
        if all(specs.get(d, ({}, ""))[0].get("status") == READY for d in deps):
            out.append(key)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("song")
    args = ap.parse_args()
    specs = load_specs(args.song)
    concept = specs.get("00-concept", ({}, ""))[0]
    params = concept.get("params") or {}
    print(f"■ {args.song} の spec 状態" + ("" if vocal_enabled(specs) else "(インスト: 歌詞・ボーカルなし)"))
    print(f"  ジャンル={params.get('genre', '未設定')} / 長さ={params.get('target_seconds', '未設定')}秒 / 進め方={concept.get('run_mode', '未設定')}(step=1ステップごと確認 / auto=作り切る)")
    for key in active_keys(specs):
        label = label_of(specs, key)
        meta = specs.get(key, ({}, ""))[0]
        st = meta.get("status", "(ファイルなし)")
        mark = {READY: "✔", "needs-revision": "↻"}.get(st, "・")
        print(f" {mark} {key:<13} {label:<16} status={st:<15} v{meta.get('version', '-')}")
    cand = next_candidates(specs)
    print()
    if cand:
        names = "、".join(f"{k}({label_of(specs, k)})" for k in cand)
        print(f"次に決められる要素: {names}")
    else:
        print("すべての spec が決定済み(ready)です。最終ミックスと notes.md の振り返りへ。")


if __name__ == "__main__":
    main()
