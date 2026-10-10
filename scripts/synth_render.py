#!/usr/bin/env python3
"""トラック MIDI を SuperCollider(非リアルタイム=NRT)でゼロから合成して wav にする。

  synth_render.py <song> <name> [--out PATH] [--dry-run]    tracks/<name>.mid -> stems/<name>.wav

流れ: MIDI を読む -> spec の patch / patch_params で音色を決める -> ボイス列を .scd に書く -> sclang が Score.recordNRT で wav を書く。
SynthDef とパッチ一覧は曲ごと(projects/<song>/synth/)。他の曲の音色は流用しない。
サンプルはユーザーが用意した wav(projects/<song>/samples/)を patches.yaml の sample で指定したときだけ。SoundFont は使わない。
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from array import array
from pathlib import Path

import mido
import patches
from common import ROOT, load_dotenv, load_specs, require_project

load_dotenv()

SAMPLE_RATE = 48000
TAIL = 1.0  # 最後の音のあとに残す余韻(秒)
MONO_GAP = 0.02  # mono パッチで、この秒数以内に次の音が始まれば同じ音のままグライドする
SC_APP = Path("/Applications/SuperCollider.app/Contents")


def find_sclang() -> str | None:
    for c in (os.environ.get("SCLANG"), shutil.which("sclang"), str(SC_APP / "MacOS" / "sclang")):
        if c and Path(c).is_file() and os.access(c, os.X_OK):
            return c
    return None


def read_notes(mid: Path) -> list[dict]:
    """MIDI -> [{start, end, note, vel, ch}](秒。テンポ変化を反映)。"""
    t, open_, notes = 0.0, {}, []
    for msg in mido.MidiFile(str(mid)):
        t += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            open_.setdefault((msg.channel, msg.note), []).append((t, msg.velocity))
        elif msg.type in ("note_off", "note_on") and open_.get((msg.channel, msg.note)):
            s, v = open_[(msg.channel, msg.note)].pop(0)
            notes.append({"start": s, "end": max(t, s + 0.01), "note": msg.note, "vel": v, "ch": msg.channel})
    for lst in open_.values():  # 閉じ忘れは 0.25 秒で閉じる
        for s, v in lst:
            notes.append({"start": s, "end": s + 0.25, "note": 0, "vel": v, "ch": 0})
    return sorted(notes, key=lambda n: (n["start"], n["note"]))


def mtof(n: int) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def resolve(entry: dict, overrides: dict) -> dict:
    """パッチの params(または各ピースの params)に patch_params を重ねた値。"""
    ov = overrides or {}
    if entry["kind"] == "drums":
        return {
            name: {**p["params"], **(ov.get(name) or {})} for name, p in entry["pieces"].items()
        }
    return {**entry["params"], **ov}


def wav_seconds(path: str) -> float:
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def sample_fields(holder: dict, note: int, proj: Path | None) -> dict:
    """sample を持つパッチ(またはドラムのピース)のボイスに足す項目。sample が無ければ空。
    rate は root_note があればノートの高さに合わせ、無ければ 1(ワンショット)。tail=再生が終わるまでの秒数。"""
    rel = holder.get("sample")
    if rel is None:
        return {}
    if proj is None:
        raise ValueError("サンプルのパッチには曲のディレクトリ(proj)が必要です")
    path = str((proj / rel).resolve())
    root = holder.get("root_note")
    rate = 2 ** ((note - int(root)) / 12) if root is not None else 1.0
    return {"sample": path, "rate": round(rate, 6), "tail": wav_seconds(path) / rate}


def build_voices(notes: list[dict], entry: dict, overrides: dict, proj: Path | None = None) -> list[dict]:
    """ノート列 -> ボイス列。voice = {start, def, release(None=自然に消える), controls, sets[(t, freq)]}。
    サンプルのパッチは voice に sample(絶対パス)と tail が付き、controls に rate が入る(buf は write_scd が割り当てる)。"""
    params = resolve(entry, overrides)
    voices: list[dict] = []
    if entry["kind"] == "drums":
        by_note = {n: (name, p) for name, p in entry["pieces"].items() for n in p["notes"]}
        for n in notes:
            hit = by_note.get(n["note"])
            if not hit:
                continue  # 割り当てのないノートは鳴らさない(検証側で警告)
            name, piece = hit
            c = dict(params[name])
            c["amp"] = round(c.get("amp", 0.5) * (n["vel"] / 127), 5)
            sm = sample_fields(piece, n["note"], proj)
            if sm:
                c["rate"] = sm["rate"]
            voices.append({"start": n["start"], "def": piece["synthdef"], "release": None, "controls": c, "sets": [],
                           **({"sample": sm["sample"], "tail": sm["tail"]} if sm else {})})
        return voices

    oneshot = bool(entry.get("oneshot"))
    for n in notes:
        c = dict(params)
        c["amp"] = round(c.get("amp", 0.4) * (n["vel"] / 127), 5)
        c["freq"] = round(mtof(n["note"]), 4)
        if entry.get("uses_dur"):
            c["dur"] = round(n["end"] - n["start"], 4)
        sm = sample_fields(entry, n["note"], proj)
        if sm:
            c["rate"] = sm["rate"]
        prev = voices[-1] if voices else None
        if entry.get("mono") and not oneshot and prev and prev["release"] is not None and n["start"] <= prev["release"] + MONO_GAP:
            prev["sets"].append((n["start"], c["freq"]))
            prev["release"] = n["end"]
            continue
        voices.append({
            "start": n["start"], "def": entry["synthdef"], "controls": c, "sets": [],
            "release": None if oneshot else n["end"],
            **({"sample": sm["sample"], "tail": sm["tail"]} if sm else {}),
        })
    return voices


def sc_symbol(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise ValueError(f"SuperCollider の名前に使えない文字: {name!r}")
    return "\\" + name


def sc_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def end_time(voices: list[dict]) -> float:
    """最後の音が消えるまでの秒数(リリース・固定長の減衰を含む)。"""
    end = 0.0
    for v in voices:
        tail = float(v["controls"].get("rel", 0.5)) if v["release"] is not None else max(
            [float(x) for k, x in v["controls"].items() if k in ("decay", "rel")] or [1.0]) * 1.2
        end = max(end, (v["release"] if v["release"] is not None else v["start"]) + tail)
        if "tail" in v:  # サンプルは最後まで鳴らす
            end = max(end, v["start"] + v["tail"])
    return end + TAIL


def score_events(voices: list[dict]) -> list[tuple]:
    """ボイス列 -> 時刻順のイベント (time, kind, id, def, controls)。kind: 0=new 1=set 2=release。
    SuperCollider 側では並べ替えない(同時刻の順序を Python で確定させる)。"""
    ev: list[tuple] = []
    for i, v in enumerate(voices):
        vid = 1000 + i
        ev.append((v["start"], 0, vid, v["def"], v["controls"]))
        ev += [(t, 1, vid, "", {"freq": f}) for t, f in v["sets"]]
        if v["release"] is not None:
            ev.append((v["release"], 2, vid, "", {}))
    return sorted(ev, key=lambda e: (e[0], e[1], e[2]))


def write_scd(path: Path, voices: list[dict], duration: float, osc: Path, out: Path, defs: Path) -> None:
    samples = sorted({v["sample"] for v in voices if "sample" in v})  # サンプル wav -> バッファ番号(0〜)
    for v in voices:
        if "sample" in v:
            v["controls"]["buf"] = samples.index(v["sample"])
    bufs_src = "\n".join(f"score.add([0.0, ['/b_allocRead', {i}, {sc_str(f)}]]);" for i, f in enumerate(samples))
    lines = []
    for t, kind, vid, d, ctl in score_events(voices):
        c = ", ".join(f"{sc_symbol(k)}, {float(x)!r}" for k, x in ctl.items())
        lines.append(f"[{t!r}, {kind}, {vid}, {sc_symbol(d) if d else 'nil'}, [{c}]]")
    events_src = ",\n".join(lines)
    used = sorted({v["def"] for v in voices})
    used_src = ", ".join(sc_symbol(u) for u in used)
    path.write_text(
        f"""(
var defs = {sc_str(str(defs))}.load;
var byName = ();
var events = [
{events_src}
];
var score = List.new;
var opts = ServerOptions.new.sampleRate_({SAMPLE_RATE}).numOutputBusChannels_(2).numInputBusChannels_(0);
defs.do {{ |d| byName[d.name.asSymbol] = d }};
[{used_src}].do {{ |n| score.add([0.0, ['/d_recv', byName[n].asBytes]]) }};
{bufs_src}
events.do {{ |e|
	case
	{{ e[1] == 0 }} {{ score.add([e[0], ['/s_new', e[3], e[2], 0, 0] ++ e[4]]) }}
	{{ e[1] == 1 }} {{ score.add([e[0], ['/n_set', e[2]] ++ e[4]]) }}
	{{ true }} {{ score.add([e[0], ['/n_set', e[2], \\gate, 0]]) }};
}};
score.add([{duration!r}, ['/c_set', 0, 0]]);
Score.recordNRT(score, {sc_str(str(osc))}, {sc_str(str(out))}, nil, {SAMPLE_RATE}, "WAV", "int16", opts, duration: {duration!r}, action: {{ 0.exit }});
)
""",
        encoding="utf-8",
    )


def peak_db(wav_path: Path) -> float | None:
    """int16 wav のピーク(dBFS)。クリップ検出用。"""
    import math

    try:
        with wave.open(str(wav_path)) as w:
            if w.getsampwidth() != 2:
                return None
            a = array("h")
            a.frombytes(w.readframes(w.getnframes()))
    except (wave.Error, OSError):
        return None
    pk = max((abs(x) for x in a), default=0)
    return 20 * math.log10(pk / 32768) if pk else float("-inf")


def render(song: str, name: str, out: Path | None = None, dry_run: bool = False) -> Path:
    proj = require_project(song)
    mid = proj / "tracks" / f"{name}.mid"
    if not mid.is_file():
        sys.exit(f"[エラー] 見つかりません: projects/{song}/tracks/{name}.mid")
    num = name.split("_", 1)[0]
    specs = load_specs(song)
    key = next((k for k in specs if k.startswith(f"{num}-")), None)
    if not key:
        sys.exit(f"[エラー] spec {num}-*.md がありません")
    pid = patches.patch_id_of(specs, key)
    reg = patches.registry(song)
    if pid not in reg:
        sys.exit(f"[エラー] {key}: パッチ '{pid}' は projects/{song}/synth/patches.yaml にありません(`patches.py list {song}`)")
    perrs = patches.check(song, only=key)
    if perrs:
        sys.exit("\n".join(f"[エラー] {e}" for e in perrs) + "\n先に直してください(patches.py check)")
    overrides = (specs[key][0].get("params") or {}).get("patch_params") or {}
    errs = patches.validate_overrides(reg[pid], overrides)
    if errs:
        sys.exit("\n".join(f"[エラー] {key}: {e}" for e in errs))

    notes = read_notes(mid)
    voices = build_voices(notes, reg[pid], overrides, proj)
    if reg[pid]["kind"] == "drums":
        skipped = sorted({n["note"] for n in notes} - {x for p in reg[pid]["pieces"].values() for x in p["notes"]})
        if skipped:
            print(f"[注意] キット {pid} に割り当てのないノート番号は鳴らしません: {skipped}")
    if not voices:
        sys.exit("[エラー] 鳴らすノートがありません(MIDI が空、またはキットに割り当てがない)")
    duration = end_time(voices)

    target = out or proj / "stems" / f"{name}.wav"
    if out is None and target.exists():
        sys.exit(f"[エラー] 既に存在します(上書きしません): {target.relative_to(ROOT)}")
    print(f"■ {name}: パッチ {pid}({reg[pid]['name']})・{len(voices)} ボイス・約{duration:.1f}秒")
    synthesize(voices, duration, target, patches.synthdefs_path(song), dry_run)
    return target


def synthesize(voices: list[dict], duration: float, target: Path, defs: Path, dry_run: bool = False) -> None:
    """ボイス列を sclang(NRT)で target の wav にする。ピークを表示する。"""
    sclang = find_sclang()
    if dry_run:
        print(f"[dry-run] sclang で {target} に合成(sclang={sclang or '未検出'})")
        return
    if not sclang:
        sys.exit("[エラー] sclang が見つかりません。SuperCollider を入れてください(brew install --cask supercollider)。"
                 "場所が標準でなければ .env に SCLANG=/path/to/sclang を設定")

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        scd, osc = Path(td) / "render.scd", Path(td) / "score.osc"
        tmp_wav = Path(td) / "out.wav"
        write_scd(scd, voices, duration, osc, tmp_wav, defs)
        try:
            r = subprocess.run([sclang, str(scd)], capture_output=True, text=True, timeout=600, env=os.environ.copy())
        except subprocess.TimeoutExpired:
            sys.exit("[エラー] sclang が 10 分で終わりませんでした(SuperCollider の起動を確認してください)")
        if not tmp_wav.is_file() or tmp_wav.stat().st_size < 1000:
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-15:])
            sys.exit(f"[エラー] 合成に失敗しました(wav が出ていません)。sclang の出力末尾:\n{tail}")
        shutil.copyfile(tmp_wav, target)
    pk = peak_db(target)
    if pk is not None:
        msg = f"ピーク {pk:.1f} dBFS"
        if pk > -0.5:
            msg += "  [注意] クリップしています。patch_params の amp を下げるか velocity を下げて再生成してください"
        print(msg)
    print(f"出力: {target.relative_to(ROOT) if target.is_relative_to(ROOT) else target}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("name", help="tracks/ の MIDI 名(拡張子なし 例: 04_bass_v1)")
    ap.add_argument("--out", type=Path, help="出力先(試聴用の一時 wav など。省略時は stems/<name>.wav)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", a.name):
        sys.exit(f"[エラー] トラック名は英数字・_・- のみ: {a.name!r}")
    render(a.song, a.name, a.out, a.dry_run)


if __name__ == "__main__":
    main()
