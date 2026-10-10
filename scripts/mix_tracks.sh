#!/usr/bin/env bash
# 使い方: mix_tracks.sh <song> <step> [track=N ...] [--dry-run]
# stems/ にあるトラック(NN_<track>_vN.wav)を、トラックごとに最新版で ffmpeg で重ねて mix/step<step>_vN.wav を作る。
# ボーカルは output/<song>.wav を stems/ に NN_vocal_vN.wav としてコピーしておく。トラック数は spec(ジャンル)で変わる。
# 版を固定する: mix_tracks.sh <song> <step> [track=N ...]
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SONG="${1:-}"; STEP="${2:-}"
[ -n "$SONG" ] && [ -n "$STEP" ] || die "使い方: mix_tracks.sh <song> <step> [track=N ...] [--dry-run]"
for x in "$@"; do [ "$x" = "--dry-run" ] && DRY_RUN=1; done
D="$(song_dir "$SONG")"
case "$STEP" in *[!0-9]*) die "step は数字のみ: '$STEP'" ;; esac
command -v ffmpeg >/dev/null || die "ffmpeg がありません"

INPUTS=(); GAINS=(); PANS=(); LUFS=""; FADE_IN=""
while IFS=$'\t' read -r kind a b c; do
  case "$kind" in
    T) INPUTS+=("$a"); GAINS+=("$b"); PANS+=("$c") ;;
    L) LUFS="$a" ;;
    F) FADE_IN="$a" ;;
  esac
done < <(
  python3 - "$D" "$@" <<'PY'
import pathlib, re, sys
d = pathlib.Path(sys.argv[1])
# stems/<NN>_<track>_v<N>.wav のうち、トラックごとに最新版を使う(NN 順に重ねる)。
# 版の固定: mix_tracks.sh <song> <step> drums=1 chords=2 のように track=N を後ろに並べる
pins = dict(a.split("=", 1) for a in sys.argv[4:] if "=" in a)
found = {}
for f in sorted((d / "stems").glob("*_v*.wav")):
    m = re.fullmatch(r"(\d{2})_([a-z0-9-]+)_v(\d+)\.wav", f.name)
    if not m:
        continue
    num, track, ver = m.group(1), m.group(2), int(m.group(3))
    if num == "09":
        continue
    if track in pins and str(ver) != pins[track]:
        continue
    if track not in found or ver > found[track][1]:
        found[track] = (num, ver, f)
# 09-mix が ready のときだけ、音量(levels_db)・パン(pan)・目標ラウドネスを反映する
levels, pans, lufs, fade_in = {}, {}, None, None
spec = d / "spec" / "09-mix.md"
if spec.exists():
    import yaml
    m = re.match(r"\A---\n(.*?)\n---", spec.read_text(encoding="utf-8"), re.S)
    meta = (yaml.safe_load(m.group(1)) or {}) if m else {}
    if meta.get("status") == "ready":
        p = meta.get("params") or {}
        levels, pans, lufs = p.get("levels_db") or {}, p.get("pan") or {}, p.get("loudness_lufs")
        fade_in = p.get("fade_in_sec")
for track, (num, ver, f) in sorted(found.items(), key=lambda kv: kv[1][0]):
    print(f"T\t{f}\t{float(levels.get(track, 0))}\t{float(pans.get(track, 0))}")
if lufs is not None:
    print(f"L\t{float(lufs)}")
if fade_in:
    print(f"F\t{float(fade_in)}")
PY
)
[ "${#INPUTS[@]}" -gt 0 ] || die "stems/ にトラックがありません(render_track.sh で作成)"
ARGS=()
for f in "${INPUTS[@]}"; do
  [ -f "$f" ] || die "stem がありません: ${f#"$ROOT"/}(render_track.sh で作成)"
  ARGS+=(-i "$f")
done

N=1
while [ -e "$D/mix/step${STEP}_v${N}.wav" ]; do N=$((N + 1)); done
OUT="$D/mix/step${STEP}_v${N}.wav"
echo "ミックス対象(トラックごとに最新版):"; printf '  %s\n' "${INPUTS[@]#"$ROOT"/}"

# 09-mix が ready なら音量・パンを反映。そうでなければ従来どおり均等に重ねる
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
  # 導入の唐突さを避ける(loudnorm が静かな導入を持ち上げるため、最後にフェードインを掛ける)
  [ -z "$FADE_IN" ] || FILTER="${FILTER},afade=t=in:d=${FADE_IN}"
  echo "09-mix の設定を反映: 音量(dB)=${GAINS[*]} / パン=${PANS[*]} / 目標ラウドネス=${LUFS:-なし} LUFS"
else
  FILTER="amix=inputs=${#INPUTS[@]}:normalize=0,alimiter=limit=0.95"
fi
run ffmpeg -hide_banner -loglevel error "${ARGS[@]}" -filter_complex "$FILTER" "$OUT"
echo "出力: ${OUT#"$ROOT"/}"
