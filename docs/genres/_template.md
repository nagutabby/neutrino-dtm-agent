---
# ジャンル定義の雛形。ジャンル別の定義は予め用意しない。曲ごとに projects/<song>/genre/<id>.md を作る。
# ユーザーが選んだジャンルを Web で調べて埋め、ユーザーに内容を確認してもらってから genre_apply.py で曲に反映する。
id: example
name: Example
tempo: {range: [100, 130], default: 120, feel: normal}   # feel: normal | half-time | double-time | swing
scale: [minor]                                           # 典型のスケール(major / minor)
length_seconds: {range: [60, 180], default: 120}
sections:                                                # 標準構成(小節数は目安。曲の長さに合わせて伸縮)
  - {name: intro, bars: 4}
  - {name: main, bars: 16}
# トラック・音色・コード進行はここに書かない(ユーザーが最初に指示する。projects/<song>/user_inputs.yaml)
mix_hint: {levels_db: {drums: -3, bass: -4}, loudness_lufs: -14}
---
# 特徴(AI が読む。1項目1行)
- リズム:
- 和声:
- 音色:
- 構成:
- 出典: (調べた Web ページ・参考曲)
