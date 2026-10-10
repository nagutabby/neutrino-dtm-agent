#!/usr/bin/env bash
# 使い方: new_song.sh [--dry-run]
# projects/<YYYYMMDD-NN>/ を自動で作り、spec 雛形を展開する。
# プロジェクト名は「日付-連番」(例: 20261010-01)。同じ日の2つ目以降は連番が増える。名前は指定できない。
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

[ "${1:-}" != "--dry-run" ] || DRY_RUN=1
{ [ $# -eq 0 ] || { [ $# -eq 1 ] && [ "$1" = "--dry-run" ]; }; } || die "使い方: new_song.sh [--dry-run](プロジェクト名は日付-連番で自動付与)"

TODAY="$(date +%Y%m%d)"
N=1
while [ -e "$ROOT/projects/$TODAY-$(printf '%02d' "$N")" ]; do N=$((N + 1)); done
SONG="$TODAY-$(printf '%02d' "$N")"
DEST="$ROOT/projects/$SONG"

run mkdir -p "$ROOT/projects"
run mkdir "$DEST"
for d in spec tracks stems mix musicxml label/full label/mono label/timing output; do
  run mkdir -p "$DEST/$d"
done
run cp "$ROOT"/docs/templates/spec/*.md "$DEST/spec/"
run cp "$ROOT/docs/templates/notes.md" "$DEST/notes.md"
echo "作成しました: projects/$SONG"
echo "曲名(以降のスクリプトに渡す): $SONG"
echo "次: uv run scripts/spec_status.py $SONG"
