---
name: genre-research
description: ユーザーが選んだジャンルの音楽的特徴(テンポ・リズム・和声・音色・構成・尺)を調べ、トラック構成と必要な SoundFont を決めて曲に反映する。
---

前提: ジャンルはユーザーに聞いて決まっている(推測しない)。

1. **定義を探す**: `uv run scripts/genre_apply.py --list` と `docs/genres/` に該当ジャンルがあるか。あれば読んで 2 は省く(曲固有の調整が要るときだけ追加で調べる)。
2. **無ければ調べる**: WebSearch で、そのジャンルの ①テンポ帯とノリ(ハーフタイム/スウィング等) ②リズムの型 ③典型のスケール・コード進行 ④定番の楽器・音色 ⑤標準的な曲構成と尺 ⑥ミックスの傾向 を確認する。複数の情報源で裏を取り、確信のない点は「推定」と書く。`docs/genres/_template.md` を元に `projects/<song>/genre/<id>.md` を作る(`tracks` に、このジャンルで作るトラックと使う SoundFont ID を書く)。
3. **登録簿を確認**: 必要な音源が `config/soundfonts.yaml` に無ければ、ID・name・need(「どんな音源か」を日本語で具体的に)を追記する。名前に確信のない市販/配布 SoundFont 名は書かない。
4. **ユーザーに見せて確認**: 特徴を5〜8行にまとめ(初出の専門用語は括弧で補足)、トラック構成・標準の長さ・必要な SoundFont を示して、ズレがないか聞く(選択肢は最大3)。曲名を例に出すのは確信のある有名曲だけ。旋律・歌詞・リズムの複製は提案しない。
5. **反映**: 先に `uv run scripts/genre_apply.py <song> <id> --length-seconds <秒> --run-mode <step|auto> --dry-run`、問題なければ実行。出力の「曲の長さ → 小節数」を `01-structure` の決定材料にする。
6. **SoundFont 不足なら中断**: 終了コード 3 のとき、表示された「必要な内容・使うトラック・置き場所」をそのままユーザーに伝え、**ここで作業を止める**。用意してもらったら `uv run scripts/soundfont.py check <song>` で再確認してから続きを再開する。
7. 使える音色は `uv run scripts/soundfont.py presets <id>` で調べ、トラック spec の `params.program` を決める根拠にする。
