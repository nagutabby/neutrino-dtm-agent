#!/usr/bin/env bash
# 使い方: ab_render.sh <song> <musicxml-basename> "<model:styleShift:transpose> ..." [--dry-run]
#   例: ab_render.sh demo vocal_v1 "MERROW:0:0 MERROW:2:0 NAKUMO:0:0"
# 設定違いを別名で合成し、聴き比べ用に output/ へ並べる(耳の学習用)。
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SONG="${1:-}"; BASE="${2:-}"; VARIANTS="${3:-}"
[ -n "$SONG" ] && [ -n "$BASE" ] && [ -n "$VARIANTS" ] || die "使い方: ab_render.sh <song> <basename> \"M:k:f ...\" [--dry-run]"
EXTRA=()
[ "${4:-}" = "--dry-run" ] && EXTRA=(--dry-run)
D="$(song_dir "$SONG")"
for v in $VARIANTS; do
  IFS=: read -r model k f <<<"$v"
  [ -n "$model" ] && [ -n "${k:-}" ] && [ -n "${f:-}" ] || die "形式は model:styleShift:transpose です: $v"
  name="${BASE}__${model}_k${k}_f${f}"
  if [ "${EXTRA[0]:-}" != "--dry-run" ]; then
    cp -n "$D/musicxml/$BASE.musicxml" "$D/musicxml/$name.musicxml"
  else
    echo "[dry-run] cp $BASE.musicxml $name.musicxml(synth.sh の検査は実ファイルが必要なため省略)"
    continue
  fi
  STYLE_SHIFT="$k" TRANSPOSE="$f" "$ROOT/scripts/synth.sh" "$SONG" "$name" "$model" ${EXTRA[@]+"${EXTRA[@]}"}
done
