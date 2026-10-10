#!/usr/bin/env python3
"""ジャンル定義(docs/genres/<id>.md か projects/<song>/genre/<id>.md)を曲に反映する。

  genre_apply.py <song> <genre-id> [--length-seconds N] [--run-mode step|auto] [--dry-run]
  genre_apply.py --list

やること:
  - 00-concept.params に genre / target_seconds / tracks(トラック計画と SoundFont ID)を書く
  - ジャンルのトラック spec を作る(無ければ docs/templates/track-spec.md から)。使わない draft の
    トラック spec は削除する。各トラック spec の params.soundfont を設定する
  - 曲の長さをテンポ候補ごとの小節数に換算して表示する
  - 最後に SoundFont を確認し、足りなければ必要な内容を表示して終了コード 3(エージェントは中断する)
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date

import soundfont
from common import (
    READY,
    ROOT,
    VOCAL_ONLY,
    load_specs,
    read_spec,
    require_project,
    track_of,
    write_spec,
)

GENRES = ROOT / "docs" / "genres"
TEMPLATE = ROOT / "docs" / "templates" / "track-spec.md"


def profile_path(proj, gid: str):
    if not re.fullmatch(r"[a-z0-9-]+", gid):
        sys.exit(f"ジャンル ID は英小文字・数字・- のみ: {gid!r}")
    for p in (proj / "genre" / f"{gid}.md", GENRES / f"{gid}.md"):
        if p.is_file():
            return p
    sys.exit(f"ジャンル定義がありません: {gid}(docs/genres/_template.md を元に調べて作る)")


def bars_for(seconds: float, bpm: float, beats: int = 4) -> int:
    return round(seconds * bpm / 60 / beats)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song", nargs="?")
    ap.add_argument("genre", nargs="?")
    ap.add_argument("--length-seconds", type=float)
    ap.add_argument("--run-mode", choices=["step", "auto"])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.list:
        for p in sorted(GENRES.glob("*.md")):
            if not p.stem.startswith("_"):
                m, _ = read_spec(p)
                print(f" {m.get('id', p.stem):<8} {m.get('name', '')}  テンポ {m.get('tempo', {}).get('range')}")
        return
    if not a.song or not a.genre:
        ap.error("song と genre-id を指定してください(--list で一覧)")

    proj = require_project(a.song)
    prof, _ = read_spec(profile_path(proj, a.genre))
    tracks = [t for t in prof.get("tracks", []) if isinstance(t, dict) and t.get("spec")]
    tempo = prof.get("tempo", {})
    lengths = prof.get("length_seconds", {})
    seconds = a.length_seconds or lengths.get("default")
    if seconds and lengths.get("range") and not lengths["range"][0] <= seconds <= lengths["range"][1]:
        print(f"[注意] 長さ {seconds:.0f} 秒は {prof.get('name')} の一般的な範囲 {lengths['range']} の外です(ユーザーの希望なら続行可)")

    spec_dir = proj / "spec"
    specs = load_specs(a.song)
    plan = [{"spec": t["spec"], "track": t["track"], **({"soundfont": t["soundfont"]} if t.get("soundfont") else {})}
            for t in tracks if t.get("track")]
    keep = {t["spec"] for t in tracks}
    log: list[str] = []

    # 00-concept
    cpath = spec_dir / "00-concept.md"
    cmeta, cbody = read_spec(cpath)
    params = cmeta.setdefault("params", {})
    params.update({"genre": prof["id"], "target_seconds": seconds, "tracks": plan})
    if a.run_mode:
        cmeta["run_mode"] = a.run_mode
    cmeta.setdefault("decisions", []).append(
        {"date": date.today().isoformat(), "version": cmeta.get("version", 1),
         "note": f"ジャンル {prof['id']}・約{(seconds or 0):.0f}秒・トラック {len(plan)}本を反映"}
    )
    log.append(f"00-concept: genre={prof['id']} target_seconds={seconds} tracks={[t['track'] for t in plan]}")
    if not a.dry_run:
        write_spec(cpath, cmeta, cbody)

    # トラック spec の作成・更新
    for t in tracks:
        key, trk = t["spec"], t.get("track")
        path = spec_dir / f"{key}.md"
        if not trk:  # 歌詞など、トラックを持たない要素は雛形のまま残す
            if not path.exists():
                log.append(f"[警告] {key}.md がありません(new_song.sh の雛形から補ってください)")
            continue
        sf = t.get("soundfont")
        if path.exists():
            meta, body = read_spec(path)
            if trk == "vocal" or not sf:
                continue
            p = meta.setdefault("params", {})
            if p.get("soundfont") != sf:
                changed = p.get("soundfont") is not None  # 以前に決めた音源を変える場合だけ見直し扱い
                p["soundfont"] = sf
                if changed and meta.get("status") == READY:
                    meta["status"] = "needs-revision"
                    log.append(f"{key}: soundfont={sf} に変更。ready だったので needs-revision に戻しました(再生成が必要)")
                else:
                    log.append(f"{key}: soundfont={sf}")
                if not a.dry_run:
                    write_spec(path, meta, body)
        else:
            tmeta, tbody = read_spec(TEMPLATE)
            tmeta.update({"label": t.get("label", key), "track": trk})
            tmeta["params"]["soundfont"] = sf or "gm"
            if trk == "vocal":
                tmeta["params"] = {}
            tmeta["decisions"] = [{"date": date.today().isoformat(), "version": 1, "note": f"ジャンル {prof['id']} のトラック計画から作成"}]
            log.append(f"{key}.md を新規作成(track={trk}, soundfont={tmeta['params'].get('soundfont', '-')})")
            if not a.dry_run:
                write_spec(path, tmeta, f"# {t.get('label', key)}\n")

    # 使わないトラック spec の整理(draft のみ削除。ボーカル系は vocal フラグで制御するので触らない)
    for key in list(specs):
        if key in keep or key in VOCAL_ONLY or not track_of(specs, key):
            continue
        st = specs[key][0].get("status")
        if st == "draft":
            log.append(f"{key}.md を削除(このジャンルでは使わない draft)")
            if not a.dry_run:
                (spec_dir / f"{key}.md").unlink()
        else:
            log.append(f"[警告] {key} はこのジャンルのトラック計画にありませんが status={st} のため残しました")

    print(f"■ {prof['name']} を {a.song} に反映" + ("(dry-run)" if a.dry_run else ""))
    for line in log:
        print(f"  - {line}")
    if seconds:
        cands = [("下限", tempo.get("range", [None, None])[0]), ("既定", tempo.get("default")), ("上限", tempo.get("range", [None, None])[1])]
        print(f"■ 約{seconds:.0f}秒 を 4/4 の小節数にすると: " + " / ".join(
            f"{n} {bpm}BPM → {bars_for(seconds, bpm)}小節" for n, bpm in cands if bpm))
    if prof.get("sections"):
        total = sum(s.get("bars", 0) for s in prof["sections"])
        print(f"■ 標準構成(計{total}小節): " + " → ".join(f"{s['name']} {s['bars']}" for s in prof["sections"]) + "(曲の長さに合わせて伸縮)")
    print()
    if a.dry_run:
        need = sorted({t["soundfont"] for t in tracks if t.get("soundfont") and t.get("track") != "vocal"})
        print(f"(dry-run)必要な SoundFont ID: {', '.join(need) or 'なし'}。実行後に確認します")
        return
    sys.exit(soundfont.cmd_check(a.song))


if __name__ == "__main__":
    main()
