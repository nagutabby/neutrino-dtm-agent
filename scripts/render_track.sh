#!/usr/bin/env bash
# 使い方: render_track.sh <song> <track-midi-name 例: 04_bass_v1> [--dry-run]
# tracks/<name>.mid を Sonic Pi の内蔵シンセでゼロから合成(実時間録音)し、stems/<name>.wav にする(試聴用)。音色はトラック spec の params.patch で決まる
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SONG="${1:-}"; NAME="${2:-}"
[ -n "$SONG" ] && [ -n "$NAME" ] || die "使い方: render_track.sh <song> <name> [--dry-run]"
ARGS=()
[ "${3:-}" = "--dry-run" ] && ARGS+=(--dry-run)
D="$(song_dir "$SONG")"
safe_name "トラック名" "$NAME"
[ -f "$D/tracks/$NAME.mid" ] || die "見つかりません: projects/$SONG/tracks/$NAME.mid"

cd "$ROOT" && uv run --quiet scripts/synth_render.py "$SONG" "$NAME" ${ARGS[@]+"${ARGS[@]}"}
