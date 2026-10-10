---
id: phonk
name: Phonk
tempo: {range: [120, 150], default: 130, feel: half-time}
scale: [minor]
length_seconds: {range: [60, 180], default: 100}
sections:
  - {name: intro, bars: 4}
  - {name: A, bars: 8}
  - {name: drop, bars: 16}
  - {name: break, bars: 8}
  - {name: drop2, bars: 16}
  - {name: outro, bars: 4}
tracks:
  - {spec: 03-drums, track: drums, label: ドラム, patch: kit_808, role: ハーフタイムのスネア・8分ハット+ロール・カウベル}
  - {spec: 04-bass, track: bass, label: ベース, patch: sub808, role: 歪んだ808ベース。キックと同時打鍵・グライド}
  - {spec: 05-chords, track: chords, label: コード楽器, patch: pad_saw, role: 暗いスタブ/パッド。短調の i と VI の往復が多い}
  - {spec: 06-melody, track: melody, label: リード/カウベル旋律, patch: bell, role: 短い反復フレーズ(カウベル/ダークリード)}
mix_hint: {levels_db: {drums: -3, bass: -4, chords: -9, melody: -6}, loudness_lufs: -14}
---
# 特徴
- リズム: ハーフタイム(スネア3拍目)で重く、ハイハットは8分+16分/3連のロール。カウベルを打楽器兼メロディに使う
- 和声: 短調(自然短音階/フリジアン寄り)。コードは少なく、i↔VI や i↔bVII の往復、ループ中心
- 低音: 808ベースが主役。歪み・ロングトーン・音程スライド。ベースとキックを同時に鳴らして一体化
- 音色: ダーク。カウベル、歪んだリード、ボイスサンプル(Memphis ラップ由来)
- 構成: 短いループを重ね、drop(最も厚い区間)と break(ドラム抜き/薄め)で起伏を作る
- 長さ: 1〜3分。ループ主体で曲が短く、繰り返しが多い
- 音色: sub808(glide・drive で歪みとスライド)、kit_808 のカウベル(ノート56)、bell(カウベル旋律)。ダークさは pad_saw の cutoff を下げて作る
