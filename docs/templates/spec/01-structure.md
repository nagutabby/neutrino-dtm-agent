---
status: draft  # draft | approved | needs-revision
version: 1
depends_on: [00-concept]
params:
  key: C
  scale: major  # major | minor
  tempo: 120
  time_signature: "4/4"
  bars: 8
sections: []  # 例: [{name: サビ, bars: 8}]
decisions: []  # {date, version, note}
open_questions: []
---
# 曲構成
キー・テンポ・拍子・小節数・曲構成。生成物の検査(spec_check.py)の基準になる。

## 選択肢の例
- キー: C(白鍵だけで分かりやすい) / 歌いやすい高さに合わせて後から移調
- テンポ: 80〜100(ゆったり) / 110〜130(ポップ) / 140〜(速い)。遅いほど歌詞の音数は少なくなる
- 構成: まず「サビ8小節」だけ → 慣れたら A→B→サビ
