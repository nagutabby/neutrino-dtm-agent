#!/usr/bin/env python3
"""シンセ音色(パッチ)の登録簿 config/patches.yaml の参照と検査。

  patches.py check <song>      曲のトラック spec が指す patch / patch_params が登録簿と合っているか検査(エラーは終了コード 2)
  patches.py list              登録簿の一覧
  patches.py show <id>         そのパッチの引数と既定値(spec の patch_params を決める根拠)

音は SuperCollider の SynthDef(synth/synthdefs.scd)でゼロから合成する。サンプルや SoundFont は使わない。
"""

from __future__ import annotations

import argparse
import re
import sys

import yaml
from common import ROOT, active_keys, load_specs, track_of

REGISTRY = ROOT / "config" / "patches.yaml"
SYNTHDEFS = ROOT / "synth" / "synthdefs.scd"


def _load() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}


def registry() -> dict[str, dict]:
    return _load().get("patches") or {}


def defaults() -> dict[str, str]:
    return _load().get("defaults") or {}


def patch_id_of(specs: dict[str, tuple[dict, str]], key: str) -> str | None:
    """そのトラック spec が使うパッチ ID。spec の params.patch > concept のトラック計画 > トラック種別の既定。"""
    from common import concept_tracks

    p = (specs.get(key, ({}, ""))[0].get("params") or {}).get("patch")
    if p:
        return str(p)
    for t in concept_tracks(specs):
        if t.get("spec") == key and t.get("patch"):
            return str(t["patch"])
    return defaults().get(track_of(specs, key) or "")


def allowed_params(entry: dict) -> set[str]:
    if entry.get("kind") == "drums":
        return set(entry.get("pieces") or {})
    return set(entry.get("params") or {})


def synthdef_args() -> dict[str, set[str]]:
    """synthdefs.scd から SynthDef 名 -> 引数名の集合を読む(登録簿との整合検査用)。"""
    src = SYNTHDEFS.read_text(encoding="utf-8")
    out: dict[str, set[str]] = {}
    for m in re.finditer(r"SynthDef\(\\(\w+),\s*\{\s*\|([^|]*)\|", src):
        out[m.group(1)] = {a.split("=")[0].strip() for a in m.group(2).split(",") if a.strip()}
    return out


def validate_overrides(entry: dict, overrides: dict) -> list[str]:
    """patch_params の検査。melodic は {引数: 値}、drums は {ピース名: {引数: 値}}。"""
    errs: list[str] = []
    if not isinstance(overrides, dict):
        return ["patch_params はマッピングで書く"]
    for k, v in overrides.items():
        if entry.get("kind") == "drums":
            piece = (entry.get("pieces") or {}).get(k)
            if piece is None:
                errs.append(f"ドラムのピース '{k}' はない(使えるもの: {', '.join(entry.get('pieces') or {})})")
                continue
            if not isinstance(v, dict):
                errs.append(f"patch_params.{k} は {{引数: 値}} で書く")
                continue
            for a, x in v.items():
                if a not in piece["params"]:
                    errs.append(f"{k} に引数 '{a}' はない(使えるもの: {', '.join(piece['params'])})")
                elif not isinstance(x, (int, float)) or isinstance(x, bool):
                    errs.append(f"patch_params.{k}.{a} は数値で書く")
        else:
            if k not in entry["params"]:
                errs.append(f"引数 '{k}' はない(使えるもの: {', '.join(entry['params'])})")
            elif not isinstance(v, (int, float)) or isinstance(v, bool):
                errs.append(f"patch_params.{k} は数値で書く")
    return errs


def check(song: str) -> list[str]:
    reg = registry()
    specs = load_specs(song)
    errs: list[str] = []
    for key in active_keys(specs):
        t = track_of(specs, key)
        if not t or t == "vocal":
            continue
        pid = patch_id_of(specs, key)
        if not pid:
            errs.append(f"{key}: patch が決まらない(params.patch を書くか、00-concept のトラック計画に patch を入れる)")
            continue
        if pid not in reg:
            errs.append(f"{key}: 登録簿 config/patches.yaml にないパッチ '{pid}'(`patches.py list` で確認)")
            continue
        ov = (specs[key][0].get("params") or {}).get("patch_params")
        if ov:
            errs += [f"{key}: {e}" for e in validate_overrides(reg[pid], ov)]
    return errs


def cmd_check(song: str) -> int:
    errs = check(song)
    for e in errs:
        print(f"[エラー] {e}")
    if errs:
        return 2
    specs = load_specs(song)
    for key in active_keys(specs):
        if track_of(specs, key) and track_of(specs, key) != "vocal":
            print(f"  ✔ {key}: {patch_id_of(specs, key)}")
    print("音色(パッチ)はすべて登録簿と一致しています。")
    return 0


def cmd_list() -> int:
    for pid, e in registry().items():
        print(f" {pid:<14} [{e.get('kind')}] {e.get('name')} — {e.get('desc', '')}")
    return 0


def cmd_show(pid: str) -> int:
    e = registry().get(pid)
    if not e:
        print(f"[エラー] 登録簿にないパッチ: {pid}", file=sys.stderr)
        return 2
    print(f"■ {pid}: {e['name']} [{e['kind']}] — {e.get('desc', '')}")
    if e["kind"] == "drums":
        for name, p in e["pieces"].items():
            print(f"  {name:<11} ノート {p['notes']}  {p['synthdef']}  {p['params']}")
    else:
        print(f"  synthdef={e['synthdef']}" + ("  mono" if e.get("mono") else ""))
        print(f"  params: {e['params']}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").add_argument("song")
    sub.add_parser("list")
    sub.add_parser("show").add_argument("id")
    a = ap.parse_args()
    sys.exit({"check": lambda: cmd_check(a.song), "list": cmd_list, "show": lambda: cmd_show(a.id)}[a.cmd]())


if __name__ == "__main__":
    main()
