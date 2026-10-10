---
name: genre-research
description: ユーザーが選んだジャンルの音楽的特徴(テンポ・リズム・和声・音色・構成・尺)を調べ、トラック構成と使うシンセパッチを決めて曲に反映する。
---

前提: ジャンルはユーザーに聞いて決まっている(推測しない)。

1. **定義を探す**: `uv run scripts/genre_apply.py --list` と `docs/genres/` に該当ジャンルがあるか。あれば読んで 2 は省く(曲固有の調整が要るときだけ追加で調べる)。
2. **無ければ調べる**: WebSearch で、そのジャンルの ①テンポ帯とノリ(ハーフタイム/スウィング等) ②リズムの型 ③典型のスケール・コード進行 ④定番の楽器・音色 ⑤標準的な曲構成と尺 ⑥ミックスの傾向 を確認する。複数の情報源で裏を取り、確信のない点は「推定」と書く。`docs/genres/_template.md` を元に `projects/<song>/genre/<id>.md` を作る(`tracks` に、このジャンルで作るトラックと使う patch ID を書く)。
3. **パッチを確認**(音は必ず SuperCollider で作る。サンプル・SoundFont・外部音源は使わない): `patches.py list` で足りるか見る。足りなければ `synth/synthdefs.scd` に SynthDef を足し、`config/patches.yaml` に ID・name・desc・params(引数と既定値)を追記する(引数名は SynthDef と一致させる。`uv run pytest` が検査する)。
4. **ユーザーに見せて確認**: 特徴を5〜8行にまとめ(初出の専門用語は括弧で補足)、トラック構成・標準の長さ・使うパッチ(音の作り)を示して、ズレがないか聞く(選択肢は最大3)。曲名を例に出すのは確信のある有名曲だけ。旋律・歌詞・リズムの複製は提案しない。
5. **反映**: 先に `uv run scripts/genre_apply.py <song> <id> --length-seconds <秒> --run-mode <step|auto> --dry-run`、問題なければ実行。出力の「曲の長さ → 小節数」を `01-structure` の決定材料にする。
6. **パッチ検査**: `genre_apply.py` の最後に `patches.py check` が走る。終了コード 2 なら表示されたエラーを直してから続ける。
7. パッチの引数は `uv run scripts/patches.py show <id>` で調べ、トラック spec の `patch_params` を決める根拠にする。
