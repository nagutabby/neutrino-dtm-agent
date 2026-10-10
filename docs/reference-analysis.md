# 参考曲の分析(YouTube → 音声 → MIDI → 雰囲気の言語化)

目的: 「こんな雰囲気の曲を作りたい」を、参考曲の**抽象的な特徴**に翻訳して `spec` に反映する。コーチの対話の材料であり、曲をまねるための機能ではない。

## 使い方
`/reference <song> <YouTube URL>`、または `scripts/reference_run.sh <song> <url>`。
`scripts/reference_run.sh` は次の3段階を順に実行する(個別実行も可):

| 段階 | スクリプト | 出力(`projects/<song>/reference/<video-id>/`) |
|---|---|---|
| 取得 | `reference_fetch.sh` | `audio.wav`、`source.json`(タイトル等) |
| 書き起こし | `reference_to_midi.py`(Basic Pitch / ONNX) | `transcription.mid` |
| 分析 | `reference_analyze.py`(librosa) | `analysis.json`、`analysis.md` |

必要なもの: `brew install yt-dlp ffmpeg`。Python 依存は `uv sync --group reference`(`uv run --group reference` で自動)。

## 分析する特徴
テンポ / キー(長調・短調)/ 小節ごとのコード(ローマ数字=機能で表示。短調は平行長調基準)/ 盛り上がりの形(8分割の音量)/ 音の明るさ / 刻みの細かさ / 書き起こし MIDI の音域・密度。
旋律・歌詞・音符列そのものは出力しない。

## 精度の限界(必ずユーザーに伝える)
- 複数楽器が混ざった音声の書き起こしは不完全。MIDI は音域や密度の傾向を見る目安。
- テンポは倍/半分に誤検出することがある。コード推定は旋律や転調で外れる。
- 推定値はユーザーの耳で確認してから spec に反映する。

## 守ること(厳守)
- **私的な参考分析に限る**。YouTube の利用規約と著作権法を守り、取得する権利のあるコンテンツだけを対象にする。ダウンロードの責任はユーザーにある。
- 取得した音声・書き起こし MIDI は**コミット・公開・再配布しない**(`.gitignore` 済み)。分析結果(`analysis.md/json`)は抽象的な数値のみ。
- 参考曲の**旋律・歌詞・特徴的なリズムパターンを複製しない**。取り入れるのはテンポ感・キーの長短・コード機能の並び・盛り上がりの設計などの一般的な要素まで。
- 「AI が学習する」は、分析結果を材料にコーチが対話することを指す。モデルの学習・ファインチューニングはしない。
- NEUTRINO の出力音声・中間データを参考曲として分析しない(`docs/licensing.md`)。
