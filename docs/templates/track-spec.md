---
status: draft  # draft | ready | needs-revision
version: 1
label: ラベル
track: track-name  # ファイル名・stem 名に使う(英小文字・数字・-)
depends_on: [01-structure, 02-harmony]
params:
  patch: bass_saw  # config/patches.yaml の ID(patches.py list)
  patch_params: {}  # 音色の上書き。例 {cutoff: 700}。ドラムは {kick: {tune: 45}}
  range: [C2, C4]
  velocity: 90
decisions: []  # {date, version, note}
open_questions: []
---
# ラベル
