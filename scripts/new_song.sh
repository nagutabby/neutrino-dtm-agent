#!/usr/bin/env bash
# 使い方: new_song.sh <song> [--dry-run]
# projects/<song>/ を作り、spec 雛形を展開する(既存なら何もしない)
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SONG="${1:-}"
[ -n "$SONG" ] || die "使い方: new_song.sh <song> [--dry-run]"
[ "${2:-}" = "--dry-run" ] && DRY_RUN=1
case "$SONG" in *[!A-Za-z0-9_-]*) die "曲名は英数字・_・- のみ: '$SONG'" ;; esac

DEST="$ROOT/projects/$SONG"
[ ! -e "$DEST" ] || die "既に存在します: projects/$SONG(上書きしません)"

for d in spec tracks stems mix musicxml label/full label/mono label/timing output; do
  run mkdir -p "$DEST/$d"
done
run cp "$ROOT"/docs/templates/spec/*.md "$DEST/spec/"
run cp "$ROOT/docs/templates/notes.md" "$DEST/notes.md"
echo "作成しました: projects/$SONG"
echo "次: uv run scripts/spec_status.py $SONG"
