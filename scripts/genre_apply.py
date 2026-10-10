#!/usr/bin/env python3
"""ジャンル定義(projects/<song>/genre/<id>.md。ジャンル別の定義は予め用意せず、曲ごとに調べて作る)と、
ユーザーが最初に指示した内容(projects/<song>/user_inputs.yaml)を曲に反映する。

  genre_apply.py <song> <genre-id> [--length-seconds N] [--run-mode step|auto] [--dry-run]
  genre_apply.py --list

やること:
  - 00-concept.params に genre / target_seconds / tracks(トラック計画と音色パッチ ID)を書く
  - トラックと音(patch)・コード進行は user_inputs.yaml のユーザー指定だけを使う。ジャンル定義の tracks は使わない(AI は補わない・候補を出さない)
  - user_inputs.yaml の progression を 02-harmony に、sections(セクション名と小節数)を 01-structure に書く
  - トラックごとのユーザー指示 usage(どう生成し、曲のどこでどう使うか)・sampling(サンプリングの技法)をトラック spec に書く
  - トラック spec を作る(無ければ docs/templates/track-spec.md から)。ユーザーが指定しなかった draft のトラック spec は削除する
  - 曲の長さをテンポ候補ごとの小節数に換算して表示する
  - 最後に音色パッチを検査し(patches.py。この曲の登録簿だけを見る)、登録簿にない/引数が不正なら終了コード 2
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date

import patches
import yaml
from common import (
    READY,
    ROOT,
    SPEC_KEY_RE,
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
    sys.exit(f"ジャンル定義がありません: {gid}(docs/genres/_template.md を元に、ジャンルを調べて projects/<song>/genre/ に作る)")


def bars_for(seconds: float, bpm: float, beats: int = 4) -> int:
    return round(seconds * bpm / 60 / beats)


def load_user_inputs(proj) -> dict:
    """projects/<song>/user_inputs.yaml(ユーザーが最初に指示した、トラックの音とコード進行)。不正は終了コード 2。"""
    f = proj / "user_inputs.yaml"
    if not f.is_file():
        sys.exit(f"[エラー] {f.name} がありません(ユーザーの最初の指示を書く。docs/templates/user_inputs.yaml)")
    data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    errs: list[str] = []
    tracks = data.get("tracks") or []
    if not tracks:
        errs.append("tracks が空です(作るトラックと音はユーザーが指示する。AI は候補を出さない)")
    seen: set[str] = set()
    for t in tracks:
        if not isinstance(t, dict) or not SPEC_KEY_RE.fullmatch(str(t.get("spec", ""))) or not re.fullmatch(r"[a-z0-9-]+", str(t.get("track", ""))):
            errs.append(f"トラックの書式が不正: {t}(spec: NN-name と track: 英小文字・数字・- が必要)")
            continue
        if t["track"] in seen:
            errs.append(f"track 名が重複: {t['track']}")
        seen.add(t["track"])
        if t["track"] != "vocal" and not t.get("usage"):
            print(f"[注意] {t['spec']}: usage がありません(どう生成し、曲のどこでどう使うかをユーザーに聞く)")
        if t["track"] != "vocal" and not t.get("patch"):
            errs.append(f"{t['spec']}: patch がありません(ユーザーが指示した音を synth/ にパッチとして作り、ID を書く)")
    for c in data.get("progression") or []:
        if not (isinstance(c, dict) and isinstance(c.get("bars"), int) and c["bars"] > 0 and isinstance(c.get("chord"), str)):
            errs.append(f"progression の書式が不正: {c}({{bars: 2, chord: Am}} の形)")
    for sec in data.get("sections") or []:
        if not (isinstance(sec, dict) and isinstance(sec.get("bars"), int) and sec["bars"] > 0 and isinstance(sec.get("name"), str)):
            errs.append(f"sections の書式が不正: {sec}({{name: サビ, bars: 8}} の形)")
    if errs:
        print("\n".join(f"[エラー] {e}" for e in errs))
        sys.exit(2)
    return data


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
    user = load_user_inputs(proj)
    tracks = user["tracks"]  # トラックと音はユーザー指定だけ(ジャンル定義の tracks は使わない)
    tempo = prof.get("tempo", {})
    lengths = prof.get("length_seconds", {})
    seconds = a.length_seconds or lengths.get("default")
    if seconds and lengths.get("range") and not lengths["range"][0] <= seconds <= lengths["range"][1]:
        print(f"[注意] 長さ {seconds:.0f} 秒は {prof.get('name')} の一般的な範囲 {lengths['range']} の外です(ユーザーの希望なら続行可)")

    spec_dir = proj / "spec"
    specs = load_specs(a.song)
    plan = [{"spec": t["spec"], "track": t["track"], **({"patch": t["patch"]} if t.get("patch") else {})}
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

    # 02-harmony: ユーザーが指定したコード進行(指定が無ければ触らない。AI は補わない)
    prog = user.get("progression") or []
    hpath = spec_dir / "02-harmony.md"
    if prog and hpath.exists():
        hmeta, hbody = read_spec(hpath)
        if hmeta.get("progression") != prog:
            if hmeta.get("status") == READY and hmeta.get("progression"):
                hmeta["status"] = "needs-revision"
                log.append("02-harmony: ユーザー指定の進行が ready の内容と違うため needs-revision に戻しました(下流の再生成が必要)")
            hmeta["progression"] = prog
            hmeta.setdefault("decisions", []).append(
                {"date": date.today().isoformat(), "version": hmeta.get("version", 1), "note": "コード進行はユーザー指定(user_inputs.yaml)"})
            log.append(f"02-harmony: progression={[c['chord'] for c in prog]}(ユーザー指定)")
            if not a.dry_run:
                write_spec(hpath, hmeta, hbody)

    # 01-structure: ユーザーが指定したセクション(指定が無ければ触らない。AI は補わない)
    secs = user.get("sections") or []
    spath = spec_dir / "01-structure.md"
    if secs and spath.exists():
        smeta, sbody = read_spec(spath)
        if smeta.get("sections") != secs:
            if smeta.get("status") == READY and smeta.get("sections"):
                smeta["status"] = "needs-revision"
                log.append("01-structure: ユーザー指定のセクションが ready の内容と違うため needs-revision に戻しました(下流の再生成が必要)")
            smeta["sections"] = secs
            smeta.setdefault("decisions", []).append(
                {"date": date.today().isoformat(), "version": smeta.get("version", 1), "note": "セクションはユーザー指定(user_inputs.yaml)"})
            log.append(f"01-structure: sections={[x['name'] for x in secs]}(ユーザー指定)")
            if not a.dry_run:
                write_spec(spath, smeta, sbody)

    # トラック spec の作成・更新
    for t in tracks:
        key, trk = t["spec"], t.get("track")
        path = spec_dir / f"{key}.md"
        if not trk:  # 歌詞など、トラックを持たない要素は雛形のまま残す
            if not path.exists():
                log.append(f"[警告] {key}.md がありません(new_song.sh の雛形から補ってください)")
            continue
        pt = t.get("patch")
        if path.exists():
            meta, body = read_spec(path)
            if trk == "vocal" or not pt:
                continue
            p = meta.setdefault("params", {})
            if t.get("sampling") and meta.get("sampling") != t["sampling"]:
                meta["sampling"] = t["sampling"]  # ユーザーの言葉(サンプリングの技法)
                log.append(f"{key}: sampling=ユーザー指示を記録")
                if not a.dry_run:
                    write_spec(path, meta, body)
            if t.get("usage") and meta.get("usage") != t["usage"]:
                meta["usage"] = t["usage"]  # ユーザーの言葉(どう生成し、どこでどう使うか)
                log.append(f"{key}: usage=ユーザー指示を記録")
                if not a.dry_run:
                    write_spec(path, meta, body)
            if t.get("sound") and meta.get("sound") != t["sound"]:
                meta["sound"] = t["sound"]  # ユーザーの言葉(音を作る根拠)
                log.append(f"{key}: sound=ユーザー指示を記録")
                if not a.dry_run:
                    write_spec(path, meta, body)
            if p.get("patch") != pt:
                changed = p.get("patch") is not None  # 以前に決めた音色を変える場合だけ見直し扱い
                p["patch"] = pt
                p.pop("patch_params", None)  # 別パッチの引数名は引き継がない
                if changed and meta.get("status") == READY:
                    meta["status"] = "needs-revision"
                    log.append(f"{key}: patch={pt} に変更。ready だったので needs-revision に戻しました(再生成が必要)")
                else:
                    log.append(f"{key}: patch={pt}")
                if not a.dry_run:
                    write_spec(path, meta, body)
        else:
            tmeta, tbody = read_spec(TEMPLATE)
            tmeta.update({"label": t.get("label", key), "track": trk})
            if t.get("sound"):
                tmeta["sound"] = t["sound"]  # ユーザーの言葉(音を作る根拠)
            if t.get("sampling"):
                tmeta["sampling"] = t["sampling"]  # ユーザーの言葉(サンプリングの技法)
            if t.get("usage"):
                tmeta["usage"] = t["usage"]  # ユーザーの言葉(どう生成し、どこでどう使うか)
            tmeta["params"]["patch"] = pt
            if trk == "vocal":
                tmeta["params"] = {}
            tmeta["decisions"] = [{"date": date.today().isoformat(), "version": 1, "note": f"ジャンル {prof['id']} のトラック計画から作成"}]
            log.append(f"{key}.md を新規作成(track={trk}, patch={tmeta['params'].get('patch', '-')})")
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
        need = sorted({t["patch"] for t in tracks if t.get("patch") and t.get("track") != "vocal"})
        print(f"(dry-run)使う音色パッチ: {', '.join(need) or 'なし'}。実行後に検査します")
        return
    sys.exit(patches.cmd_check(a.song))


if __name__ == "__main__":
    main()
