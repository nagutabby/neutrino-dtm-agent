#!/usr/bin/env bash
# 使い方: reference_fetch.sh <song> <youtube-url> [--dry-run]
# 参考曲の音声を projects/<song>/reference/<video-id>/audio.wav に保存する(私的な分析専用)。
# 10 分以内の単体動画のみ。既存は上書きしない。音声は .gitignore で追跡されない。
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SONG="${1:-}"; URL="${2:-}"
[ -n "$SONG" ] && [ -n "$URL" ] || die "使い方: reference_fetch.sh <song> <youtube-url> [--dry-run]"
[ "${3:-}" = "--dry-run" ] && DRY_RUN=1
D="$(song_dir "$SONG")"
case "$URL" in
  https://www.youtube.com/*|https://youtube.com/*|https://m.youtube.com/*|https://music.youtube.com/*|https://youtu.be/*) ;;
  *) die "YouTube の https URL のみ対応です: '$URL'" ;;
esac
command -v yt-dlp >/dev/null || die "yt-dlp がありません(brew install yt-dlp)"
command -v ffmpeg >/dev/null || die "ffmpeg がありません(brew install ffmpeg)"

ID="$(yt-dlp --no-playlist --skip-download --print id "$URL" | head -n1)"
case "$ID" in ''|*[!A-Za-z0-9_-]*) die "動画 ID を取得できませんでした: '$ID'" ;; esac
OUT="$D/reference/$ID"
[ ! -e "$OUT/audio.wav" ] || die "既に存在します(上書きしません): ${OUT#"$ROOT"/}/audio.wav"

run mkdir -p "$OUT"
run yt-dlp --no-playlist --match-filter "duration<=600" -x --audio-format wav \
  --print-to-file "%(.{id,title,uploader,duration,webpage_url})j" "$OUT/source.json" \
  -o "$OUT/audio.%(ext)s" "$URL"
echo "保存: ${OUT#"$ROOT"/}/audio.wav"
echo "$ID"
