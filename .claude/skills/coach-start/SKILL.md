---
name: coach-start
description: 新しい曲を始めるとき。目的・好み・使える時間を最大3問で確認し、projects/<song> と 00-concept の下書きを作る。
---

1. 質問は合計 **最大3問**(AskUserQuestion)。この順で聞く:
   1. **【必ず最初】どの曲を参考に作るか**。**YouTube の動画リンク(URL)を書いてもらう**。複数あれば複数(1行1URL)。曲名だけの回答なら URL も重ねて聞く。参考曲が無いと明言されたときだけ、確信のある有名曲を挙げ「〇〇(曲名/アーティスト)と同じ感じでよいですか?」と聞いて代わりにする(複製は提案しない)。
   2. **歌あり / インスト**(後から変えると作り直しになるため最初に決める)。
   3. 目的・使える時間。
2. 曲名を決め、`scripts/new_song.sh <song>` を実行(先に `--dry-run` で確認)。
3. 集めた URL ごとに `/reference` の手順(`scripts/reference_run.sh <song> <url>`、先に `--dry-run`)で分析する。
4. 回答と分析結果(複数あれば共通点・違いを整理)を `spec/00-concept.md` に下書き(`vocal: true|false` を必ず記入。インスト曲は歌詞・ボーカル前提の説明を出さない)し、承認を取る(`approve.py`)。
5. `uv run scripts/spec_status.py <song>` で次に決める要素を案内する。
