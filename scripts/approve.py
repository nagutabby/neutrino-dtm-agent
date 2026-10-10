#!/usr/bin/env python3
"""ユーザーの承認を spec に記録する。ユーザーが承認すると発言した後にのみ実行すること。

spec 承認:   approve.py <song> <spec-key> [--reason 理由]
トラック承認: approve.py <song> <spec-key> --track-version N
  (承認済みトラックは projects/<song>/approved.json に spec の version とともに記録。
   approved.json は spec から導出できる派生物。手で編集しない)
"""

from __future__ import annotations

import argparse
import json
from datetime import date

from common import SPECS, load_specs, read_spec, require_project, write_spec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("spec", choices=list(SPECS))
    ap.add_argument("--reason", default="")
    ap.add_argument("--track-version", type=int)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    proj = require_project(a.song)
    path = proj / "spec" / f"{a.spec}.md"
    meta, body = read_spec(path)

    if a.track_version is None:
        specs = load_specs(a.song)
        missing = [d for d in SPECS[a.spec][1] if specs.get(d, ({}, ""))[0].get("status") != "approved"]
        if missing:
            raise SystemExit(f"依存元が未承認のため承認できません: {', '.join(missing)}")
        meta["status"] = "approved"
        meta.setdefault("decisions", []).append(
            {"date": date.today().isoformat(), "version": meta.get("version", 1), "note": a.reason or "承認"}
        )
        print(f"{a.spec} を approved にします(version {meta.get('version', 1)})")
        if not a.dry_run:
            write_spec(path, meta, body)
        return

    track = SPECS[a.spec][2]
    if not track:
        raise SystemExit(f"{a.spec} はトラックを持たない要素です")
    if meta.get("status") != "approved":
        raise SystemExit("spec が approved ではありません。先に spec を承認してください")
    f = proj / "approved.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    data[track] = {"track_version": a.track_version, "spec": a.spec, "spec_version": meta.get("version", 1)}
    print(f"トラック {track} v{a.track_version} を承認として記録(spec v{meta.get('version', 1)})")
    if not a.dry_run:
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
