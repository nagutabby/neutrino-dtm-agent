# 曲ごとのワークフロー

```
spec 立案 → 承認 → 生成(approved のみ) → 検証 → 提示(単体+累積) → 技術解説 → 承認ゲート
     ↑                                                                        │
     └── 気になる点 → spec の差分案 → 承認 → version+1 → 該当+下流を再生成 ←──┘
```

1. `scripts/new_song.sh <song>` で `projects/<song>/` と spec 雛形を作る
2. `spec_status.py <song>` で次に決められる要素を確認
3. 要素ごとに spec を決める(`spec-propose`)→ ユーザー承認 → `approve.py <song> <spec>`
4. approved の spec から MIDI を作り、`register_track.py <song> <spec> <midi>` で版と spec_version を記録
5. `midi_validate.py`、`explain_midi.py` で検証と数値根拠 → `render_track.sh` で stems/ → `mix_tracks.sh` で累積ミックス
6. 技術解説とともに提示し、承認(`approve.py <song> <spec> --track-version N`)
7. ボーカル: 歌詞付き MusicXML(`midi_to_musicxml.sh` → `lyrics_inject.py` → `musicxml_validate.py`)→ `synth.sh`
8. 修正は必ず spec から(`spec-revise` → `spec-regenerate`)。`spec_check.py` で stale を確認

試聴: `scripts/play.sh <path> [--start 秒] [--loop]`(音声は mpv、MIDI は fluidsynth)、`scripts/play.sh --list <song>` で一覧。

ディレクトリ: `spec/ tracks/ stems/ mix/ musicxml/ label/{full,mono,timing}/ output/ notes.md approved.json`
トラックの番号は spec の番号(03 drums / 04 bass / 05 chords / 06 melody / 08 vocal)。

複数曲: 曲ごとに `projects/<song>/` を分ける。スクリプトは常に `<song>` を引数に取り、他の曲のファイルには触れない。曲の複製は `cp -r` でなく新規作成+spec の再承認で行う(承認状態を引き継がない)。

スクリプト側のガード: ファイル名引数(トラック名・basename・モデル名)に `/` や `..` は使えない。`mix_tracks.sh` の step は数字のみ。`register_track.py` は別の曲の `projects/<other>/` 配下の MIDI を拒否する。

参考曲がある場合: spec 立案の前に `/reference` で雰囲気を分析し、`spec/00-concept.md` の下書きに反映する(`docs/reference-analysis.md`)。
