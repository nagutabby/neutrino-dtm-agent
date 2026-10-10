#!/usr/bin/env bash
# 使い方: synth.sh <song> <musicxml-basename> [model] [--dry-run]
#   projects/<song>/musicxml/<basename>.musicxml → label → projects/<song>/output/<basename>.wav
# 引数の既定値は NEUTRINO 同梱の Run.sh と同じ。NEUTRINO_DIR は読み取りのみで書き込まない。
# 環境変数で上書き: NUM_THREADS STYLE_SHIFT TRANSPOSE SAMPLING_RATE BIT_DEPTH
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SONG="${1:-}"; BASE="${2:-}"; MODEL="${3:-MERROW}"
if [ -z "$SONG" ] || [ -z "$BASE" ]; then die "使い方: synth.sh <song> <basename> [model] [--dry-run]"; fi
for a in "$@"; do [ "$a" = "--dry-run" ] && DRY_RUN=1; done
[ "$MODEL" = "--dry-run" ] && MODEL=MERROW
D="$(song_dir "$SONG")"
safe_name "basename" "$BASE"
safe_name "モデル名" "$MODEL"

XML="$D/musicxml/$BASE.musicxml"
[ -f "$XML" ] || die "MusicXML がありません: ${XML#"$ROOT"/}"
[ -d "$NEUTRINO_DIR/model/$MODEL" ] || die "モデルがありません: $NEUTRINO_DIR/model/$MODEL"
for b in neutrino musicXMLtoLabel; do
  [ -f "$NEUTRINO_DIR/bin/$b" ] || die "$NEUTRINO_DIR/bin/$b がありません(NEUTRINO_DIR を確認)"
  [ -x "$NEUTRINO_DIR/bin/$b" ] || die "$b に実行権限がありません。ご自身で実行してください: chmod 755 \"$NEUTRINO_DIR\"/bin/* && xattr -dr com.apple.quarantine \"$NEUTRINO_DIR/bin\""
done

FULL="$D/label/full/$BASE.lab"; MONO="$D/label/mono/$BASE.lab"; TIMING="$D/label/timing/$BASE.lab"
OUT="$D/output/$BASE"
[ ! -e "$OUT.wav" ] || die "既に存在します(上書きしません。別名にするか削除を確認): ${OUT#"$ROOT"/}.wav"

uv run "$ROOT/scripts/musicxml_validate.py" "$XML" || die "MusicXML の検査に失敗しました。直してから再実行してください"

export DYLD_LIBRARY_PATH="$NEUTRINO_DIR/bin:${DYLD_LIBRARY_PATH:-}"
echo "$(date +%M:%S) : MusicXMLtoLabel"
# NEUTRINO は settings/dic を相対パスで読むため、実行時のカレントを NEUTRINO_DIR にする(読み取りのみ。出力は絶対パスで projects/ へ)
cd "$NEUTRINO_DIR"
run "$NEUTRINO_DIR/bin/musicXMLtoLabel" "$XML" "$FULL" "$MONO"
echo "$(date +%M:%S) : NEUTRINO (model=$MODEL)"
run "$NEUTRINO_DIR/bin/neutrino" "$FULL" "$TIMING" "$OUT.f0" "$OUT.melspec" "$OUT.wav" \
  "$NEUTRINO_DIR/model/$MODEL/" \
  -n "${NUM_THREADS:-4}" -k "${STYLE_SHIFT:-0}" -f "${TRANSPOSE:-0}" \
  -s "${SAMPLING_RATE:-48000}" -b "${BIT_DEPTH:-16}" -t
echo "$(date +%M:%S) : END → ${OUT#"$ROOT"/}.wav"
