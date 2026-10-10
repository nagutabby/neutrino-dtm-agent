#!/usr/bin/env python3
"""曲が使う SoundFont の存在確認と解決。

  soundfont.py check <song>          必要な SoundFont を洗い出し、足りなければ「何が必要か」を表示して終了コード 3
  soundfont.py resolve <song> <NN>   トラック spec NN-*.md が使う SoundFont ファイルのパスを出力(無ければ 3)
  soundfont.py list                  登録簿と解決状況の一覧
  soundfont.py presets <id>          その SoundFont のプリセット一覧(bank / program / 名前)。spec の program を選ぶ根拠

足りないとき、エージェントは作業を中断してユーザーに用意してもらう(代わりに探して取得・コミットしない)。
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
from pathlib import Path

import yaml
from common import ROOT, active_keys, load_dotenv, load_specs, soundfont_id_of, track_of

load_dotenv()

REGISTRY = ROOT / "config" / "soundfonts.yaml"
EXTS = {".sf2", ".sf3"}
EXIT_MISSING = 3


def registry() -> dict[str, dict]:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    return data.get("soundfonts") or {}


def sf_dir() -> Path:
    return Path(os.environ.get("SOUNDFONT_DIR") or ROOT / "soundfonts").expanduser()


def find(sf_id: str, entry: dict) -> Path | None:
    for var in (entry.get("env"), "SF_" + sf_id.upper().replace("-", "_")):
        v = os.environ.get(var) if var else None
        if v and Path(v).expanduser().is_file():
            return Path(v).expanduser()
    kws = [str(k).lower() for k in entry.get("keywords") or []]
    anys = [str(k).lower() for k in entry.get("keywords_any") or []]
    if not kws and not anys:
        return None
    d = sf_dir()
    if d.is_dir():
        for p in sorted(d.rglob("*")):
            n = p.name.lower()
            if p.suffix.lower() in EXTS and all(k in n for k in kws) and (not anys or any(k in n for k in anys)):
                return p
    return None


def presets_of(path: Path) -> list[tuple[int, int, str]]:
    """SoundFont(sf2/sf3)の phdr チャンクからプリセット (bank, program, name) を読む。"""
    data = path.read_bytes()
    j = data.find(b"phdr")
    if j < 0:
        return []
    size = struct.unpack("<I", data[j + 4 : j + 8])[0]
    out = []
    for k in range(size // 38 - 1):  # 最後は終端レコード(EOP)
        r = data[j + 8 + k * 38 : j + 8 + (k + 1) * 38]
        prog, bank = struct.unpack("<HH", r[20:24])
        out.append((bank, prog, r[:20].split(b"\0")[0].decode("latin1")))
    return sorted(out)


def required(song: str) -> dict[str, list[str]]:
    """SoundFont ID -> 使うトラック(spec キー)。ボーカル(NEUTRINO で合成)は SoundFont を使わない。"""
    specs = load_specs(song)
    need: dict[str, list[str]] = {}
    for key in active_keys(specs):
        t = track_of(specs, key)
        if t and t != "vocal":
            need.setdefault(soundfont_id_of(specs, key), []).append(key)
    return need


def cmd_check(song: str) -> int:
    reg = registry()
    need = required(song)
    unknown = [i for i in need if i not in reg]
    if unknown:
        print(f"[エラー] 登録簿 config/soundfonts.yaml にない SoundFont ID: {', '.join(unknown)}")
        print("  → ID・name・need(どんな音源か)を登録簿に追記してから再実行してください。")
        return 2
    missing = []
    for sf_id, keys in need.items():
        p = find(sf_id, reg[sf_id])
        if p:
            print(f"  ✔ {sf_id}: {p}  (用途: {', '.join(keys)})")
        else:
            missing.append((sf_id, keys))
    if not missing:
        print("必要な SoundFont はすべて揃っています。")
        return 0
    print()
    print("■ 足りない SoundFont があります。ここで作業を中断します。")
    for sf_id, keys in missing:
        e = reg[sf_id]
        print(f"\n  ✘ {sf_id}: {e['name']}")
        print(f"    必要な内容: {' '.join(str(e['need']).split())}")
        print(f"    使うトラック: {', '.join(keys)}")
        hint = e.get("keywords") or e.get("keywords_any") or []
        word = "と" if e.get("keywords") else "か"
        print(f"    置き場所: {sf_dir()}/ に .sf2 / .sf3 を置く(ファイル名に {word.join(map(repr, hint))} を含める)")
        print(f"    または .env に SF_{sf_id.upper().replace('-', '_')}=<ファイルのパス> を設定")
    print("\n用意できたら教えてください。再確認(soundfont.py check)後に続きから再開します。")
    print("(SoundFont は配布元のライセンスを確認してご自身で入手してください。リポジトリにはコミットしません)")
    return EXIT_MISSING


def cmd_resolve(song: str, num: str) -> int:
    specs = load_specs(song)
    key = next((k for k in specs if k.startswith(f"{num}-")), None)
    if not key:
        print(f"[エラー] spec {num}-*.md がありません", file=sys.stderr)
        return 2
    sf_id = soundfont_id_of(specs, key)
    reg = registry()
    if sf_id not in reg:
        print(f"[エラー] 登録簿にない SoundFont ID: {sf_id}", file=sys.stderr)
        return 2
    p = find(sf_id, reg[sf_id])
    if not p:
        print(f"[エラー] SoundFont '{sf_id}'({reg[sf_id]['name']})が見つかりません。"
              f"`uv run scripts/soundfont.py check {song}` で必要な内容を確認し、ユーザーに用意してもらってください",
              file=sys.stderr)
        return EXIT_MISSING
    print(p)
    return 0


def cmd_list() -> int:
    for sf_id, e in registry().items():
        p = find(sf_id, e)
        print(f" {'✔' if p else '✘'} {sf_id:<10} {e['name']}" + (f"  → {p}" if p else ""))
    return 0


def cmd_presets(sf_id: str) -> int:
    reg = registry()
    if sf_id not in reg:
        print(f"[エラー] 登録簿にない SoundFont ID: {sf_id}", file=sys.stderr)
        return 2
    p = find(sf_id, reg[sf_id])
    if not p:
        print(f"[エラー] SoundFont '{sf_id}' が見つかりません(check で必要な内容を確認)", file=sys.stderr)
        return EXIT_MISSING
    print(f"■ {sf_id}: {p}")
    for bank, prog, name in presets_of(p):
        print(f"  bank {bank:>3} program {prog:>3}  {name}" + ("  (ドラムキット)" if bank == 128 else ""))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").add_argument("song")
    r = sub.add_parser("resolve")
    r.add_argument("song")
    r.add_argument("num")
    sub.add_parser("list")
    sub.add_parser("presets").add_argument("id")
    a = ap.parse_args()
    if a.cmd == "check":
        sys.exit(cmd_check(a.song))
    if a.cmd == "resolve":
        sys.exit(cmd_resolve(a.song, a.num))
    if a.cmd == "presets":
        sys.exit(cmd_presets(a.id))
    sys.exit(cmd_list())


if __name__ == "__main__":
    main()
