---
id: lofi
name: Lo-fi Hip Hop
tempo: {range: [65, 90], default: 80, feel: swing}
scale: [major, minor]
length_seconds: {range: [60, 180], default: 90}
sections:
  - {name: intro, bars: 4}
  - {name: A, bars: 8}
  - {name: B, bars: 8}
  - {name: A2, bars: 8}
  - {name: outro, bars: 4}
tracks:
  - {spec: 03-drums, track: drums, label: ドラム, patch: kit_acoustic, role: ゆるいブームバップ。ベロシティを弱めスウィング}
  - {spec: 04-bass, track: bass, label: ベース, patch: bass_saw, role: ルート中心でまろやか。音は短め}
  - {spec: 05-chords, track: chords, label: エレピ, patch: epiano, role: 7th/9th のジャジーなコードをゆったり}
  - {spec: 06-melody, track: melody, label: リード, patch: pluck, role: ギターやエレピの控えめな旋律}
mix_hint: {levels_db: {drums: -5, bass: -5, chords: -6, melody: -8}, loudness_lufs: -16}
---
# 特徴
- リズム: 70〜90BPM。16分/8分をスウィング(裏拍を遅らせる)し、ベロシティを不揃いにして「よれ」を出す
- 和声: maj7/m7/9th などテンションコード。ii-V-I や IVmaj7-iiim7 などジャズ寄りの循環
- 音色: エレピ(Rhodes 系)、柔らかいギター、ほこり感のあるドラム。音圧は控えめ
- 構成: 短いループの繰り返し。展開より雰囲気の持続
- 長さ: 1〜3分
- 音色: epiano(index を下げるとまろやか)、pluck の控えめな旋律。ベースは bass_saw の cutoff を下げて丸く
