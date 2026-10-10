#!/usr/bin/env bash
# 使い方: render_track.sh <song> <track-midi-name 例: 04_bass_v1> [--dry-run]
# tracks/<name>.mid を FluidSynth で stems/<name>.wav にする(試聴用)。SoundFont はトラックごとに spec から決まる
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SONG="${1:-}"; NAME="${2:-}"
[ -n "$SONG" ] && [ -n "$NAME" ] || die "使い方: render_track.sh <song> <name> [--dry-run]"
[ "${3:-}" = "--dry-run" ] && DRY_RUN=1
D="$(song_dir "$SONG")"
safe_name "トラック名" "$NAME"
[ -f "$D/tracks/$NAME.mid" ] || die "見つかりません: projects/$SONG/tracks/$NAME.mid"
command -v fluidsynth >/dev/null || die "fluidsynth がありません(brew install fluid-synth)"

# トラック spec が指定する SoundFont(params.soundfont > 00-concept のトラック計画 > gm)を解決する。
# 足りなければ「何が必要か」を表示して失敗する(作業を中断してユーザーに用意してもらう)。
SOUNDFONT="$(cd "$ROOT" && uv run --quiet scripts/soundfont.py resolve "$SONG" "${NAME%%_*}")" || exit 1

OUT="$D/stems/$NAME.wav"
[ ! -e "$OUT" ] || die "既に存在します(上書きしません): $OUT"
run fluidsynth -ni -F "$OUT" -r 48000 "$SOUNDFONT" "$D/tracks/$NAME.mid"
echo "出力: ${OUT#"$ROOT"/}"
