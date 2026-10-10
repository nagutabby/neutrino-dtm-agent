---
name: spec-propose
description: 次に決める spec 要素の選択肢(最大3)を、聴感への効果つきで提示する。
---

1. `uv run scripts/spec_status.py <song>` で次に決められる要素を確認(依存元が approved のもの)。
2. `docs/spec-options.md` の該当要素の選択肢を基に、最大3案と音への効果を示す。ユーザー案があれば優先。
3. 決まったら spec を更新(params・decisions)し、`approve.py <song> <spec> --reason ...`(ユーザーの承認発言後のみ)。
4. 未承認の依存元がある要素は提案しない。
