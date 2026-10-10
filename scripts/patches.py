#!/usr/bin/env python3
"""この曲(プロジェクト)専用の音色(パッチ)の登録簿 projects/<song>/synth/patches.yaml の参照と検査。

  patches.py check <song>      曲のトラック spec が指す patch / patch_params が登録簿と合っているか検査(エラーは終了コード 2)
  patches.py list <song>       その曲の登録簿の一覧
  patches.py show <song> <id>  そのパッチの引数と既定値(spec の patch_params を決める根拠)

音色は曲ごとに持ち、他の曲やリポジトリ共通の音色は流用しない。実体は projects/<song>/synth/synthdefs.scd(SuperCollider)。
ユーザーが用意した wav(projects/<song>/samples/)だけは、patches.yaml の sample で鳴らせる。SoundFont・外部音源は使わない。
"""

from __future__ import annotations

import argparse
import re
import sys
import wave
from pathlib import Path

import yaml
from common import active_keys, load_specs, require_project, track_of


def registry_path(song: str) -> Path:
    return require_project(song) / "synth" / "patches.yaml"


def synthdefs_path(song: str) -> Path:
    return require_project(song) / "synth" / "synthdefs.scd"


def registry(song: str) -> dict[str, dict]:
    p = registry_path(song)
    if not p.is_file():
        return {}
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("patches") or {}


def patch_id_of(specs: dict[str, tuple[dict, str]], key: str) -> str | None:
    """そのトラック spec が使うパッチ ID。spec の params.patch > concept のトラック計画。
    AI が音色を補う既定はない(音はユーザーが指示する)。"""
    from common import concept_tracks

    p = (specs.get(key, ({}, ""))[0].get("params") or {}).get("patch")
    if p:
        return str(p)
    for t in concept_tracks(specs):
        if t.get("spec") == key and t.get("patch"):
            return str(t["patch"])
    return None


def allowed_params(entry: dict) -> set[str]:
    if entry.get("kind") == "drums":
        return set(entry.get("pieces") or {})
    return set(entry.get("params") or {})


def synthdef_args(song: str) -> dict[str, set[str]]:
    """曲の synthdefs.scd から SynthDef 名 -> 引数名の集合を読む(登録簿との整合検査用)。"""
    p = synthdefs_path(song)
    src = p.read_text(encoding="utf-8") if p.is_file() else ""
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


def sample_file(song: str, rel: str) -> Path | None:
    """patches.yaml の sample(曲の samples/ 配下の wav)を絶対パスにする。範囲外・存在しなければ None。"""
    base = (require_project(song) / "samples").resolve()
    p = (require_project(song) / rel).resolve()
    return p if p.is_relative_to(base) and p.suffix.lower() == ".wav" and p.is_file() else None


def sample_errors(song: str, pid: str, entry: dict, args: dict[str, set[str]]) -> list[str]:
    """サンプルを使うパッチ(patch 自身、または drums のピース)の検査。"""
    errs: list[str] = []
    holders = [(pid, entry)] if entry.get("kind") != "drums" else [(f"{pid}.{n}", p) for n, p in (entry.get("pieces") or {}).items()]
    for name, h in holders:
        rel = h.get("sample")
        if rel is None:
            continue
        f = sample_file(song, str(rel))
        if f is None:
            errs.append(f"{name}: sample '{rel}' は projects/{song}/samples/ 内の wav ファイルで指定する(ユーザーが用意したものだけ)")
            continue
        try:
            with wave.open(str(f)):
                pass
        except (wave.Error, EOFError):
            errs.append(f"{name}: {rel} は PCM の WAV ではありません(16/24bit PCM の wav に変換してもらう)")
        miss = {"buf", "rate"} - args.get(h.get("synthdef", ""), set())
        if miss:
            errs.append(f"{name}: サンプルを鳴らす SynthDef '{h.get('synthdef')}' に引数 {sorted(miss)} が必要")
    return errs


def check(song: str, only: str | None = None) -> list[str]:
    """曲のトラック spec の音色を検査する。only=spec キーならそのトラックだけ。"""
    reg = registry(song)
    specs = load_specs(song)
    errs: list[str] = []
    args = synthdef_args(song)
    for key in active_keys(specs):
        t = track_of(specs, key)
        if not t or t == "vocal" or (only and key != only):
            continue
        pid = patch_id_of(specs, key)
        if not pid:
            errs.append(f"{key}: patch が決まらない(ユーザーが指示した音の patch を params.patch か user_inputs.yaml のトラックに入れる)")
            continue
        if pid not in reg:
            errs.append(f"{key}: この曲の登録簿 projects/{song}/synth/patches.yaml にないパッチ '{pid}'(他の曲の音色は流用しない。ユーザーの指示から synth/ に作る)")
            continue
        entry = reg[pid]
        used = [entry["synthdef"]] if entry.get("kind") != "drums" else [p["synthdef"] for p in entry["pieces"].values()]
        errs += [f"{key}: SynthDef '{d}' が projects/{song}/synth/synthdefs.scd にない" for d in used if d not in args]
        errs += [f"{key}: {e}" for e in sample_errors(song, pid, entry, args)]
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
    print("音色(パッチ)はすべてこの曲の登録簿と一致しています。")
    return 0


def cmd_list(song: str) -> int:
    for pid, e in registry(song).items():
        print(f" {pid:<14} [{e.get('kind')}] {e.get('name')} — {e.get('desc', '')}")
    return 0


def cmd_show(song: str, pid: str) -> int:
    e = registry(song).get(pid)
    if not e:
        print(f"[エラー] 登録簿にないパッチ: {pid}", file=sys.stderr)
        return 2
    print(f"■ {pid}: {e['name']} [{e['kind']}] — {e.get('desc', '')}")
    if e["kind"] == "drums":
        for name, p in e["pieces"].items():
            print(f"  {name:<11} ノート {p['notes']}  {p['synthdef']}  {p['params']}")
    else:
        print(f"  synthdef={e['synthdef']}" + ("  mono" if e.get("mono") else "") + (f"  sample={e['sample']}" if e.get("sample") else ""))
        print(f"  params: {e['params']}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").add_argument("song")
    sub.add_parser("list").add_argument("song")
    sh = sub.add_parser("show")
    sh.add_argument("song")
    sh.add_argument("id")
    a = ap.parse_args()
    sys.exit({"check": lambda: cmd_check(a.song), "list": lambda: cmd_list(a.song), "show": lambda: cmd_show(a.song, a.id)}[a.cmd]())


if __name__ == "__main__":
    main()
