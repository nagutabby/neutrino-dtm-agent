---
name: ai-check
description: トラック生成後・最終ミックス後に、AI 生成音楽にありがちな問題(ループの貼り合わせ・起伏のなさ・機械的な強弱・帯域の偏り・ステレオの狭さ)を数値でチェックし、直し方を spec の差分案として示す。
---

1. `uv run --group reference scripts/ai_check.py <song> --all`(MIDI だけなら `--midi tracks/NN_x_vN.mid`、ミックスだけなら `--mix mix/stepN_vN.wav`)。基準と直し方は `docs/ai-music-pitfalls.md`。
2. 警告を「何が/なぜ/直し方」で伝える。黙って直さない。ジャンルの特性で許容できる項目は理由を添えて外す。
3. 自動で測れない項目(無難な和声・主役の不在)は、聴きどころ(何秒付近)を添えてユーザーに確認する。
4. 直す場合は `spec-revise`(spec の差分案 → 了承 → version+1 → 影響範囲を一覧で確認 → 再生成)。生成物を直接直さない。
5. `run_mode: step` はトラックごとの技術解説のあとに、`auto` は最終ミックスのあとにまとめて実行・報告する。
