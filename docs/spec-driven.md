# スペック駆動の制作

**spec(`projects/<song>/spec/*.md`)が唯一の正**。決まった要素だけを AI が作り、修正は spec から。

## spec ファイル
`00-concept` `01-structure` `02-harmony` `03-drums` `04-bass` `05-chords` `06-melody` `07-lyrics` `08-vocal` `09-mix`(標準)+ ジャンルが要るトラックを `10-xxx` 以降で追加。
**使うトラックはジャンルで決まる**(`genre-research` が曲ごとに `projects/<song>/genre/<id>.md` を作る → `genre_apply.py` が曲に反映)。使わないトラックの spec ファイルは作らない/削除される。

frontmatter: `status`(draft/ready/needs-revision)、`version`、`depends_on`、`params`(機械可読。spec_check の基準)、`decisions`(決定と理由=学習ログ)、`open_questions`。標準外のトラック spec は `label` / `track` も持つ。
- `00-concept`: `vocal`、`run_mode`(step/auto)、`params.genre` `params.target_seconds` `params.tracks`(`[{spec, track, patch}]`)
- `01-structure.params`: `key` `scale` `tempo` `time_signature` `bars`(`bars` は `target_seconds × tempo / 60 / 拍子の拍数` から換算)
- トラック spec の `params`: `range`(`[C1, C3]` のように音名)、`sound`(ユーザーが指示した音の原文)、`patch`(その曲の `projects/<song>/synth/patches.yaml` の ID。省略は concept のトラック計画。AI が既定を補うことはない)、`patch_params`(パッチ引数の上書き。ドラムは `{kick: {tune: 45}}`)
- `09-mix` の `depends_on` の既定は「曲にあるトラック spec すべて」(インストは歌詞・ボーカルを除く)

## ループ
1. 立案: 次に決められる要素(`spec_status.py`)について選択肢(最大3)と聴感への効果を提示(`auto` は AI が選ぶ)。**コード進行・トラックの音・サンプリングは立案しない**(曲の最初にユーザーが指示した `user_inputs.yaml` の内容だけ)
2. 決定: spec が埋まったら `decide.py <song> <spec>` で ready に。**依存元が ready でなければ決定も生成もしない**。ユーザーの承認を待つゲートではない
3. 生成: ready の spec のみを入力に作り、`register_track.py` で spec_versions を記録
4. フィードバック → spec の**差分案**(例: 音域 C1〜C2→C2〜C3)→ ユーザーが了承したら version+1、`decisions` に追記
5. 再生成: stale になる要素(`spec_check.py` の `[stale]`)を一覧で示し、確認後に v(N+1) として作り直す(旧版は残す)

## 進め方(run_mode)
`step`=1トラックごとに提示して確認 / `auto`=最後まで作り切って最後にまとめて提示。最初にユーザーに聞き、`00-concept` に記録する。

## 音色(シンセ)
音は SuperCollider でゼロから合成する(例外: ユーザーが用意した wav)。音色は**曲ごとの専用**で、他の曲・共通の既存音色は流用しない。トラックは `params.patch` でその曲のパッチ ID を指定し、`patch_params` で引数を上書き。登録簿は `projects/<song>/synth/patches.yaml`、実体は `projects/<song>/synth/synthdefs.scd`。ユーザーの最初の指示(コード進行・トラックと音・サンプリング)は `projects/<song>/user_inputs.yaml`。`patches.py check <song>` が ID・引数名・サンプルの置き場の誤りを検出する(終了コード 2)。仕組みと各引数の効き方は `docs/synthesis.md`。

## ルール
- 生成物(MIDI/MusicXML)を直接直さない。ユーザーが自分で編集した場合のみ、取り込み→spec 逆更新を提案する
- 雛形: `docs/templates/spec/`、標準外トラック: `docs/templates/track-spec.md`、ジャンル: `docs/genres/_template.md`
