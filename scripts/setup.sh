#!/usr/bin/env bash
# 環境確認: uv / Sonic Pi / ruby / ffmpeg / mpv
set -u
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

ok() { echo "  ✔ $*"; }
ng() { echo "  ✘ $*"; MISSING=1; }
MISSING=0

echo "■ 環境チェック"
if command -v uv >/dev/null; then ok "uv"; else ng "uv(brew install uv)"; fi
if command -v ffmpeg >/dev/null; then ok "ffmpeg(録音の変換)"; else ng "ffmpeg(brew install ffmpeg)"; fi
SONIC_PI_APP_DIR="${SONIC_PI_APP:-/Applications/Sonic Pi.app}"
if [ -f "$SONIC_PI_APP_DIR/Contents/Resources/app/server/ruby/bin/headless_boot.rb" ]; then ok "Sonic Pi(ライブコーディング本体。エージェントの試聴録音はヘッドレスで実時間)"; else ng "Sonic Pi(brew install --cask sonic-pi。標準外の場所なら .env に SONIC_PI_APP=/path/to/'Sonic Pi.app')"; fi
if command -v ruby >/dev/null || [ -x "${SONIC_PI_RUBY:-}" ]; then ok "ruby(録音スクリプト用)"; else ng "ruby(brew install ruby。または .env に SONIC_PI_RUBY)"; fi
if command -v mpv >/dev/null; then ok "mpv(試聴: scripts/play.sh)"; else ng "mpv(brew install mpv)"; fi
if [ "$MISSING" = 0 ]; then echo "すべて揃っています。"; else echo "不足があります。上の ✘ を解消してください。"; fi
exit 0
