#!/usr/bin/env bash
# 使い方: reference_run.sh <song> <youtube-url> [--role seed|similar] [--dry-run]
# 参考曲の YouTube 取得 → 音源分離 → 雰囲気の分析 を順に実行する(MIDI への書き起こし・MIDI 検索はしない)。
# --role: seed=ユーザーの参考曲(既定) / similar=Web 検索で見つけた類似曲(few-shot の例)。reference/<id>/role に記録。
# 例が揃ったら reference_summary.py <song> で共通点をまとめる。
# 音源分離を省く場合は REF_SEPARATE=0(精度は下がる)。
# 結果: projects/<song>/reference/<video-id>/analysis.md
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SONG="${1:-}"; URL="${2:-}"
[ -n "$SONG" ] && [ -n "$URL" ] || die "使い方: reference_run.sh <song> <youtube-url> [--role seed|similar] [--dry-run]"
shift 2
ROLE=seed; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --role) shift; ROLE="${1:-}" ;;
    *) die "不明な引数: $1" ;;
  esac
  shift
done
case "$ROLE" in seed|similar) ;; *) die "--role は seed か similar: '$ROLE'" ;; esac
if [ "$DRY" = 1 ]; then
  "$ROOT/scripts/reference_fetch.sh" "$SONG" "$URL" --dry-run
  echo "[dry-run] 続けて reference_separate.py → reference_analyze.py を実行します"
  exit 0
fi

ID="$("$ROOT/scripts/reference_fetch.sh" "$SONG" "$URL" | tee /dev/stderr | tail -n1)"
cd "$ROOT"
printf '%s\n' "$ROLE" > "$ROOT/projects/$SONG/reference/$ID/role"
[ "${REF_SEPARATE:-1}" = 0 ] || uv run --group reference scripts/reference_separate.py "$SONG" "$ID"
uv run --group reference scripts/reference_analyze.py "$SONG" "$ID"
echo "分析結果: projects/$SONG/reference/$ID/analysis.md(区分: $ROLE)"
