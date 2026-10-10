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
case "$STEP" in *[!0-9]*) die "step は数字のみ: '$STEP'" ;; esac
[ -f "$D/approved.json" ] || die "approved.json がありません。承認済みトラックがないためミックスできません"
command -v ffmpeg >/dev/null || die "ffmpeg がありません"

INPUTS=(); GAINS=(); PANS=(); LUFS=""
while IFS=$'\t' read -r kind a b c; do
  case "$kind" in
    T) INPUTS+=("$a"); GAINS+=("$b"); PANS+=("$c") ;;
    L) LUFS="$a" ;;
  esac
done < <(
  python3 - "$D" <<'PY'
import json, sys, pathlib
d = pathlib.Path(sys.argv[1])
a = json.loads((d / "approved.json").read_text())
order = ["drums", "bass", "chords", "melody", "vocal"]
num = {"drums": "03", "bass": "04", "chords": "05", "melody": "06", "vocal": "08"}
# 09-mix が approved のときだけ、音量(levels_db)・パン(pan)・目標ラウドネスを反映する
levels, pans, lufs = {}, {}, None
spec = d / "spec" / "09-mix.md"
if spec.exists():
    import re
    import yaml
    m = re.match(r"\A---\n(.*?)\n---", spec.read_text(encoding="utf-8"), re.S)
    meta = (yaml.safe_load(m.group(1)) or {}) if m else {}
    if meta.get("status") == "approved":
        p = meta.get("params") or {}
        levels, pans, lufs = p.get("levels_db") or {}, p.get("pan") or {}, p.get("loudness_lufs")
for t in order:
    if t in a:
        f = d / "stems" / f"{num[t]}_{t}_v{a[t]['track_version']}.wav"
        print(f"T\t{f}\t{float(levels.get(t, 0))}\t{float(pans.get(t, 0))}")
if lufs is not None:
    print(f"L\t{float(lufs)}")
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

# 09-mix が approved なら音量・パンを反映。そうでなければ従来どおり均等に重ねる
if [ -n "$LUFS" ] || [ "$(printf '%s\n' "${GAINS[@]}" "${PANS[@]}" | grep -vc '^0.0$')" -gt 0 ]; then
  FILTER=""; LABELS=""; i=0
  for f in "${INPUTS[@]}"; do
    # パン p(-1 左〜+1 右): 反対側のチャンネルだけ (1-|p|) に下げる
    FILTER="${FILTER}[${i}:a]volume=${GAINS[$i]}dB,pan=stereo|c0=$(awk -v p="${PANS[$i]}" 'BEGIN{print (p>0)?1-p:1}')*c0|c1=$(awk -v p="${PANS[$i]}" 'BEGIN{print (p<0)?1+p:1}')*c1[a${i}];"
    LABELS="${LABELS}[a${i}]"; i=$((i + 1))
  done
  FILTER="${FILTER}${LABELS}amix=inputs=${#INPUTS[@]}:normalize=0"
  [ -z "$LUFS" ] || FILTER="${FILTER},loudnorm=I=${LUFS}:TP=-1:LRA=11,aresample=48000"
  FILTER="${FILTER},alimiter=limit=0.95"
  echo "09-mix の設定を反映: 音量(dB)=${GAINS[*]} / パン=${PANS[*]} / 目標ラウドネス=${LUFS:-なし} LUFS"
else
  FILTER="amix=inputs=${#INPUTS[@]}:normalize=0,alimiter=limit=0.95"
fi
run ffmpeg -hide_banner -loglevel error "${ARGS[@]}" -filter_complex "$FILTER" "$OUT"
echo "出力: ${OUT#"$ROOT"/}"
