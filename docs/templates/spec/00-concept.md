---
status: draft  # draft | ready | needs-revision
version: 1
depends_on: []
vocal: true  # true=歌あり | false=インスト(最初に決める)
mode: beginner  # beginner | standard
run_mode: step  # step=1ステップごとに確認 | auto=すべて作り切る(最初に聞く)
params:  # genre_apply.py が埋める
  genre: ""  # docs/genres/<id>.md
  target_seconds: 0  # 曲の長さ(秒)。小節数は 01-structure で換算
  tracks: []  # [{spec, track, patch}] ジャンルのトラック計画
level: 1  # 1〜3(docs/learning-path.md)
decisions: []  # {date, version, note}
open_questions: []
---
# コンセプト
