#!/usr/bin/env bash
# 使い方: midi_to_musicxml.sh <in.mid> <out.musicxml> [--dry-run]
# MuseScore 4 CLI で MIDI → MusicXML。歌詞は変換後に lyrics_inject.py で付与する。
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

IN="${1:-}"; OUT="${2:-}"
[ -n "$IN" ] && [ -n "$OUT" ] || die "使い方: midi_to_musicxml.sh <in.mid> <out.musicxml> [--dry-run]"
[ "${3:-}" = "--dry-run" ] && DRY_RUN=1
[ -f "$IN" ] || die "入力がありません: $IN"
[ ! -e "$OUT" ] || die "既に存在します(上書きしません): $OUT"
[ -n "${MUSESCORE_BIN:-}" ] && [ -x "$MUSESCORE_BIN" ] || die "MUSESCORE_BIN が未設定です(.env)"
run "$MUSESCORE_BIN" -o "$OUT" "$IN"
echo "出力: $OUT"
echo "次: uv run scripts/lyrics_inject.py $OUT <lyrics.txt> -o <with_lyrics.musicxml>"
