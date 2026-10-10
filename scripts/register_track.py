#!/usr/bin/env python3
"""生成した MIDI を projects/<song>/tracks/ に次の版番号で登録し、元になった spec の版を記録する。

使い方: register_track.py <song> <spec-key> <midi>
  例:   register_track.py demo 04-bass /tmp/bass.mid
  → tracks/04_bass_v1.mid と 04_bass_v1.json(spec_versions を記録)
approved でない spec のトラックは登録できない(スペック駆動)。
"""

from __future__ import annotations

import argparse
import json
import shutil

from common import SPECS, load_specs, require_project, track_files, version_of


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("spec", choices=[k for k, v in SPECS.items() if v[2]])
    ap.add_argument("midi")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    proj = require_project(a.song)
    specs = load_specs(a.song)
    track = SPECS[a.spec][2]
    needed = [a.spec, *SPECS[a.spec][1]]
    bad = [k for k in needed if specs.get(k, ({}, ""))[0].get("status") != "approved"]
    if bad:
        raise SystemExit(f"approved でない spec があるため登録できません: {', '.join(bad)}")

    nxt = max((version_of(p) for p in track_files(a.song, track)), default=0) + 1
    num = a.spec.split("-")[0]
    dest = proj / "tracks" / f"{num}_{track}_v{nxt}.mid"
    meta = {"spec": a.spec, "spec_versions": {k: specs[k][0].get("version", 1) for k in needed}}
    print(f"登録: {dest.relative_to(proj.parent.parent)}  spec_versions={meta['spec_versions']}")
    if a.dry_run:
        return
    dest.parent.mkdir(exist_ok=True)
    shutil.copyfile(a.midi, dest)
    dest.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
