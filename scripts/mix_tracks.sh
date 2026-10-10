#!/usr/bin/env bash
# 使い方: mix_tracks.sh <song> <step> [--dry-run]
# approved.json に載っている承認済みトラックだけを ffmpeg で重ねて mix/step<step>_vN.wav を作る。
# stems/ には <NN>_<track>_v<承認版>.wav(ボーカルは output/<song>.wav を stems/ に NN_vocal_vN.wav としてコピー)が必要。
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SONG="${1:-}"; STEP="${2:-}"
[ -n "$SONG" ] && [ -n "$STEP" ] || die "使い方: mix_tracks.sh <song> <step> [--dry-run]"
[ "${3:-}" = "--dry-run" ] && DRY_RUN=1
D="$(song_dir "$SONG")"
[ -f "$D/approved.json" ] || die "approved.json がありません。承認済みトラックがないためミックスできません"
command -v ffmpeg >/dev/null || die "ffmpeg がありません"

INPUTS=()
while IFS= read -r f; do INPUTS+=("$f"); done < <(
  python3 - "$D" <<'PY'
import json, sys, pathlib
d = pathlib.Path(sys.argv[1])
a = json.loads((d / "approved.json").read_text())
order = ["drums", "bass", "chords", "melody", "vocal"]
num = {"drums": "03", "bass": "04", "chords": "05", "melody": "06", "vocal": "08"}
for t in order:
    if t in a:
        print(d / "stems" / f"{num[t]}_{t}_v{a[t]['track_version']}.wav")
PY
)
[ "${#INPUTS[@]}" -gt 0 ] || die "承認済みトラックがありません"
ARGS=()
for f in "${INPUTS[@]}"; do
  [ -f "$f" ] || die "stem がありません: ${f#"$ROOT"/}(render_track.sh で作成)"
  ARGS+=(-i "$f")
done

N=1
while [ -e "$D/mix/step${STEP}_v${N}.wav" ]; do N=$((N + 1)); done
OUT="$D/mix/step${STEP}_v${N}.wav"
echo "ミックス対象(承認済みのみ):"; printf '  %s\n' "${INPUTS[@]#"$ROOT"/}"
run ffmpeg -hide_banner -loglevel error "${ARGS[@]}" \
  -filter_complex "amix=inputs=${#INPUTS[@]}:normalize=0,alimiter=limit=0.95" "$OUT"
echo "出力: ${OUT#"$ROOT"/}"
