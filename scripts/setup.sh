#!/usr/bin/env bash
# 環境確認: uv / NEUTRINO / Sonic Pi / ffmpeg / MuseScore
set -u
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

ok() { echo "  ✔ $*"; }
ng() { echo "  ✘ $*"; MISSING=1; }
MISSING=0

echo "■ 環境チェック"
if command -v uv >/dev/null; then ok "uv"; else ng "uv(brew install uv)"; fi
if command -v ffmpeg >/dev/null; then ok "ffmpeg"; else ng "ffmpeg(brew install ffmpeg)"; fi
SONIC_PI_APP_DIR="${SONIC_PI_APP:-/Applications/Sonic Pi.app}"
if [ -f "$SONIC_PI_APP_DIR/Contents/Resources/app/server/ruby/bin/headless_boot.rb" ]; then ok "Sonic Pi(シンセ合成。ヘッドレスで実時間録音)"; else ng "Sonic Pi(brew install --cask sonic-pi。標準外の場所なら .env に SONIC_PI_APP=/path/to/'Sonic Pi.app')"; fi
if command -v ruby >/dev/null || [ -x "${SONIC_PI_RUBY:-}" ]; then ok "ruby(Sonic Pi の録音スクリプト用)"; else ng "ruby(brew install ruby。または .env に SONIC_PI_RUBY)"; fi
if command -v mpv >/dev/null; then ok "mpv(試聴: scripts/play.sh)"; else ng "mpv(brew install mpv)"; fi
if command -v yt-dlp >/dev/null; then ok "yt-dlp(参考曲の分析用)"; else echo "  - yt-dlp 未導入(参考曲の分析を使うなら brew install yt-dlp)"; fi
if [ -x "$NEUTRINO_DIR/bin/neutrino" ] && [ -x "$NEUTRINO_DIR/bin/musicXMLtoLabel" ]; then
  ok "NEUTRINO: $NEUTRINO_DIR"
elif [ -f "$NEUTRINO_DIR/bin/neutrino" ]; then
  ng "NEUTRINO に実行権限がありません。次をご自身で実行してください: chmod 755 \"$NEUTRINO_DIR\"/bin/* && xattr -dr com.apple.quarantine \"$NEUTRINO_DIR/bin\""
else
  ng "NEUTRINO が見つかりません: $NEUTRINO_DIR(.env の NEUTRINO_DIR を確認)"
fi
if [ -n "${MUSESCORE_BIN:-}" ] && [ -x "$MUSESCORE_BIN" ]; then
  ok "MuseScore CLI: $MUSESCORE_BIN"
else
  ng "MuseScore 4 CLI(brew install --cask musescore 後、.env に MUSESCORE_BIN を設定)"
fi
echo "  音色(パッチ。曲ごとの検査は patches.py check <song>):"
(cd "$ROOT" && uv run --quiet scripts/patches.py list 2>/dev/null | sed 's/^/   /') || echo "   (uv 未導入のため一覧を省略)"
if [ "$MISSING" = 0 ]; then echo "すべて揃っています。"; else echo "不足があります。上の ✘ を解消してください。"; fi
exit 0
