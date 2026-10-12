---
name: coach-explain
description: 今のコードや用語の理論をやさしく説明する。ユーザーが『なぜ?』と聞いたとき、または専門用語が初出のとき。
---

- まず `docs/learning-log.md` を `uv run scripts/learning_log.py search <語>` で探し、過去に使った技法・選んだ案に当たれば、その番号(L0xx)を示して要点を振り返る。
- 理論の理由は `docs/music-theory.md`(度数・コード機能・終止・声部連結・コードトーン等)、Sonic Pi の技法は `docs/live-coding.md` から選ぶ。初出の理論用語は一度に最大2つ。
- 理由(理論) → 数値(`amp`・`cutoff`・`sleep`・音域など、ユーザーのコードの値) → 聴きどころの順で短く。用語は括弧で補い、既出なら `docs/glossary.md` を案内。
- 説明のあと、ユーザーが自分で試せる小さな課題を1つ添える(`docs/learning-path.md`)。
- 数値で断定できない理論判断(機能・終止感)は推定と明示し、コード名とローマ数字を根拠に添える。
