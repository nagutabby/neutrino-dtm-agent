---
name: spec-propose
description: 次に決める spec 要素の選択肢(最大3)を、聴感への効果つきで提示する。
---

1. `uv run scripts/spec_status.py <song>` で次に決められる要素を確認(依存元が ready のもの)。
2. 選択肢の元は `projects/<song>/genre/<ジャンル>.md`の特徴と、`docs/spec-options.md` の観点。**ジャンルに合う案**を最大3つ、聴感の効果に加えて**具体的な曲名(「〇〇のような感じ」)**を添えて示し、「これと同じ感じでよいか」で聞く。確信のある有名曲のみ。ユーザー案があれば優先。トラック spec の `patch` / `patch_params` は `patches.py list` / `show <id>` に実在するものから選ぶ。
3. `run_mode: auto` ではユーザーに聞かず、ジャンル定義・参考曲分析・concept から最良の案を AI が選んで決め、`decisions` に理由を残す(後で `spec-revise` で直せる)。`step` ではユーザーが選ぶ。
4. 決まったら spec を更新(params・decisions)し、`decide.py <song> <spec> --reason ...` で ready にする。
5. 依存元が ready でない要素は提案しない。
