#!/usr/bin/env bash
# 使い方:
#   play.sh <file> [--start 秒] [--loop] [--dry-run]   projects/ 配下の音声(wav/mp3/flac/m4a)か MIDI(.mid)を再生
#   play.sh --list <song>                                曲の聴けるファイルを一覧する
# 音声は mpv(ターミナル操作: スペース=一時停止、←→=5秒移動、↑↓=音量、q=終了)。
# MIDI(projects/<song>/tracks/*.mid)は Sonic Pi で一時 wav に合成(実時間録音)してから mpv で再生する(音色は spec の patch)。
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

if [ "${1:-}" = "--list" ]; then
  D="$(song_dir "${2:-}")"
  find "$D" \( -name '*.wav' -o -name '*.mp3' -o -name '*.flac' -o -name '*.m4a' -o -name '*.mid' \) -type f \
    | sed "s|^$ROOT/||" | sort
  exit 0
fi

FILE="${1:-}"; START=""; LOOP=0
[ -n "$FILE" ] || die "使い方: play.sh <file> [--start 秒] [--loop] [--dry-run] / play.sh --list <song>"
shift
while [ $# -gt 0 ]; do
  case "$1" in
    --start) START="${2:-}"; shift 2 || die "--start に秒数が必要です" ;;
    --loop) LOOP=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) die "不明な引数: $1" ;;
  esac
done
case "$START" in ''|*[!0-9.]*) [ -z "$START" ] || die "--start は秒数(数字)で指定します: '$START'" ;; esac

# projects/ 配下のファイルだけ再生する(曲の取り違え・任意パスの再生を防ぐ)
[ -f "$FILE" ] || FILE="$ROOT/$FILE"
[ -f "$FILE" ] || die "ファイルがありません: $1"
REAL="$(cd "$(dirname "$FILE")" && pwd -P)/$(basename "$FILE")"
case "$REAL" in "$ROOT"/projects/*) ;; *) die "projects/ 配下のファイルのみ再生できます: $REAL" ;; esac

case "$REAL" in
  *.mid|*.midi)
    REL="${REAL#"$ROOT"/projects/}"; P_SONG="${REL%%/*}"; P_NAME="$(basename "$REAL")"; P_NAME="${P_NAME%.*}"
    case "$REL" in */tracks/*.mid) ;; *) die "MIDI は projects/<song>/tracks/ のものだけ再生できます(音色を spec から決めるため): $REAL" ;; esac
    [ "$DRY_RUN" = 1 ] || command -v mpv >/dev/null || die "mpv がありません(brew install mpv)"
    TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
    run bash -c 'cd "$1" && uv run --quiet scripts/synth_render.py "$2" "$3" --out "$4"' _ "$ROOT" "$P_SONG" "$P_NAME" "$TMP/preview.wav"
    ARGS=(--no-video)
    [ -z "$START" ] || ARGS+=("--start=$START")
    [ "$LOOP" = 0 ] || ARGS+=(--loop-file=inf)
    run mpv "${ARGS[@]}" "$TMP/preview.wav" ;;
  *.wav|*.mp3|*.flac|*.m4a)
    [ "$DRY_RUN" = 1 ] || command -v mpv >/dev/null || die "mpv がありません(brew install mpv)"
    ARGS=(--no-video)
    [ -z "$START" ] || ARGS+=("--start=$START")
    [ "$LOOP" = 0 ] || ARGS+=(--loop-file=inf)
    run mpv "${ARGS[@]}" "$REAL" ;;
  *) die "再生できない形式です: $REAL(wav/mp3/flac/m4a/mid)" ;;
esac
