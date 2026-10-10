#!/usr/bin/env bash
# 共通: リポジトリルート、.env 読み込み、--dry-run 実行ヘルパー
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ROOT/.env"
  set +a
fi
NEUTRINO_DIR="${NEUTRINO_DIR:-$HOME/NEUTRINO}"
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

# song 名の検査と作業ディレクトリ
song_dir() {
  case "$1" in
    ''|*[!A-Za-z0-9_-]*) die "曲名は英数字・_・- のみ: '$1'" ;;
  esac
  [ -d "$ROOT/projects/$1" ] || die "プロジェクトがありません: projects/$1(scripts/new_song.sh $1)"
  echo "$ROOT/projects/$1"
}
