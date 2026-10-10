#!/usr/bin/env python3
"""この曲(プロジェクト)専用の音色(パッチ)の登録簿 projects/<song>/synth/patches.yaml の参照と検査。

  patches.py check <song>      曲のトラック spec が指す patch / patch_params が登録簿と合っているか検査(エラーは終了コード 2)
  patches.py list <song>       その曲の登録簿の一覧
  patches.py show <song> <id>  そのパッチの引数と既定値(spec の patch_params を決める根拠)

音色は曲ごとに持ち、他の曲の音色は流用しない。パッチ = Sonic Pi 内蔵シンセ(synth)+ 引数(params)+ 任意の FX(fx)。
ユーザーが用意した wav(projects/<song>/samples/)だけは、patches.yaml の sample で鳴らせる(Sonic Pi 同梱のサンプルは使わない)。
内蔵シンセ・FX の名前と引数は config/sonicpi_synths.json(`sonicpi.py dump-info` で作り直す)と照合する。
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from functools import lru_cache
from pathlib import Path

import yaml
from common import ROOT, active_keys, load_specs, require_project, track_of

INFO_PATH = ROOT / "config" / "sonicpi_synths.json"
# sample :xxx に渡せる主な引数(ユーザーの wav を鳴らすパッチの params に書ける)
SAMPLE_OPTS = {
    "amp", "pan", "attack", "decay", "sustain", "release", "attack_level", "decay_level", "sustain_level", "env_curve",
    "cutoff", "lpf", "hpf", "res", "rate", "start", "finish", "norm", "pitch", "window_size", "pitch_dis", "time_dis",
}


def registry_path(song: str) -> Path:
    return require_project(song) / "synth" / "patches.yaml"


@lru_cache(maxsize=1)
def info() -> dict:
    """Sonic Pi 内蔵シンセ・FX の {synths: {名前: [引数]}, fx: {...}}。"""
    if not INFO_PATH.is_file():
        sys.exit("[エラー] config/sonicpi_synths.json がありません(`uv run scripts/sonicpi.py dump-info` で作る。Sonic Pi が必要)")
    return json.loads(INFO_PATH.read_text(encoding="utf-8"))


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


def is_sample(holder: dict) -> bool:
    return holder.get("sample") is not None


def allowed_params(entry: dict) -> set[str]:
    if entry.get("kind") == "drums":
        return set(entry.get("pieces") or {})
    return set(entry.get("params") or {})


def fx_errors(name: str, entry: dict) -> list[str]:
    """パッチ(キット)全体にかける FX の検査。fx: [{name: reverb, params: {room: 0.6}}]"""
    errs: list[str] = []
    for i, fx in enumerate(entry.get("fx") or []):
        fname = (fx or {}).get("name")
        if fname not in info()["fx"]:
            errs.append(f"{name}: fx[{i}] '{fname}' は Sonic Pi の内蔵 FX にない(`sonicpi.py fx` で一覧)")
            continue
        for k, v in (fx.get("params") or {}).items():
            if k not in info()["fx"][fname]:
                errs.append(f"{name}: fx '{fname}' に引数 '{k}' はない")
            elif not isinstance(v, (int, float)) or isinstance(v, bool):
                errs.append(f"{name}: fx '{fname}' の {k} は数値で書く")
    return errs


def voice_errors(name: str, h: dict) -> list[str]:
    """1つの音(melodic のパッチ、または drums のピース)の synth / params / sweep の検査。"""
    errs: list[str] = []
    params = h.get("params")
    if not isinstance(params, dict):
        return [f"{name}: params はマッピングで書く"]
    if is_sample(h):
        if h.get("synth"):
            errs.append(f"{name}: sample と synth は同時に指定できない")
        valid, what = SAMPLE_OPTS, "sample の引数"
    else:
        synth = h.get("synth")
        if synth not in info()["synths"]:
            return [f"{name}: synth '{synth}' は Sonic Pi の内蔵シンセにない(`sonicpi.py synths` で一覧。他の音源は使わない)"]
        valid, what = set(info()["synths"][synth]), f"{synth} の引数"
    errs += [f"{name}: params '{k}' は {what} にない" for k in params if k not in valid]
    errs += [f"{name}: params.{k} は数値で書く" for k, v in params.items() if not isinstance(v, (int, float)) or isinstance(v, bool)]
    sw = h.get("sweep")
    if sw is not None and (is_sample(h) or not isinstance(sw, dict) or not {"note", "time"} <= set(sw)):
        errs.append(f"{name}: sweep は合成シンセ用の {{note: 到達ノート, time: 秒}}")
    return errs


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


def sample_errors(song: str, pid: str, entry: dict) -> list[str]:
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
    return errs


def check(song: str, only: str | None = None) -> list[str]:
    """曲のトラック spec の音色を検査する。only=spec キーならそのトラックだけ。"""
    reg = registry(song)
    specs = load_specs(song)
    errs: list[str] = []
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
        if entry.get("kind") == "drums":
            for pn, piece in (entry.get("pieces") or {}).items():
                errs += [f"{key}: {e}" for e in voice_errors(f"{pid}.{pn}", piece)]
        elif entry.get("kind") == "melodic":
            errs += [f"{key}: {e}" for e in voice_errors(pid, entry)]
        else:
            errs.append(f"{key}: パッチ '{pid}' の kind は melodic か drums")
        errs += [f"{key}: {e}" for e in fx_errors(pid, entry)]
        errs += [f"{key}: {e}" for e in sample_errors(song, pid, entry)]
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
            print(f"  {name:<11} ノート {p['notes']}  {p.get('sample') or p.get('synth')}  {p['params']}")
    else:
        print(f"  {'sample=' + e['sample'] if e.get('sample') else 'synth=' + str(e.get('synth'))}" + ("  mono" if e.get("mono") else ""))
        print(f"  params: {e['params']}")
        if e.get("fx"):
            print(f"  fx: {e['fx']}")
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
