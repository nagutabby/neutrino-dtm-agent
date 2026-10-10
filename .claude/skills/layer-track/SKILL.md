---
name: layer-track
description: トラックを1本ずつ作り、単体+累積ミックスを提示し、技術解説する固定フロー。run_mode が step なら1本ごとに確認し、auto なら最後にまとめて提示する。
---

前提: サウンドチェック(`patch_audition.py <song>` で全トラックの試奏 wav を作成済み・音色確認済み。AGENTS.md「サウンドチェック」)。`00-concept.params.tracks`(ユーザーが最初に指示したトラック。`user_inputs.yaml` 由来)にあるトラックだけを作り、AI が足さない。`patches.py check <song>` が通っていること。

予告 → 生成(ready の spec のみ、最大3案) → 検証(`midi_validate.py`/`spec_check.py`) → `register_track.py` → `render_track.sh`(単体 stem。Sonic Pi の内蔵シンセでゼロから合成(実時間録音。これ以外の方法で音を作らない)。音色は spec の `params.patch` / `patch_params` で決まる) → `mix_tracks.sh`(各トラックの最新版を累積) → 提示(パス・聴きどころ・`scripts/play.sh <path> --start 秒` の再生コマンドを単体と累積の2本分) → **技術解説(数値付き)** → 記録(`notes.md`)。

- `run_mode: step`: 解説のあと `AskUserQuestion`(次へ / 修正 / やり直し / 自分で直す)。答えを受けてから次のトラックへ。1ステップ1トラック。
- `run_mode: auto`: 確認せず次のトラックへ。全トラックと最終ミックスのあと、トラックごとの技術解説・聴きどころ・再生コマンドをまとめて提示し、気になる点を聞く。検証エラーや合成失敗で続行できないときだけ中断して報告する(spec の差分案・再生成範囲・サブエージェントの指摘の採否も自分で決めて進める)。ボーカルありの曲は、歌詞・旋律・ボーカル合成の前に `docs/vocal-tuning.md`(NEUTRINO 調声メモ)を参照する。ボーカルは `synth.sh` が既存 wav を上書きしないため、basename に版を付ける(`08_vocal_v2` など)。

歌ありの曲は `docs/vocal-blend.md` に従う: 旋律を担えるトラックはボーカルの旋律を追う/受ける形で配置し(インストだけで成立させる)、提示では通常ミックスに加えて `mix_tracks.sh <song> <step> exclude=vocal` のインスト版の再生コマンドも並べる。ボーカルのなじませ(帯域・ダッキング・リバーブ・質感)は `09-mix` に数値で入れる。

全トラックを作り終えたら、ユーザーへの最終提示の前に `sound-qa`(雑音・統一感の Haiku チェック)を走らせ、そのあと `mix-review` に進む。
