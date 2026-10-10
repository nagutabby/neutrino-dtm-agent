#!/usr/bin/env bash
# 使い方: new_session.sh [--dry-run]
# projects/<YYYYMMDD-NN>/ をライブコーディング用に作る(current.rb / proposals/ / renders/ / session.md)。
# プロジェクト名は「日付-連番」(例: 20261010-01)で自動付与。名前は指定できない。既存の曲は触らない。
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

[ "${1:-}" != "--dry-run" ] || DRY_RUN=1
{ [ $# -eq 0 ] || { [ $# -eq 1 ] && [ "$1" = "--dry-run" ]; }; } || die "使い方: new_session.sh [--dry-run]"

TODAY="$(date +%Y%m%d)"
N=1
while [ -e "$ROOT/projects/$TODAY-$(printf '%02d' "$N")" ]; do N=$((N + 1)); done
SONG="$TODAY-$(printf '%02d' "$N")"
DEST="$ROOT/projects/$SONG"

run mkdir -p "$ROOT/projects"
run mkdir "$DEST"
for d in proposals renders; do
  run mkdir -p "$DEST/$d"
done
if [ "$DRY_RUN" = 1 ]; then
  echo "[dry-run] $DEST/current.rb と session.md を作成"
else
  cat > "$DEST/current.rb" <<'RB'
# ここに Sonic Pi のバッファを貼る(ユーザーのコード。エージェントは依頼がなければ書き換えない)
RB
  cat > "$DEST/session.md" <<'MD'
# セッション
- 狙い(ユーザーの言葉):
- テンポ(BPM) / キー・スケール:
- 目標の長さ:

## ステム(重ねた順)
<!-- 例: 1. drums — live_loop :drums / 2. bass — live_loop :bass -->

## 履歴
<!-- 改善・次のステムの提案と、ユーザーの採否を1行ずつ -->
MD
fi
echo "作成しました: projects/$SONG"
echo "曲名(以降のスクリプトに渡す): $SONG"
echo "次: Sonic Pi のコードを projects/$SONG/current.rb に保存して、エージェントに伝える"
