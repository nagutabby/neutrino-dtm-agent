---
status: draft  # draft | approved | needs-revision
version: 1
depends_on: [03-drums, 04-bass, 05-chords, 08-vocal]
params:
  loudness_lufs: -14
  levels_db: {drums: -3, bass: -4, chords: -8, melody: -4, vocal: 0}  # 歌なしの曲は vocal 不要
  pan: {chords: -0.2}
decisions: []  # {date, version, note}
open_questions: []
---
# ミックス
## 方針
- ボーカルを主役にして、伴奏は少し下げる(歌なしの曲は melody を主役に)
- 歌なしの曲は depends_on から 08-vocal を外してよい(その曲の spec だけ書き換える)
- approved になると mix_tracks.sh が levels_db(dB)・pan(-1 左〜+1 右)・loudness_lufs を反映する
- 低音(ベース・キック)は中央、コード楽器は少し左右に振ると隙間ができる
- 全体の音量(ラウドネス)は -14 LUFS 前後が配信の目安
