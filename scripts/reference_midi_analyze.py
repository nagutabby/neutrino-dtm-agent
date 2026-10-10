#!/usr/bin/env python3
"""集めた類似曲の MIDI から抽象的な特徴(テンポ・拍子・キー・コード機能・パート構成・音域・密度)を要約する。

使い方: reference_midi_analyze.py <song> [file.mid ...]   (省略時は reference/midi/*.mid すべて)
  出力: reference/midi/analysis.json と analysis.md
旋律・歌詞・音符列そのものは出力しない。推定値は目安であり、spec を決めるのはユーザー。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import midi_tools
import mido
from common import midi_to_note, require_project
from explain_midi import MAJOR, MINOR, NAMES

ROMAN = ["I", "♭II", "II", "♭III", "III", "IV", "♯IV", "V", "♭VI", "VI", "♭VII", "VII"]
GM_FAMILIES = [
    "ピアノ", "音程打楽器", "オルガン", "ギター", "ベース", "弦", "アンサンブル", "ブラス",
    "リード", "パイプ", "シンセリード", "シンセパッド", "シンセ効果", "民族楽器", "打楽器", "効果音",
]  # fmt: skip
DRUM_CH = 9


def _corr(a: list[float], b: list[float]) -> float:
    ma, mb = sum(a) / 12, sum(b) / 12
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else 0.0


def estimate_key(pc_weight: list[float]) -> tuple[int, str, float]:
    best = (0, "長調", -2.0)
    for tonic in range(12):
        for prof, mode in ((MAJOR, "長調"), (MINOR, "短調")):
            rot = [prof[(i - tonic) % 12] for i in range(12)]
            c = _corr(pc_weight, rot)
            if c > best[2]:
                best = (tonic, mode, c)
    return best


def roman(root: int, q: str, ref_tonic: int) -> str:
    r = ROMAN[(root - ref_tonic) % 12]
    return r.lower() if q == "m" else r


def chord_of_bar(weights: list[float], bass_pc: int | None) -> tuple[int, str] | None:
    """小節内の音の長さで重み付けしたピッチクラスから、三和音(長/短)を選ぶ。ベース音を根音候補に優遇。"""
    if sum(weights) <= 0:
        return None
    best, best_s = None, -1.0
    for root in range(12):
        for q, third in (("", 4), ("m", 3)):
            tones = [root, (root + third) % 12, (root + 7) % 12]
            s = sum(weights[t] for t in tones) - 0.3 * (sum(weights) - sum(weights[t] for t in tones))
            if bass_pc == root:
                s += 0.25 * sum(weights)
            if s > best_s:
                best, best_s = (root, q), s
    return best


def part_label(ch: int, program: int | None) -> str:
    if ch == DRUM_CH:
        return "ドラム"
    return GM_FAMILIES[(program or 0) // 8]


def analyze_file(path: Path) -> dict:
    info = midi_tools.load(path)
    prog: dict[int, int] = {}
    for tr in mido.MidiFile(path).tracks:
        for msg in tr:
            if msg.type == "program_change":
                prog.setdefault(msg.channel, msg.program)
    tonal = [n for n in info.notes if n.channel != DRUM_CH]
    dur_sec = info.end_tick / info.ppq * 60 / info.bpm if info.bpm else 0.0
    res: dict = {
        "file": path.name,
        "tempo_bpm": info.bpm,
        "time_signature": f"{info.time_sig[0]}/{info.time_sig[1]}",
        "bars": info.bars,
        "duration_sec": round(dur_sec, 1),
    }
    if not tonal or not info.ticks_per_bar:
        res.update(key=None, parts={}, roman_per_bar_head=[], common_roman=[], loop_4bars=None)
        return res
    pc = [0.0] * 12
    for n in tonal:
        pc[n.pitch % 12] += n.end - n.start
    tonic, mode, conf = estimate_key(pc)
    ref_tonic = tonic if mode == "長調" else (tonic + 3) % 12
    tpb = info.ticks_per_bar
    bars: dict[int, list[float]] = defaultdict(lambda: [0.0] * 12)
    low: dict[int, int] = {}
    for n in tonal:
        b = n.start // tpb
        bars[b][n.pitch % 12] += min(n.end, (b + 1) * tpb) - n.start
        if n.pitch < 60 and (b not in low or n.pitch < low[b]):
            low[b] = n.pitch
    romans, names = [], []
    for b in range(info.bars):
        c = chord_of_bar(bars[b], low[b] % 12 if b in low else None) if b in bars else None
        if c:
            names.append(f"{NAMES[c[0]]}{c[1]}")
            romans.append(roman(*c, ref_tonic))
    loops = Counter(tuple(romans[i : i + 4]) for i in range(0, max(len(romans) - 3, 0), 4))
    loop = loops.most_common(1)[0] if loops else None
    parts: dict[str, dict] = {}
    by_ch: dict[int, list[int]] = defaultdict(list)
    for n in info.notes:
        by_ch[n.channel].append(n.pitch)
    for ch, ps in sorted(by_ch.items()):
        ps.sort()
        label = part_label(ch, prog.get(ch))
        key = label if label not in parts else f"{label}#{ch}"
        parts[key] = {
            "notes": len(ps),
            "notes_per_sec": round(len(ps) / dur_sec, 2) if dur_sec else 0,
            "register": None if ch == DRUM_CH else [ps[int(len(ps) * 0.05)], ps[int(len(ps) * 0.95)]],
        }
    vel = [n.vel for n in tonal]
    res.update(
        key=f"{NAMES[tonic]} {mode}",
        key_confidence=round(conf, 2),
        roman_per_bar_head=romans[:16],
        chords_per_bar_head=names[:16],
        common_roman=[[r, n] for r, n in Counter(romans).most_common(4)],
        loop_4bars=[list(loop[0]), loop[1]] if loop else None,
        parts=parts,
        velocity_avg=round(sum(vel) / len(vel)),
    )
    return res


def to_markdown(results: list[dict], sources: dict[str, dict]) -> str:
    lines = ["# 類似曲 MIDI の分析(私的な分析用。旋律・音符列は出力しない)", ""]
    for r in results:
        s = sources.get(r["file"], {})
        lines += [f"## {s.get('title') or r['file']}", ""]
        if s.get("url"):
            lines.append(f"- 出典: {s['url']}" + (f"({s['note']})" if s.get("note") else ""))
        lines.append(
            f"- テンポ {r['tempo_bpm']:g} BPM / 拍子 {r['time_signature']} / {r['bars']} 小節(約 {r['duration_sec']} 秒)"
        )
        if r.get("key"):
            lines.append(f"- キー(推定) {r['key']}(確信度 {r['key_confidence']})/ 平均ベロシティ {r['velocity_avg']}")
            if r["loop_4bars"]:
                lines.append(
                    f"- よく出る4小節の進行(ローマ数字、短調は平行長調基準): {' - '.join(r['loop_4bars'][0])}({r['loop_4bars'][1]}回)"
                )
            lines.append(f"- 先頭16小節のコード(推定): {' / '.join(r['chords_per_bar_head'])}")
            lines.append("- よく使われるコード機能: " + "、".join(f"{k}×{v}" for k, v in r["common_roman"]))
        for part, t in r["parts"].items():
            if t["register"] is None:
                lines.append(f"- [{part}] 打点 {t['notes_per_sec']} 回/秒")
            else:
                lo, hi = t["register"]
                lines.append(
                    f"- [{part}] 音域(5〜95%) {midi_to_note(lo)}〜{midi_to_note(hi)}、{t['notes_per_sec']} 音/秒"
                )
        lines.append("")
    lines += [
        "## 使い方の注意",
        "",
        "- コードは小節ごとの三和音への当てはめで、テンションや転調は拾わない。目安として扱う。",
        "- MIDI は採譜者の解釈を含む。複数の曲に共通する傾向(テンポ帯・進行の型・パート構成・音域)を拾い、旋律・リズムパターンは写さない。",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()
    d = require_project(a.song) / "reference" / "midi"
    paths = [d / Path(f).name for f in a.files] if a.files else sorted(d.glob("*.mid"))
    if not paths or not all(p.exists() for p in paths):
        sys.exit(f"MIDI が見つかりません: {d}(reference_midi_fetch.py で取得)")
    sources = {}
    sp = d / "sources.jsonl"
    if sp.exists():
        for line in sp.read_text(encoding="utf-8").splitlines():
            if line.strip():
                j = json.loads(line)
                sources[j["file"]] = j
    results = [analyze_file(p) for p in paths]
    (d / "analysis.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = to_markdown(results, sources)
    (d / "analysis.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
