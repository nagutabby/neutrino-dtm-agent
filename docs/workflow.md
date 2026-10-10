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

ディレクトリ: `spec/ tracks/ stems/ mix/ musicxml/ label/{full,mono,timing}/ output/ notes.md approved.json`
トラックの番号は spec の番号(03 drums / 04 bass / 05 chords / 06 melody / 08 vocal)。
