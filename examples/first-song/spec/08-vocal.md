---
status: draft  # draft | approved | needs-revision
version: 1
depends_on: [06-melody, 07-lyrics]
params:
  model: MERROW
  style_shift: 0
  transpose: 0
  sampling_rate: 48000
  bit_depth: 16
decisions: []  # {date, version, note}
open_questions: []
---
# ボーカル(NEUTRINO)
## 選択肢と聴感
- model: モデルで声質が変わる(MERROW/NAKUMO/REINA/RUNO/SOMA)。ab_render.sh で聴き比べる
- style_shift(-/+): 声の高さの傾向(表情)を調整する
- transpose: 出力の音高をずらす(半音単位)。キーが高すぎ/低すぎるとき
