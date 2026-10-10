# 曲ごとのワークフロー

```
5問(参考曲・ジャンル・長さ・歌/インスト・進め方) → ジャンル調査 → トラック計画・音色パッチ検査・サウンドチェック(全トラックの試奏を SuperCollider で作って確認)
  → spec 立案 → 決定(ready) → 生成 → 検証 → 提示(単体+累積) → 技術解説 → [step: 進行確認]
        ↑                                                              │
        └── 気になる点 → spec の差分案 → 了承 → version+1 → 該当+下流を再生成 ←┘
```

1. `scripts/new_song.sh`(名前は `日付-連番` で自動)で `projects/<song>/` と spec 雛形を作る
2. 参考曲の URL → `/reference`、ジャンル・曲の長さ・歌/インスト・進め方を聞く(`coach-start`)
3. `genre-research` でジャンルを調べ、`genre_apply.py <song> <genre> --length-seconds N --run-mode step|auto` でトラック計画・音色(patch)を反映。登録簿にない patch はエラー(`patches.py check <song>`)
4. `spec_status.py <song>` で次に決められる要素を確認し、要素ごとに spec を決める(`spec-propose`)→ `decide.py <song> <spec>`
5. ready の spec から MIDI を作り、`register_track.py <song> <spec> <midi>` で版と spec_version を記録
6. `midi_validate.py`、`explain_midi.py` で検証と数値根拠 → `render_track.sh`(音源は spec から自動)で stems/ → `mix_tracks.sh` で累積ミックス(各トラックの最新版。固定は `track=N`)
7. 技術解説とともに提示。`step` は1本ごとに「次へ/修正/やり直し/自分で直す」を確認、`auto` は最後にまとめて提示
8. ボーカル: 歌詞付き MusicXML(`midi_to_musicxml.sh` → `lyrics_inject.py` → `musicxml_validate.py`)→ `synth.sh`
9. 修正は必ず spec から(`spec-revise` → `spec-regenerate`)。`spec_check.py` で stale を確認

試聴: `scripts/play.sh <path> [--start 秒] [--loop]`(音声は mpv。MIDI は SuperCollider で一時合成して再生)、`scripts/play.sh --list <song>` で一覧。

ディレクトリ: `spec/ tracks/ stems/ mix/ musicxml/ label/{full,mono,timing}/ output/ genre/(任意) notes.md`
トラックの番号は spec の番号(03 drums / 04 bass / 05 chords / 06 melody / 08 vocal / 10〜 ジャンル固有)。

複数曲: 曲ごとに `projects/<song>/` を分ける。スクリプトは常に `<song>` を引数に取り、他の曲のファイルには触れない。曲の複製は `cp -r` でなく新規作成+spec の作り直しで行う。

スクリプト側のガード: ファイル名引数(トラック名・basename・モデル名)に `/` や `..` は使えない。`mix_tracks.sh` の step は数字のみ。`register_track.py` は別の曲の `projects/<other>/` 配下の MIDI を拒否する。

参考曲がある場合: spec 立案の前に `/reference` で雰囲気を分析し(YouTube 取得 → 音源分離 → 音声の分析 → ジャンル確定後に類似曲を Web 検索して同じ手順で分析 → `reference_summary.py` で共通点をまとめる)、`spec/00-concept.md` に反映する(`docs/reference-analysis.md`)。
