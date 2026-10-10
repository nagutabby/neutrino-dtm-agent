---
name: coach-start
description: 新しい曲を始めるとき。参考曲・ジャンル・曲の長さ・歌/インスト・進め方を5問で確認し、projects/<song> と 00-concept を作ってジャンルを反映する。
---

1. 質問は合計 **5問**(AskUserQuestion。最大4問/回なので2回に分けてよい)。この順で聞く:
   1. **【必ず最初】どの曲を参考に作るか**。**YouTube の動画リンク(URL)を書いてもらう**。複数あれば複数(1行1URL)。曲名だけの回答なら URL も重ねて聞く。参考曲が無いと明言されたときだけ、確信のある有名曲を挙げ「〇〇(曲名/アーティスト)と同じ感じでよいですか?」と聞いて代わりにする(複製は提案しない)。
   2. **ジャンル**。参考曲の分析(手順3)を先に済ませ、その結果に近いジャンルを最大3つ候補にして聞く(自由記述も可)。ユーザーの答えを正とし、AI が決めない。
   3. **曲の長さ**(秒の目安。例: 30秒 / 1分 / 2分 / 3分)。ジャンルの標準尺(`docs/genres/<id>.md` の `length_seconds`)を添えて選択肢にする。
   4. **歌あり / インスト**(後から変えると作り直しになるため早めに決める)。
   5. **進め方**: ステップごとに進める(`step`: 1トラックごとに聴いて確認) / すべて作り切る(`auto`: 最後にまとめて提示)。
2. 曲名を決め、`scripts/new_song.sh <song>` を実行(先に `--dry-run` で確認)。
3. 集めた URL ごとに `/reference` の手順(`scripts/reference_run.sh <song> <url>`、先に `--dry-run`)で分析する。1 より前に質問1だけ済ませて 3 を実行し、2 以降の質問に分析結果を活かしてよい。
4. **`genre-research` スキル**でジャンルを調べ、`genre_apply.py` で反映する(長さ・`run_mode` を渡す)。**SoundFont 不足なら中断**してユーザーに必要な内容を伝える。
5. 回答と分析結果(複数あれば共通点・違いを整理)を `spec/00-concept.md` に反映(`vocal: true|false`・`run_mode`・`params.genre/target_seconds/tracks` を必ず記入。インスト曲は歌詞・ボーカル前提の説明を出さない)。内容を見せてから `uv run scripts/decide.py <song> 00-concept` で ready にする。
6. `uv run scripts/spec_status.py <song>` で次に決める要素を案内する。
