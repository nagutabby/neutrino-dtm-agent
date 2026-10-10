---
status: draft  # draft | approved | needs-revision
version: 1
depends_on: [01-structure, 02-harmony]
params:
  range: [C4, C5]
  motif: ''  # 例: 「ソ・ソ・ラ・ソ」のようなリズム/音の短い型
  strong_beat: chord-tone  # 強拍にコード構成音を置く
decisions: []  # {date, version, note}
open_questions: []
---
# 歌メロ
ユーザーが先に書く(ハミングを音名で書く、鍵盤で弾く、など)→ AI が改善案を2つ。

## 方針の選択肢
- 音域は1オクターブ程度(C4〜C5)に収める → 歌いやすい
- 強拍にコード構成音を置く → 和音と馴染む
- 同じリズムを繰り返し(モチーフ)、最後だけ変える → 覚えやすい
- フレーズの切れ目に休符 → 息継ぎ
