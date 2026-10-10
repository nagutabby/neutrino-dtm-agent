---
description: 新しい曲のプロジェクト(projects/<song>/)を開始する
argument-hint: "[曲名(英数字・_・-)]"
---

新しい曲のプロジェクトを開始する。`coach-start` スキルの手順に従う。曲名の指定: $ARGUMENTS

1. 環境確認: `bash scripts/setup.sh` を実行し、✘ があれば直し方を伝える(認証・権限付与などはユーザー自身に実行してもらう)。SuperCollider の ✘ は合成に必須(`brew install --cask supercollider` をユーザーに案内)。
2. 曲名が空なら `AskUserQuestion` で決めてもらう(英数字・`_`・`-` のみ。既存の `projects/` と重複しないこと)。
3. **最初に参考曲の YouTube リンクを聞く**(複数あれば複数)。参考曲が無いと明言されたときだけ、具体的な曲名を挙げ「〇〇と同じ感じでよいですか?」と聞く。
4. 先に `scripts/new_song.sh <song> --dry-run` で確認し、問題なければ `scripts/new_song.sh <song>` で `projects/<song>/` を作る。既存なら上書きせず、続きから始めるか別名にするか聞く。
5. 集めた URL ごとに `/reference` の手順で音源分離・分析する(MIDI への書き起こしはしない)。続けて **ジャンル → 曲の長さ → 歌あり/インスト → 進め方(ステップごと / すべて作り切る)** を聞く(合計5問)。
6. ジャンルが決まったら `/reference` の手順で類似曲の MIDI を Web 検索して解析する。`genre-research` でジャンルの特徴を調べ(`docs/genres/` か Web)、ユーザーに確認して `genre_apply.py` で反映する。最後の `patches.py check` がエラーなら直してから進む。
7. 回答と分析結果を `spec/00-concept.md` に反映し、内容を見せて `uv run scripts/decide.py <song> 00-concept` で ready にする。
8. 「いま扱う曲は `<song>`」と宣言し、`uv run scripts/spec_status.py <song>` で次に決める要素を案内する。

ジャンル・曲の長さ・進め方を決める前に、次の要素やトラックには進まない。
