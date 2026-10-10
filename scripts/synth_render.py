#!/usr/bin/env python3
"""トラック MIDI を Sonic Pi の内蔵シンセでゼロから合成して wav にする(実時間で録音)。

  synth_render.py <song> <name> [--out PATH] [--dry-run]    tracks/<name>.mid -> stems/<name>.wav

流れ: MIDI を読む -> spec の patch / patch_params で音色を決める -> ボイス列を Sonic Pi の Ruby コードに書く
-> ヘッドレスの Sonic Pi で実行しながら録音(sonicpi.py)-> ffmpeg で 16bit wav にする。
パッチ一覧は曲ごと(projects/<song>/synth/patches.yaml)。他の曲の音色は流用しない。
サンプルはユーザーが用意した wav(projects/<song>/samples/)を patches.yaml の sample で指定したときだけ。
Sonic Pi には非リアルタイム書き出しがないため、レンダリングには曲の長さ分の時間がかかる(録音中は音が鳴る)。
"""

from __future__ import annotations

import argparse
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
import sonicpi
from common import ROOT, load_dotenv, load_specs, require_project

load_dotenv()

TAIL = 1.0  # 最後の音のあとに残す余韻(秒)
MONO_GAP = 0.02  # mono パッチで、この秒数以内に次の音が始まれば同じ音のままグライドする
DEFAULT_GLIDE = 0.08  # mono パッチで params に note_slide が無いときのグライド秒


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
    rate は root_note があればノートの高さに合わせ、無ければ params のまま(ワンショット)。tail=再生が終わるまでの秒数。"""
    rel = holder.get("sample")
    if rel is None:
        return {}
    if proj is None:
        raise ValueError("サンプルのパッチには曲のディレクトリ(proj)が必要です")
    path = str((proj / rel).resolve())
    root = holder.get("root_note")
    rate = 2 ** ((note - int(root)) / 12) if root is not None else float((holder.get("params") or {}).get("rate", 1.0))
    return {"sample": path, "rate": round(rate, 6), "tail": wav_seconds(path) / rate}


def build_voices(notes: list[dict], entry: dict, overrides: dict, proj: Path | None = None) -> list[dict]:
    """ノート列 -> ボイス列。
    voice = {start, synth|sample, opts, end(None=ワンショット), sets[(t, note)], sweep, tail}。
    opts は Sonic Pi の引数(amp はベロシティを掛けた値)。サンプルのパッチは sample(絶対パス)と tail が付く。"""
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
            voices.append({"start": n["start"], "end": None, "opts": c, "sets": [], "sweep": piece.get("sweep"),
                           **({"sample": sm["sample"], "tail": sm["tail"]} if sm else {"synth": piece["synth"]})})
        return voices

    oneshot = bool(entry.get("oneshot")) or bool(entry.get("sample"))
    for n in notes:
        c = dict(params)
        c["amp"] = round(c.get("amp", 0.4) * (n["vel"] / 127), 5)
        sm = sample_fields(entry, n["note"], proj)
        if sm:
            c["rate"] = sm["rate"]
        else:
            c["note"] = n["note"]
            if entry.get("mono"):
                c.setdefault("note_slide", DEFAULT_GLIDE)
        prev = voices[-1] if voices else None
        if entry.get("mono") and not oneshot and prev and prev["end"] is not None and n["start"] <= prev["end"] + MONO_GAP:
            prev["sets"].append((n["start"], n["note"]))
            prev["end"] = n["end"]
            continue
        voices.append({
            "start": n["start"], "opts": c, "sets": [], "sweep": None,
            "end": None if oneshot else n["end"],
            **({"sample": sm["sample"], "tail": sm["tail"]} if sm else {"synth": entry["synth"]}),
        })
    return voices


def envelope_total(opts: dict) -> float:
    """固定長のエンベロープ(ワンショット)が鳴り終わるまでの秒数。"""
    return sum(float(opts.get(k, d)) for k, d in (("attack", 0.0), ("decay", 0.0), ("sustain", 0.0), ("release", 1.0)))


def end_time(voices: list[dict]) -> float:
    """最後の音が消えるまでの秒数(リリース・固定長の減衰を含む)。"""
    end = 0.0
    for v in voices:
        if v["end"] is not None:
            end = max(end, v["end"] + float(v["opts"].get("release", 1.0)))
        else:
            end = max(end, v["start"] + envelope_total(v["opts"]))
        if "tail" in v:  # サンプルは最後まで鳴らす
            end = max(end, v["start"] + v["tail"])
    return end + TAIL


def rb_sym(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise ValueError(f"Sonic Pi の名前に使えない文字: {name!r}")
    return ":" + name


def rb_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("#", "\\#") + '"'


def rb_opts(opts: dict) -> str:
    return ", ".join(f"{rb_sym(k)[1:]}: {float(x)!r}" for k, x in opts.items())


def _num(x: float) -> str:
    return repr(round(float(x), 4))


def voice_lines(voices: list[dict]) -> list[str]:
    """ボイス列 -> 時刻順の Ruby の行(sleep で時間を進めながら synth / sample を鳴らす)。
    同時刻の順序は Python で確定させる。Sonic Pi の既定テンポ(60 BPM)では 1 拍 = 1 秒。"""
    lines: list[str] = []
    ev: list[tuple] = []  # (time, order, voice index, payload)
    for i, v in enumerate(voices):
        ev.append((v["start"], 0, i, None))
        ev += [(t, 1, i, nt) for t, nt in v["sets"]]
    ev.sort(key=lambda e: (e[0], e[1], e[2]))
    now = 0.0
    for t, kind, i, payload in ev:
        tr = round(t, 4)  # 丸めた時刻の差を sleep にして、誤差を積み上げない
        if tr - now > 1e-6:
            lines.append(f"sleep {_num(tr - now)}")
            now = tr
        v = voices[i]
        if kind == 1:
            lines.append(f"control v{i}, note: {float(payload)!r}")
            continue
        o = dict(v["opts"])
        if v["end"] is not None:  # 音の長さに合わせて保持部を決める(リリースはそのあとに鳴る)
            o["sustain"] = round(max(v["end"] - v["start"] - float(o.get("attack", 0)) - float(o.get("decay", 0)), 0.0), 4)
        ref = f"v{i} = " if (v["sets"] or v["sweep"]) else ""
        if "sample" in v:
            lines.append(f"{ref}sample {rb_str(v['sample'])}, {rb_opts(o)}")
        else:
            if v["sweep"]:
                o["note_slide"] = float(v["sweep"]["time"])
            lines.append(f"{ref}synth {rb_sym(v['synth'])}, {rb_opts(o)}")
        if v["sweep"]:
            lines.append(f"control v{i}, note: {float(v['sweep']['note'])!r}")
    return lines


def build_code(voices: list[dict], duration: float, fx: list[dict] | None = None) -> str:
    """ボイス列 -> Sonic Pi のコード全体。fx は外側から順に with_fx で包む。曲の終わりまで sleep して余韻(FX の尾)を残す。"""
    body = voice_lines(voices)
    last = sum(float(ln.split()[1]) for ln in body if ln.startswith("sleep "))
    body.append(f"sleep {_num(max(duration - last, 0.0))}")
    pad = "  "
    out = ["use_bpm 60", "use_random_seed 0"]
    depth = 0
    for f in fx or []:
        opts = rb_opts(f.get("params") or {})
        out.append(f"{pad * depth}with_fx {rb_sym(f['name'])}{', ' + opts if opts else ''} do")
        depth += 1
    out += [pad * depth + ln for ln in body]
    for d in reversed(range(depth)):
        out.append(f"{pad * d}end")
    return "\n".join(out) + "\n"


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
    synthesize(voices, duration, target, reg[pid].get("fx"), dry_run)
    return target


def synthesize(voices: list[dict], duration: float, target: Path, fx: list[dict] | None = None, dry_run: bool = False) -> None:
    """ボイス列を Sonic Pi で鳴らしながら録音し、16bit wav の target にする。ピークを表示する。"""
    code = build_code(voices, duration, fx)
    if dry_run:
        print(f"[dry-run] Sonic Pi で約{duration:.1f}秒録音して {target} に書く(Sonic Pi={sonicpi.find_app() or '未検出'})")
        return
    if not shutil.which("ffmpeg"):
        sys.exit("[エラー] ffmpeg が見つかりません(brew install ffmpeg)")
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Sonic Pi で録音中(約{duration:.0f}秒+起動。録音中は音が鳴ります)…")
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "rec.wav"
        sonicpi.record(code, duration, raw)
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-ar", "48000", "-c:a", "pcm_s16le", str(target)],
                           capture_output=True, text=True)
        if r.returncode != 0 or not target.is_file():
            sys.exit(f"[エラー] wav の変換に失敗しました:\n{r.stderr.strip()}")
    pk = peak_db(target)
    if pk is not None:
        msg = f"ピーク {pk:.1f} dBFS"
        if pk == float("-inf"):
            msg += "  [注意] 無音です。パッチの synth / params(amp など)を確認してください"
        elif pk > -0.5:
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
