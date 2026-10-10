#!/usr/bin/env bash
# 環境確認: uv / NEUTRINO / fluidsynth / ffmpeg / MuseScore / SoundFont
set -u
. "$(dirname "$0")/lib.sh"

ok() { echo "  ✔ $*"; }
ng() { echo "  ✘ $*"; MISSING=1; }
MISSING=0

echo "■ 環境チェック"
command -v uv >/dev/null && ok "uv" || ng "uv(brew install uv)"
command -v ffmpeg >/dev/null && ok "ffmpeg" || ng "ffmpeg(brew install ffmpeg)"
command -v fluidsynth >/dev/null && ok "fluidsynth" || ng "fluidsynth(brew install fluid-synth)"
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
if [ -n "${SOUNDFONT:-}" ] && [ -f "$SOUNDFONT" ]; then
  ok "SoundFont: $SOUNDFONT"
else
  ng "SoundFont(.sf2)を用意して .env の SOUNDFONT に設定"
fi
[ "$MISSING" = 0 ] && echo "すべて揃っています。" || echo "不足があります。上の ✘ を解消してください。"
exit 0
