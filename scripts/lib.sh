#!/usr/bin/env bash
# 共通: リポジトリルート、.env 読み込み、--dry-run 実行ヘルパー
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ROOT/.env"
  set +a
fi
DRY_RUN="${DRY_RUN:-0}"

die() { echo "[エラー] $*" >&2; exit 1; }

# run <cmd...>: DRY_RUN=1 なら表示だけ
run() {
  if [ "$DRY_RUN" = 1 ]; then
    printf '[dry-run]'; printf ' %q' "$@"; printf '\n'
  else
    "$@"
  fi
}
