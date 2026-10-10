---
description: 新しい曲のプロジェクト(projects/<song>/)を開始する
argument-hint: "[曲名(英数字・_・-)]"
---

新しい曲のプロジェクトを開始する。`coach-start` スキルの手順に従う。曲名の指定: $ARGUMENTS

1. 環境確認: `bash scripts/setup.sh` を実行し、✘ があれば直し方を伝える(認証・権限付与などはユーザー自身に実行してもらう)。
2. 曲名が空なら `AskUserQuestion` で決めてもらう(英数字・`_`・`-` のみ。既存の `projects/` と重複しないこと)。
3. 最初に「歌あり / インスト」を確認し(`00-concept` の `vocal`)、続けて目的・好み・使える時間を聞く(合計最大3問、聴感ベースの選択肢)。
4. 先に `scripts/new_song.sh <song> --dry-run` で確認し、問題なければ `scripts/new_song.sh <song>` で `projects/<song>/` を作る。既存なら上書きせず、続きから始めるか別名にするか聞く。
5. 回答を `spec/00-concept.md` に下書きして承認を取る(承認後に `uv run scripts/approve.py <song> 00-concept`)。
6. 「いま扱う曲は `<song>`」と宣言し、`uv run scripts/spec_status.py <song>` で次に決める要素を案内する。

承認なしに次の要素やトラックには進まない。
