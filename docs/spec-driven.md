# スペック駆動の制作

**spec(`projects/<song>/spec/*.md`)が唯一の正**。決まった要素だけを AI が作り、修正は spec から。

## spec ファイル
`00-concept` `01-structure` `02-harmony` `03-drums` `04-bass` `05-chords` `06-melody` `07-lyrics` `08-vocal` `09-mix`

frontmatter: `status`(draft/approved/needs-revision)、`version`、`depends_on`、`params`(機械可読。spec_check の基準)、`decisions`(決定と理由=学習ログ)、`open_questions`。
- `01-structure.params`: `key` `scale` `tempo` `time_signature` `bars`
- トラック spec の `params.range`: `[C1, C3]` のように音名で音域

## ループ
1. 立案: 次に決められる要素(`spec_status.py`)について選択肢(最大3)と聴感への効果を提示
2. 承認: ユーザーが決めたら `approve.py <song> <spec>`。**依存元が approved でなければ承認も生成もしない**
3. 生成: approved spec のみを入力に作り、`register_track.py` で spec_versions を記録
4. フィードバック → spec の**差分案**(例: 音域 C1〜C2→C2〜C3)→ 承認で version+1、`decisions` に追記、status は approved のまま(再承認の確認を取った上で)
5. 再生成: stale になる要素(`spec_check.py` の `[stale]`)を一覧で示し、確認後に v(N+1) として作り直す(旧版は残す)

## ルール
- 生成物(MIDI/MusicXML)を直接直さない。ユーザーが自分で編集した場合のみ、取り込み→spec 逆更新を提案する
- `approved.json` は派生物。手で編集しない
- 雛形: `docs/templates/spec/`
