#!/usr/bin/env python3
"""spec を「決定済み(ready)」にして decisions に記録する。生成の入力にしてよい状態にする操作。

使い方: decide.py <song> <spec-key> [--reason 理由]
依存元がすべて ready でなければ失敗する。承認ゲートではなく、spec が埋まったことの記録。
"""

from __future__ import annotations

import argparse
from datetime import date

from common import READY, deps_of, load_specs, read_spec, require_project, write_spec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("spec")
    ap.add_argument("--reason", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    proj = require_project(a.song)
    path = proj / "spec" / f"{a.spec}.md"
    if not path.exists():
        raise SystemExit(f"spec がありません: {path.name}")
    meta, body = read_spec(path)
    specs = load_specs(a.song)
    missing = [d for d in deps_of(specs, a.spec) if specs.get(d, ({}, ""))[0].get("status") != READY]
    if missing:
        raise SystemExit(f"依存元が ready でないため決定できません: {', '.join(missing)}")
    meta["status"] = READY
    meta.setdefault("decisions", []).append(
        {"date": date.today().isoformat(), "version": meta.get("version", 1), "note": a.reason or "決定"}
    )
    print(f"{a.spec} を ready にします(version {meta.get('version', 1)})")
    if not a.dry_run:
        write_spec(path, meta, body)


if __name__ == "__main__":
    main()
