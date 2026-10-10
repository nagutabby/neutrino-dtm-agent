#!/usr/bin/env bash
# 使い方: reference_run.sh <song> <youtube-url> [--dry-run]
# 参考曲の YouTube 取得 → 音源分離 → 雰囲気の分析 を順に実行する(MIDI への書き起こし・MIDI 検索はしない)。
# 例(参考曲3つ以上)が揃ったら reference_summary.py <song> で共通点をまとめる。
# 音源分離を省く場合は REF_SEPARATE=0(精度は下がる)。
# 結果: projects/<song>/reference/<video-id>/analysis.md
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SONG="${1:-}"; URL="${2:-}"
[ -n "$SONG" ] && [ -n "$URL" ] || die "使い方: reference_run.sh <song> <youtube-url> [--dry-run]"
shift 2
DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    *) die "不明な引数: $1" ;;
  esac
  shift
done
if [ "$DRY" = 1 ]; then
  "$ROOT/scripts/reference_fetch.sh" "$SONG" "$URL" --dry-run
  echo "[dry-run] 続けて reference_separate.py → reference_analyze.py を実行します"
  exit 0
fi

ID="$("$ROOT/scripts/reference_fetch.sh" "$SONG" "$URL" | tee /dev/stderr | tail -n1)"
cd "$ROOT"
[ "${REF_SEPARATE:-1}" = 0 ] || uv run --group reference scripts/reference_separate.py "$SONG" "$ID"
uv run --group reference scripts/reference_analyze.py "$SONG" "$ID"
echo "分析結果: projects/$SONG/reference/$ID/analysis.md"
