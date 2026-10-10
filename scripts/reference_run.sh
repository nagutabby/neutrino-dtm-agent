#!/usr/bin/env bash
# 使い方: reference_run.sh <song> <youtube-url> [--dry-run]
# 参考曲の取得 → 音源分離 → MIDI 書き起こし → 雰囲気の分析 を順に実行する。
# 音源分離を省く場合は REF_SEPARATE=0(精度は下がる)。
# 結果: projects/<song>/reference/<video-id>/analysis.md
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SONG="${1:-}"; URL="${2:-}"
[ -n "$SONG" ] && [ -n "$URL" ] || die "使い方: reference_run.sh <song> <youtube-url> [--dry-run]"
if [ "${3:-}" = "--dry-run" ]; then
  "$ROOT/scripts/reference_fetch.sh" "$SONG" "$URL" --dry-run
  echo "[dry-run] 続けて reference_separate.py → reference_to_midi.py → reference_analyze.py を実行します"
  exit 0
fi

ID="$("$ROOT/scripts/reference_fetch.sh" "$SONG" "$URL" | tee /dev/stderr | tail -n1)"
cd "$ROOT"
[ "${REF_SEPARATE:-1}" = 0 ] || uv run --group reference scripts/reference_separate.py "$SONG" "$ID"
uv run --group reference scripts/reference_to_midi.py "$SONG" "$ID"
uv run --group reference scripts/reference_analyze.py "$SONG" "$ID"
echo "分析結果: projects/$SONG/reference/$ID/analysis.md"
