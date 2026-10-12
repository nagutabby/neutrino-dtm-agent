#!/usr/bin/env python3
"""Sonic Pi を呼ぶ共通部分と、内蔵シンセ・FX の一覧。

  sonicpi.py synths [名前]    内蔵シンセの一覧(名前を渡すとその引数)
  sonicpi.py fx [名前]        内蔵 FX の一覧(名前を渡すとその引数)
  sonicpi.py samples [グループ]  内蔵サンプルの一覧(グループは bass / bd / drum / elec / hat / loop / perc / sn など。名前の頭の部分)
  sonicpi.py chords | scales  chord / scale に使える名前の一覧
  sonicpi.py dump-info        Sonic Pi.app から config/sonicpi_catalog.json(シンセ・FX・サンプル・コード・スケール)を作り直す(バージョンアップ後など)

wav の録音は record()。Sonic Pi にはゼロから wav を書く非リアルタイム(NRT)の仕組みがないため、
ヘッドレスで起動して実時間で録音する(曲の長さ分の時間がかかる。録音中は実際に音が鳴る)。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from common import ROOT, load_dotenv

load_dotenv()

APP = Path(os.environ.get("SONIC_PI_APP", "/Applications/Sonic Pi.app"))
RECORD_RB = ROOT / "scripts" / "sonicpi_record.rb"
INFO_RB = ROOT / "scripts" / "sonicpi_info.rb"
CATALOG_PATH = ROOT / "config" / "sonicpi_catalog.json"
BOOT_OVERHEAD = 20  # 起動・保存の待ち時間の目安(秒)。タイムアウト計算用


def info() -> dict:
    """Sonic Pi 内蔵の {synths: {名前: [引数]}, fx: {...}, samples: {グループ: [名前]}, chords: [名前], scales: [名前]}。"""
    if not CATALOG_PATH.is_file():
        sys.exit("[エラー] config/sonicpi_catalog.json がありません(`uv run scripts/sonicpi.py dump-info` で作る。Sonic Pi が必要)")
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def find_app() -> Path | None:
    boot = APP / "Contents/Resources/app/server/ruby/bin/headless_boot.rb"
    return APP if boot.is_file() else None


def find_ruby() -> str | None:
    for c in (os.environ.get("SONIC_PI_RUBY"), shutil.which("ruby")):
        if c and Path(c).is_file() and os.access(c, os.X_OK):
            return c
    return None


def record(code: str, seconds: float, target: Path) -> str:
    """Sonic Pi のコードを実行して seconds 秒録音し、target に 24bit wav で書く。失敗は SystemExit。戻り値はログ。"""
    app, ruby = find_app(), find_ruby()
    if not app:
        sys.exit("[エラー] Sonic Pi が見つかりません。入れてください(brew install --cask sonic-pi)。"
                 "標準外の場所なら .env に SONIC_PI_APP=/path/to/'Sonic Pi.app' を設定")
    if not ruby:
        sys.exit("[エラー] ruby が見つかりません(.env の SONIC_PI_RUBY か PATH)")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        rb = Path(td) / "song.rb"
        rb.write_text(code, encoding="utf-8")
        env = {**os.environ, "SONIC_PI_APP": str(app)}
        # 録音用に起動した daemon・エンジンごと止められるよう、専用のプロセスグループで動かす
        proc = subprocess.Popen([ruby, str(RECORD_RB), str(target), f"{seconds:.3f}", str(rb)], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, env=env, start_new_session=True)
        try:
            log, _ = proc.communicate(timeout=seconds + BOOT_OVERHEAD + 60)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.communicate()
            sys.exit("[エラー] Sonic Pi の録音が終わりませんでした(別の Sonic Pi が動いていないか確認)")
    if proc.returncode not in (0, 2) or not target.is_file():
        tail = "\n".join(log.strip().splitlines()[-15:])
        sys.exit(f"[エラー] 録音に失敗しました(終了コード {proc.returncode})。Sonic Pi の出力末尾:\n{tail}")
    if proc.returncode == 2:  # 録音はできたが Sonic Pi がエラーを報告した(例: 不正な引数)
        errs = "\n".join(ln for ln in log.splitlines() if "ERROR" in ln or "SYNTAX" in ln)
        sys.exit(f"[エラー] Sonic Pi がエラーを報告しました(音は信用できません):\n{errs}")
    return log


def cmd_dump_info() -> int:
    ruby = find_ruby()
    if not (find_app() and ruby):
        print("[エラー] Sonic Pi と ruby が必要です", file=sys.stderr)
        return 1
    r = subprocess.run([ruby, str(INFO_RB)], capture_output=True, text=True, env={**os.environ, "SONIC_PI_APP": str(APP)})
    if r.returncode != 0 or not r.stdout.strip():
        print(r.stderr or "[エラー] 取得できませんでした", file=sys.stderr)
        return 1
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(r.stdout, encoding="utf-8")
    print(f"更新: {CATALOG_PATH.relative_to(ROOT)}")
    return 0


def cmd_list(kind: str, name: str | None) -> int:
    d = info()[kind]
    if name:
        if name not in d:
            print(f"[エラー] {kind} に '{name}' はありません", file=sys.stderr)
            return 2
        print(f"{name}: " + " ".join(a for a in d[name] if not a.endswith(("_slide", "_slide_shape", "_slide_curve"))))
    else:
        print(" ".join(d))
    return 0


def cmd_sounds(kind: str, name: str | None) -> int:
    d = info()
    if kind != "samples":
        print(" ".join(d[kind]))
    elif name:
        if name not in d["samples"]:
            print(f"[エラー] グループ '{name}' はありません(あるグループ: {' '.join(d['samples'])})", file=sys.stderr)
            return 2
        print(" ".join(d["samples"][name]))
    else:
        print("\n".join(f"{g}: {len(v)} 個 ({' '.join(v[:3])} …)" for g, v in d["samples"].items()))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for k in ("synths", "fx"):
        sub.add_parser(k).add_argument("name", nargs="?")
    sub.add_parser("samples").add_argument("name", nargs="?")
    sub.add_parser("chords")
    sub.add_parser("scales")
    sub.add_parser("dump-info")
    a = ap.parse_args()
    if a.cmd == "dump-info":
        sys.exit(cmd_dump_info())
    sys.exit(cmd_sounds(a.cmd, getattr(a, "name", None)) if a.cmd in ("samples", "chords", "scales") else cmd_list(a.cmd, a.name))


if __name__ == "__main__":
    main()
