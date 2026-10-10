#!/usr/bin/env python3
"""参考曲から「雰囲気」を抽象的な特徴(テンポ・キー・コード進行・音域・密度・明るさ・盛り上がり)に要約する。

使い方: reference_analyze.py <song> <video-id>
  入力: reference/<id>/audio.wav(+ transcription.mid があれば音域・密度に利用)
  出力: reference/<id>/analysis.json と analysis.md(AI がユーザーと曲のイメージを話すための材料)
旋律・歌詞・音符列は出力しない。推定値は目安であり、spec を決めるのはユーザー。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from common import require_project, safe_ref_dir
from explain_midi import MAJOR, MINOR, NAMES

ROMAN = ["I", "♭II", "II", "♭III", "III", "IV", "♯IV", "V", "♭VI", "VI", "♭VII", "VII"]
MAX_SECONDS = 600


def _templates():
    import numpy as np

    out = {}
    for root in range(12):
        for q, third in (("", 4), ("m", 3)):
            v = np.zeros(12)
            v[[root, (root + third) % 12, (root + 7) % 12]] = 1.0
            out[(root, q)] = v / np.linalg.norm(v)
    return out


def key_scores(chroma_mean) -> dict[tuple[int, str], float]:
    import numpy as np

    out = {}
    for tonic in range(12):
        for prof, mode in ((MAJOR, "長調"), (MINOR, "短調")):
            rot = np.array([prof[(i - tonic) % 12] for i in range(12)])
            out[(tonic, mode)] = float(np.corrcoef(chroma_mean, rot)[0, 1])
    return out


def estimate_key(chroma_mean) -> tuple[int, str, float]:
    sc = key_scores(chroma_mean)
    (tonic, mode), conf = max(sc.items(), key=lambda kv: kv[1])
    return tonic, mode, conf


# キーの音階に収まるコード(根音からの半音数 -> 許す質)。"5"(3 度不明)はどちらでも可
DIATONIC = {
    "長調": {0: "", 2: "m", 4: "m", 5: "", 7: "", 9: "m"},
    "短調": {0: "m", 3: "", 5: "m", 7: "m", 8: "", 10: ""},
}


def diatonic_fit(chords: list[tuple[int, str]], tonic: int, mode: str) -> float:
    if not chords:
        return 0.0
    ok = 0
    for root, q in chords:
        want = DIATONIC[mode].get((root - tonic) % 12)
        if want is not None and (
            q == "5" or q == want or (mode == "短調" and (root - tonic) % 12 == 7)
        ):
            ok += 1
    return ok / len(chords)


def roman(root: int, q: str, ref_tonic: int) -> str:
    r = ROMAN[(root - ref_tonic) % 12]
    return r.lower() if q == "m" else r + ("5" if q == "5" else "")


def tempo_word(bpm: float) -> str:
    return "ゆったり" if bpm < 90 else "中くらい" if bpm < 115 else "軽快" if bpm < 140 else "速い"


def _load(path, sr=22050):
    import librosa

    return librosa.load(str(path), sr=sr, mono=True, duration=MAX_SECONDS)[0]


def analyze(ref: Path, use_stems: bool = True) -> dict:
    import librosa
    import numpy as np

    sr = 22050
    y = _load(ref / "audio.wav")
    dur = len(y) / sr
    stems = ref / "stems"
    ALL = ("drums", "bass", "other", "vocals", "guitar", "piano")
    parts = {p: _load(stems / f"{p}.wav") for p in ALL if (stems / f"{p}.wav").exists()}
    separated = use_stems and {"bass", "other"} <= parts.keys()
    # 分離できていれば、コード・キーは伴奏(bass + other + guitar + piano)から、リズムは drums から推定する
    n = min(len(v) for v in parts.values()) if separated else 0
    harm_names = [p for p in ("other", "guitar", "piano") if p in parts] if separated else []
    y_chords = (
        sum(parts[p][:n] for p in harm_names) if separated else y
    )  # 和音を担う楽器(bass を除く)
    y_harm = parts["bass"][:n] + y_chords if separated else y
    y_rhythm = parts["drums"] if separated and "drums" in parts else y
    tempo, beats = librosa.beat.beat_track(y=y_rhythm, sr=sr)
    bpm = float(np.atleast_1d(tempo)[0])
    y_key = y_chords
    chroma = librosa.feature.chroma_cqt(y=y_key, sr=sr)
    chroma_key_mean = chroma.mean(axis=1)
    tonic, mode, conf = estimate_key(chroma_key_mean)
    # コード推定は旋律に引っ張られにくい低〜中域(C2〜B4)のクロマを使う
    chroma_low = librosa.feature.chroma_cqt(
        y=y_harm, sr=sr, fmin=librosa.note_to_hz("C2"), n_octaves=3
    )
    ref_tonic = tonic if mode == "長調" else (tonic + 3) % 12  # 短調は平行長調を基準にローマ数字化

    # 小節(4拍)ごとのコード推定
    bar_chords: list[str] = []
    if len(beats) >= 8:
        sync = librosa.util.sync(chroma_low, beats, aggregate=np.median)
        if separated:
            # 根音はベース、長調/短調は和音パート(other)の 3 度の強さで決める。
            # ベースの倍音(5 倍音=長 3 度)に引っ張られず、旋律にも惹かれにくい。
            fl = librosa.note_to_hz("C2")
            c_bass = librosa.util.sync(
                librosa.feature.chroma_cqt(
                    y=parts["bass"][:n],
                    sr=sr,
                    fmin=librosa.note_to_hz("C1"),
                    n_octaves=4,
                    bins_per_octave=36,
                ),
                beats,
                aggregate=np.median,
            )
            c_oth = librosa.util.sync(
                librosa.feature.chroma_cqt(y=y_chords, sr=sr, fmin=fl, n_octaves=3),
                beats,
                aggregate=np.median,
            )
        tpl = _templates()
        for i in range(0, sync.shape[1] - 3, 4):
            v = sync[:, i : i + 4].mean(axis=1)
            if np.linalg.norm(v) < 1e-6:
                continue
            if separated and c_bass[:, i : i + 4].mean() > 1e-3:
                root = int(np.argmax(c_bass[:, i : i + 4].mean(axis=1)))
                o = c_oth[:, i : i + 4].mean(axis=1)
                m3, M3 = o[(root + 3) % 12], o[(root + 4) % 12]
                # 3 度の差が小さいときは長/短を断定せず "5"(3 度不明)にする
                q = "5" if abs(m3 - M3) < 0.05 * max(m3 + M3, 1e-9) else ("m" if m3 > M3 else "")
            else:
                v = v / np.linalg.norm(v)
                (root, q), _ = max(tpl.items(), key=lambda kv: float(v @ kv[1]))
            bar_chords.append(f"{NAMES[root]}{q}|{roman(root, q, ref_tonic)}")
    # コード列がキーの音階に収まる割合も加味して、キー(長調/短調)を決め直す
    parsed = [
        (
            NAMES.index(c.split("|")[0].rstrip("m5")),
            "m"
            if c.split("|")[0].endswith("m")
            else ("5" if c.split("|")[0].endswith("5") else ""),
        )
        for c in bar_chords
    ]
    if parsed:
        sc = key_scores(chroma_key_mean)
        (tonic, mode), _ = max(
            sc.items(), key=lambda kv: diatonic_fit(parsed, *kv[0]) + 0.5 * kv[1]
        )
        conf = sc[(tonic, mode)]
        ref_tonic = tonic if mode == "長調" else (tonic + 3) % 12
        bar_chords = [
            f"{c.split('|')[0]}|{roman(*p, ref_tonic)}"
            for c, p in zip(bar_chords, parsed, strict=True)
        ]
        res_fit = round(diatonic_fit(parsed, tonic, mode), 2)
    else:
        res_fit = None
    names = [c.split("|")[0] for c in bar_chords]
    romans = [c.split("|")[1] for c in bar_chords]
    top = Counter(romans).most_common(4)
    loop4 = Counter(tuple(romans[i : i + 4]) for i in range(0, max(len(romans) - 3, 0), 4))
    loop = loop4.most_common(1)[0] if loop4 else None

    rms = librosa.feature.rms(y=y)[0]
    seg = np.array_split(rms, 8)
    energy = [float(s.mean()) for s in seg]
    emax = max(energy) or 1.0
    energy = [round(e / emax, 2) for e in energy]
    centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr)[0].mean())
    onsets = librosa.onset.onset_detect(y=y_rhythm, sr=sr)
    onset_rate = len(onsets) / dur if dur else 0.0

    res: dict = {
        "duration_sec": round(dur, 1),
        "tempo_bpm": round(bpm, 1),
        "key": f"{NAMES[tonic]} {mode}",
        "key_confidence": round(conf, 2),
        "chords_in_key_ratio": res_fit,
        "chords_per_bar_head": names[:16],
        "roman_per_bar_head": romans[:16],
        "ambiguous_chords": round(
            sum(c.split("|")[0].endswith("5") for c in bar_chords) / len(bar_chords), 2
        )
        if bar_chords
        else 0,
        "common_roman": [[r, n] for r, n in top],
        "loop_4bars": [list(loop[0]), loop[1]] if loop else None,
        "energy_by_eighth": energy,
        "brightness_hz": round(centroid),
        "onsets_per_sec": round(onset_rate, 2),
    }
    res["separated"] = separated
    if separated:
        tot = sum(float(librosa.feature.rms(y=v)[0].mean()) for v in parts.values()) or 1.0
        res["part_balance"] = {
            k: round(float(librosa.feature.rms(y=v)[0].mean()) / tot, 2) for k, v in parts.items()
        }
    tr = ref / "transcription.mid"
    if tr.exists():
        res["transcribed"] = summarize_midi(tr, dur)
    return res


GM_FAMILIES = [
    "ピアノ", "音程打楽器", "オルガン", "ギター", "ベース", "弦", "アンサンブル", "ブラス",
    "リード", "パイプ", "シンセリード", "シンセパッド", "シンセ効果", "民族楽器", "打楽器", "効果音",
]  # fmt: skip


def summarize_midi(path: Path, dur: float) -> dict:
    """楽器(チャンネル)ごとに音域・密度を要約する。音符列は出さない。"""
    import mido

    mid = mido.MidiFile(path)
    prog: dict[int, int] = {}
    pitches: dict[int, list[int]] = {}
    for track in mid.tracks:
        for msg in track:
            if msg.type == "program_change":
                prog[msg.channel] = msg.program
            elif msg.type == "note_on" and msg.velocity > 0:
                pitches.setdefault(msg.channel, []).append(msg.note)
    out: dict[str, dict] = {}
    for ch, ps in sorted(pitches.items()):
        ps.sort()
        label = "ドラム" if ch == 9 else GM_FAMILIES[prog.get(ch, 0) // 8]
        key = label if label not in out else f"{label}#{ch}"
        out[key] = {
            "notes": len(ps),
            "notes_per_sec": round(len(ps) / dur, 2) if dur else 0,
            "register": None if ch == 9 else [ps[int(len(ps) * 0.05)], ps[int(len(ps) * 0.95)]],
        }
    return out


def mood_hypotheses(r: dict) -> list[str]:
    out = []
    bpm = r["tempo_bpm"]
    out.append(
        f"テンポ {bpm:g} BPM → {tempo_word(bpm)}。半分/倍に取り違えている可能性があるので、聴いた感覚と合うか確認する。"
    )
    out.append(
        f"キー {r['key']} → {'明るい響きが土台' if '長' in r['key'] else '切ない・陰りのある響きが土台'}"
        f"(確信度 {r['key_confidence']}。低いと転調や曖昧さあり)。"
    )
    e = r["energy_by_eighth"]
    shape = (
        "後半に向けて盛り上がる"
        if e[-3:] and sum(e[-3:]) / 3 > sum(e[:3]) / 3 + 0.15
        else (
            "前半が強く後半は落ち着く"
            if sum(e[:3]) / 3 > sum(e[-3:]) / 3 + 0.15
            else "全体に起伏は穏やか"
        )
    )
    out.append(f"盛り上がりの形: {shape}(8 分割の相対音量 {e})。")
    out.append(
        f"音の明るさ(スペクトル重心)約 {r['brightness_hz']} Hz → "
        f"{'きらびやか' if r['brightness_hz'] > 3000 else 'やわらかい' if r['brightness_hz'] < 1800 else 'ほどよい明るさ'}。"
    )
    out.append(
        f"音の出だし {r['onsets_per_sec']} 回/秒 → {'細かく忙しい' if r['onsets_per_sec'] > 4 else 'ゆったり' if r['onsets_per_sec'] < 2 else '標準的'}な刻み。"
    )
    return out


def to_markdown(r: dict, src: dict) -> str:
    lines = [f"# 参考曲の分析: {src.get('title', '(不明)')}", ""]
    lines += [
        f"- 出典: {src.get('webpage_url', '(不明)')}(私的な分析用。音声・MIDI は保存のみで公開しない)",
        "",
    ]
    lines += [
        "## 数値",
        "",
        f"- 長さ {r['duration_sec']} 秒 / テンポ {r['tempo_bpm']} BPM / キー {r['key']}",
    ]
    if r["loop_4bars"]:
        lines.append(
            f"- よく出る4小節の進行(ローマ数字、短調は平行長調基準): {' - '.join(r['loop_4bars'][0])}({r['loop_4bars'][1]}回)"
        )
    lines.append(f"- 先頭16小節のコード(推定): {' / '.join(r['chords_per_bar_head'])}")
    lines.append("- よく使われるコード機能: " + "、".join(f"{k}×{v}" for k, v in r["common_roman"]))
    if r.get("part_balance"):
        names = {
            "drums": "ドラム",
            "bass": "ベース",
            "other": "その他",
            "vocals": "ボーカル",
            "guitar": "ギター",
            "piano": "ピアノ",
        }
        lines.append(
            "- パートの音量バランス(分離後): "
            + "、".join(f"{names[k]} {v:.0%}" for k, v in r["part_balance"].items())
        )
    if r.get("transcribed"):
        from common import midi_to_note

        for part, t in r["transcribed"].items():
            if t["register"] is None:
                lines.append(f"- 書き起こし MIDI [{part}] の打点: {t['notes_per_sec']} 回/秒(目安)")
                continue
            lo, hi = t["register"]
            lines.append(
                f"- 書き起こし MIDI [{part}] の音域(5〜95%): {midi_to_note(lo)}〜{midi_to_note(hi)}、{t['notes_per_sec']} 音/秒(目安)"
            )
    lines.append(
        f"- 解析方法: {'音源分離あり(コード・キーは伴奏、リズムはドラムから推定)' if r['separated'] else '音源分離なし(ミックス全体から推定。精度は低め)'}"
    )
    lines += ["", "## 雰囲気の仮説(推定。ユーザーの耳で確認する)", ""]
    lines += [f"- {h}" for h in mood_hypotheses(r)]
    lines += ["", "## この曲づくりへの示唆(候補。決めるのはユーザー)", ""]
    lines += [
        f"- 01-structure: テンポ {r['tempo_bpm']:g} 前後、キー {r['key']} が近い雰囲気。",
        "- 02-harmony: 上の進行の「機能の並び」(例: vi→IV→I→V)を参考に、自分のキーで別の並びを作る。",
        "- 03〜06: 盛り上がりの形と刻みの細かさを、ドラム密度・ベロシティ・音域の設計に反映。",
        "- 旋律・歌詞・リズムパターンをそのまま写さない(複製ではなく『雰囲気の言語化』が目的)。",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("song")
    ap.add_argument("ref_id")
    ap.add_argument(
        "--no-stems", action="store_true", help="分離結果があっても使わない(精度比較用)"
    )
    a = ap.parse_args()
    ref = safe_ref_dir(require_project(a.song), a.ref_id)
    audio = ref / "audio.wav"
    if not audio.exists():
        sys.exit(f"音声がありません: {audio}(reference_fetch.sh で取得)")
    r = analyze(ref, use_stems=not a.no_stems)
    src_p = ref / "source.json"
    src = json.loads(src_p.read_text(encoding="utf-8").splitlines()[0]) if src_p.exists() else {}
    (ref / "analysis.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ref / "analysis.md").write_text(to_markdown(r, src), encoding="utf-8")
    print((ref / "analysis.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
