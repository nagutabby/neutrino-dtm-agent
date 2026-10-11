#!/usr/bin/env python3
"""フレーズ仕様(JSON)から MusicXML を作り、NEUTRINO で歌声(wav + f0)を合成する。

  neutrino_sing.py <phrase.json> [--model MERROW] [--dry-run]

phrase.json の例(拍子は 4/4 固定。音符は小節をまたがない):
  {"bpm": 130, "notes": [["お", "C5", 1.5], ["な", "Bb4", 0.5], ["", "", 1.0]]}
  各要素は [歌詞(ひらがな1音), 音名, 長さ(拍)]。音名が空なら休符。

出力は work/vocals/<phrase名>_vN.{musicxml,wav,f0,...}(既存は上書きせず版を進める)。
~/neutrino(環境変数 NEUTRINO_DIR)は読み取り専用のまま使い、書き込みはしない。
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from common import WORK, load_dotenv

VOCALS = WORK / "vocals"
DIVISIONS = 4  # 四分音符 = 4 → 16 分音符まで表せる
TYPES = {  # 拍数 -> (type, ドット)
    4.0: ("whole", 0), 3.0: ("half", 1), 2.0: ("half", 0), 1.5: ("quarter", 1),
    1.0: ("quarter", 0), 0.75: ("eighth", 1), 0.5: ("eighth", 0), 0.25: ("16th", 0),
}
STEPS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def parse_pitch(name: str) -> tuple[str, int, int]:
    m = re.fullmatch(r"([A-G])([#b]?)(\d)", name)
    if not m:
        raise ValueError(f"音名が読めません: {name!r}(例: C5, Bb4, F#3)")
    return m.group(1), {"": 0, "#": 1, "b": -1}[m.group(2)], int(m.group(3))


def note_xml(lyric: str, pitch: str, beats: float) -> str:
    if beats not in TYPES:
        raise ValueError(f"対応していない長さ: {beats} 拍(使える値: {sorted(TYPES)})")
    typ, dots = TYPES[beats]
    dur = int(beats * DIVISIONS)
    tail = f"<duration>{dur}</duration><voice>1</voice><type>{typ}</type>" + "<dot/>" * dots
    if not pitch:
        return f"<note><rest/>{tail}</note>"
    step, alter, octave = parse_pitch(pitch)
    alt = f"<alter>{alter}</alter>" if alter else ""
    ly = f"<lyric number=\"1\"><syllabic>single</syllabic><text>{escape(lyric)}</text></lyric>"
    return f"<note><pitch><step>{step}</step>{alt}<octave>{octave}</octave></pitch>{tail}{ly}</note>"


def build_musicxml(spec: dict, title: str) -> str:
    bpm = spec["bpm"]
    measures: list[list[str]] = [[]]
    filled = 0.0
    for lyric, pitch, beats in spec["notes"]:
        if filled + beats > 4.0 + 1e-9:
            raise ValueError(f"音符が小節をまたぎます(小節{len(measures)}、{filled}+{beats} 拍)")
        measures[-1].append(note_xml(lyric, pitch, float(beats)))
        filled += beats
        if abs(filled - 4.0) < 1e-9:
            measures.append([])
            filled = 0.0
    if filled:
        raise ValueError(f"最後の小節が 4 拍になっていません(あと {4.0 - filled} 拍)")
    measures = [m for m in measures if m]
    body = []
    for i, notes in enumerate(measures, 1):
        attrs = ""
        if i == 1:
            attrs = (
                f"<attributes><divisions>{DIVISIONS}</divisions><key><fifths>0</fifths></key>"
                "<time><beats>4</beats><beat-type>4</beat-type></time>"
                "<clef><sign>G</sign><line>2</line></clef></attributes>"
                f"<direction placement=\"above\"><direction-type><metronome>"
                f"<beat-unit>quarter</beat-unit><per-minute>{bpm}</per-minute></metronome>"
                f"</direction-type><sound tempo=\"{bpm}\"/></direction>"
            )
        body.append(f"<measure number=\"{i}\">{attrs}{''.join(notes)}</measure>")
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<!DOCTYPE score-partwise PUBLIC \"-//Recordare//DTD MusicXML 3.1 Partwise//EN\" "
        "\"http://www.musicxml.org/dtds/partwise.dtd\">\n"
        "<score-partwise version=\"3.1\"><part-list><score-part id=\"P1\">"
        f"<part-name>{escape(title)}</part-name></score-part></part-list>"
        f"<part id=\"P1\">{''.join(body)}</part></score-partwise>\n"
    )


def next_version(stem: str) -> int:
    used = [int(m.group(1)) for p in VOCALS.glob(f"{stem}_v*.musicxml")
            if (m := re.fullmatch(rf"{re.escape(stem)}_v(\d+)\.musicxml", p.name))]
    return max(used, default=0) + 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("phrase", type=Path)
    ap.add_argument("--model", default="MERROW")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    load_dotenv()

    neutrino = Path(os.environ.get("NEUTRINO_DIR", "~/neutrino")).expanduser()
    mxl2lab, nbin = neutrino / "bin/musicXMLtoLabel", neutrino / "bin/neutrino"
    model = neutrino / "model" / args.model
    for p in (mxl2lab, nbin, model):
        if not p.exists():
            sys.exit(f"見つかりません: {p}(NEUTRINO_DIR を確認)")

    spec = json.loads(args.phrase.read_text(encoding="utf-8"))
    VOCALS.mkdir(parents=True, exist_ok=True)
    stem = args.phrase.stem
    base = VOCALS / f"{stem}_v{next_version(stem)}"
    xml_path = base.with_suffix(".musicxml")
    xml_path.write_text(build_musicxml(spec, stem), encoding="utf-8")
    paths = {k: base.with_suffix(f".{k}") for k in
             ("full.lab", "mono.lab", "timing.lab", "f0", "melspec", "wav")}
    cmds = [
        [str(mxl2lab), str(xml_path), str(paths["full.lab"]), str(paths["mono.lab"])],
        [str(nbin), str(paths["full.lab"]), str(paths["timing.lab"]), str(paths["f0"]),
         str(paths["melspec"]), str(paths["wav"]), f"{model}/",
         "-n", "4", "-k", "0", "-f", "0", "-s", "48000", "-b", "16", "-t"],
    ]
    env = {**os.environ, "DYLD_LIBRARY_PATH": f"{neutrino / 'bin'}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"}
    for cmd in cmds:
        print("+", " ".join(cmd))
        if not args.dry_run:
            r = subprocess.run(cmd, env=env, cwd=neutrino)  # settings/ を相対で読むため
            if r.returncode != 0:
                sys.exit(f"失敗しました(終了コード {r.returncode}): {Path(cmd[0]).name}")
    print(f"出力: {paths['wav']}" if not args.dry_run else "(dry-run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
