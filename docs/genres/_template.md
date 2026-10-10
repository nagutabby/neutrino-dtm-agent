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
tracks:                                                  # このジャンルで作るトラック。spec 番号=ファイル名。patch は config/patches.yaml の ID(patches.py list)
  - {spec: 03-drums, track: drums, label: ドラム, patch: kit_acoustic, role: 一言で役割}
  - {spec: 04-bass, track: bass, label: ベース, patch: bass_saw, role: 一言で役割}
  # **伴奏は10本以上**(ボーカル・歌詞を除く)。リズム(ドラム・小物打楽器)/低音/和音/旋律/対旋律/厚み(パッド・ストリングス)/動き(アルペジオ)/質感・FX を揃える
  # 標準外のトラックは spec: 10-fx のように 10 以降の番号で足す(label / track 必須。track 名は曲内で重複させない)
  # 歌ありのとき 08-vocal(patch 不要)を足す
mix_hint: {levels_db: {drums: -3, bass: -4}, loudness_lufs: -14}
---
# 特徴(AI が読む。1項目1行)
- リズム:
- 和声:
- 音色:
- 構成:
- 出典: (調べた Web ページ・参考曲)
