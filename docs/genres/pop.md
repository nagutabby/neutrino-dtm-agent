---
id: pop
name: ポップ(J-POP 系)
tempo: {range: [90, 150], default: 120, feel: normal}
scale: [major, minor]
length_seconds: {range: [90, 240], default: 150}
sections:
  - {name: intro, bars: 4}
  - {name: A, bars: 8}
  - {name: B, bars: 8}
  - {name: sabi, bars: 8}
  - {name: A2, bars: 8}
  - {name: B2, bars: 8}
  - {name: sabi2, bars: 8}
  - {name: outro, bars: 4}
tracks:
  - {spec: 03-drums, track: drums, label: ドラム, patch: kit_acoustic, role: 8ビート。サビでハイハット・クラッシュを増やす}
  - {spec: 04-bass, track: bass, label: ベース, patch: bass_saw, role: ルート8分で推進力}
  - {spec: 05-chords, track: chords, label: コード楽器, patch: epiano, role: ピアノ/ギターのコード。サビで厚く}
  - {spec: 06-melody, track: melody, label: 歌メロ, patch: lead_square, role: 歌いやすい1オクターブ前後の旋律}
  - {spec: 07-lyrics, track: null, label: 歌詞}
  - {spec: 08-vocal, track: vocal, label: ボーカル, role: NEUTRINO で歌声合成}
mix_hint: {levels_db: {drums: -4, bass: -5, chords: -8, melody: -4, vocal: 0}, loudness_lufs: -14}
---
# 特徴
- 構成: イントロ→A→B→サビ の繰り返し。サビで最も音数・音量・音域が上がる
- 和声: 王道進行(IV-V-iii-vi、vi-IV-I-V など)。サビ前にドミナントで盛り上げる
- リズム: 4つ打ちでない8ビートが基本。テンポ100〜140
- 歌: 1音符1音節、サビは音域が高め、休符で息継ぎ
- 長さ: 2.5〜4分が標準(インストは短くても可)
- 音色: kit_acoustic / bass_saw / epiano / lead_square で足りる。歌声は NEUTRINO で別に合成
