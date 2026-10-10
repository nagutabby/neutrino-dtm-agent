---
name: coach-start
description: 新しい曲を始めるとき。参考曲・ジャンル・曲の長さ・歌/インスト・進め方を5問で確認し、projects/<song> と 00-concept を作ってジャンルを反映する。
---

1. 質問は合計 **5問**(AskUserQuestion。最大4問/回なので2回に分けてよい)。この順で聞く:
   1. **【必ず最初】どの曲を参考に作るか**。**YouTube の動画リンク(URL)を最低3つ書いてもらう**(1行1URL。多いほどよい)。3つ未満なら不足分を重ねて聞く。曲名だけの回答なら URL も重ねて聞く。複数曲の共通点を雰囲気の型にするため、3曲未満のまま進めない。
   2. **ジャンル**。参考曲の分析(手順3)を先に済ませ、その結果に近いジャンルを最大3つ候補にして聞く(自由記述も可)。ユーザーの答えを正とし、AI が決めない。
   3. **曲の長さ**(秒の目安。例: 30秒 / 1分 / 2分 / 3分)。調べたジャンルの標準尺(`projects/<song>/genre/<id>.md` の `length_seconds`)を添えて選択肢にする。
   4. **歌あり / インスト**(後から変えると作り直しになるため早めに決める)。
   5. **進め方**: ステップごとに進める(`step`: 1トラックごとに聴いて確認) / すべて作り切る(`auto`: 最後にまとめて提示)。
2. `scripts/new_song.sh` を実行(先に `--dry-run` で確認)。プロジェクト名は `日付-連番`(例: `20261010-01`)で自動付与される。曲名は聞かない。出力された名前を以降の `<song>` に使う。
3. 集めた URL ごとに `/reference` の手順(`scripts/reference_run.sh <song> <url>`、先に `--dry-run`)で分析する(YouTube 取得・音源分離・音声の分析まで。MIDI への書き起こし・MIDI 検索はしない)。1 より前に質問1だけ済ませて 3 を実行し、2 以降の質問に分析結果を活かしてよい。全 URL の分析後、`reference_summary.py` で共通点を few-shot の例にまとめる(類似曲の Web 検索はしない)。
4. **`genre-research` スキル**でジャンルを調べ、`genre_apply.py` で反映する(長さ・`run_mode` を渡す)。パッチ検査(`patches.py check`)でエラーがあれば直す。続けて**サウンドチェック**(`patch_audition.py <song>` で全トラックの試奏を作り、音色を確認)を済ませてから制作に入る。
5. 回答と分析結果(複数あれば共通点・違いを整理)を `spec/00-concept.md` に反映(`vocal: true|false`・`run_mode`・`params.genre/target_seconds/tracks` を必ず記入。インスト曲は歌詞・ボーカル前提の説明を出さない)。内容を見せてから `uv run scripts/decide.py <song> 00-concept` で ready にする。
6. `uv run scripts/spec_status.py <song>` で次に決める要素を案内する。
