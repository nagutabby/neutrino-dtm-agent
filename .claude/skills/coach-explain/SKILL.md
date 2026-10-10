---
name: coach-explain
description: 今の操作や用語の理論をやさしく説明する。ユーザーが『なぜ?』と聞いたとき、または専門用語が初出のとき。
---

- 理由 → 数値 → 聴きどころの順で短く。用語は括弧で補い、既出なら `docs/glossary.md` を案内。
- 根拠の数値は `uv run scripts/explain_midi.py <midi>` で取る。`docs/technique-notes.md` を参照。
- 説明のあと、ユーザーが自分で試せる小さな課題を1つ添える(`docs/learning-path.md`)。
