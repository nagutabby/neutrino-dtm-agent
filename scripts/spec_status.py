#!/usr/bin/env python3
"""spec の状態を一覧表示し、「次に決めること」を示す。"""

from __future__ import annotations

import argparse

from common import SPECS, deps_of, load_specs


def next_candidates(specs: dict) -> list[str]:
    out = []
    for key in SPECS:
        deps = deps_of(specs, key)
        st = specs.get(key, ({"status": "draft"}, ""))[0].get("status", "draft")
        if st == "approved":
            continue
        if all(specs.get(d, ({}, ""))[0].get("status") == "approved" for d in deps):
            out.append(key)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("song")
    args = ap.parse_args()
    specs = load_specs(args.song)
    print(f"■ {args.song} の spec 状態")
    for key, (label, _deps, _) in SPECS.items():
        meta = specs.get(key, ({}, ""))[0]
        st = meta.get("status", "(ファイルなし)")
        mark = {"approved": "✔", "needs-revision": "↻"}.get(st, "・")
        print(f" {mark} {key:<13} {label:<20} status={st:<15} v{meta.get('version', '-')}")
    cand = next_candidates(specs)
    print()
    if cand:
        names = "、".join(f"{k}({SPECS[k][0]})" for k in cand)
        print(f"次に決められる要素: {names}")
    else:
        print("すべての spec が承認済みです。最終ミックスと notes.md の振り返りへ。")


if __name__ == "__main__":
    main()
