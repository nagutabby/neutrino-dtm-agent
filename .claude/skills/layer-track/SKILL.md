---
name: layer-track
description: トラックを1本ずつ作り、単体+累積ミックスを提示し、技術解説する固定フロー。run_mode が step なら1本ごとに確認し、auto なら最後にまとめて提示する。
---

前提: `00-concept.params.tracks`(ジャンルのトラック計画)にあるトラックだけを作る。`soundfont.py check <song>` が通っていること(不足なら中断)。

予告 → 生成(ready の spec のみ、最大3案) → 検証(`midi_validate.py`/`spec_check.py`) → `register_track.py` → `render_track.sh`(単体 stem。音源は spec の `params.soundfont` から自動で決まり、足りなければ失敗して必要な内容を表示する=中断) → `mix_tracks.sh`(各トラックの最新版を累積) → 提示(パス・聴きどころ・`scripts/play.sh <path> --start 秒` の再生コマンドを単体と累積の2本分) → **技術解説(数値付き)** → 記録(`notes.md`)。

- `run_mode: step`: 解説のあと `AskUserQuestion`(次へ / 修正 / やり直し / 自分で直す)。答えを受けてから次のトラックへ。1ステップ1トラック。
- `run_mode: auto`: 確認せず次のトラックへ。全トラックと最終ミックスのあと、トラックごとの技術解説・聴きどころ・再生コマンドをまとめて提示し、気になる点を聞く。検証エラーや SoundFont 不足で続行できないときだけ中断して報告する。
