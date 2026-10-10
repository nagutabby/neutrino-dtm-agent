---
status: draft  # draft | approved | needs-revision
version: 1
depends_on: [01-structure, 06-melody]
syllables_per_phrase: []  # 各フレーズの音節数(メロディの音符数と一致させる)
decisions: []  # {date, version, note}
open_questions: []
---
# 歌詞
1音符1音節。読みはひらがなで、音節をスペース区切りで書く(拗音は1音節: きゃ)。

## 歌詞(読み)
# 例:
# き ら き ら ひ か る
## メモ
- 音符数と音節数が一致しなければ lyrics_inject.py はエラーになる
- 言葉の強い音節(アクセント)は強拍に置くと自然
