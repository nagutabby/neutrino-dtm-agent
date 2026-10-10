---
description: 新しい曲のプロジェクト(projects/<song>/)を開始する
argument-hint: ""
---

新しい曲のプロジェクトを開始する。`coach-start` スキルの手順に従う。プロジェクト名は `日付-連番`(例: `20261010-01`)で自動付与する(曲名は聞かない)。

1. 環境確認: `bash scripts/setup.sh` を実行し、✘ があれば直し方を伝える(認証・権限付与などはユーザー自身に実行してもらう)。SuperCollider の ✘ は合成に必須(`brew install --cask supercollider` をユーザーに案内)。
2. **最初に参考曲の YouTube リンクを最低3つ聞く**(3つ未満なら不足分を重ねて聞く)。
3. 先に `scripts/new_song.sh --dry-run` で確認し、問題なければ `scripts/new_song.sh` で `projects/<日付-連番>/` を作る。出力された名前を以降の `<song>` に使う。
4. 集めた URL ごとに `/reference` の手順で音源分離・分析する(MIDI への書き起こしはしない)。続けて **ジャンル → 曲の長さ → 歌あり/インスト → 進め方(ステップごと / すべて作り切る)** を聞く(合計5問)。
5. 全参考曲の分析後に `reference_summary.py` で few-shot の例を作る。`genre-research` でジャンルの特徴を調べ(Web 検索で、その曲用の定義を作る)、ユーザーに見せて(`step` は確認、`auto` は止まらず)作るトラックをユーザーに聞いて(`genre-research` 手順5)、回答どおりに `genre_apply.py --tracks` で反映する。最後の `patches.py check` がエラーなら直してから進む。
6. 回答と分析結果を `spec/00-concept.md` に反映し、内容を見せて `uv run scripts/decide.py <song> 00-concept` で ready にする。
7. 「いま扱う曲は `<song>`」と宣言し、`uv run scripts/spec_status.py <song>` で次に決める要素を案内する。

ジャンル・曲の長さ・進め方を決める前に、次の要素やトラックには進まない。
