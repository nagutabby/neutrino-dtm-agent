---
name: coach-start
description: 新しい曲を始めるとき。目的・好み・使える時間を最大3問で確認し、projects/<song> と 00-concept の下書きを作る。
---

1. 目的・好きな雰囲気/参考曲・使える時間を **最大3問**(AskUserQuestion、聴感ベースの選択肢)で聞く。
2. 曲名を決め、`scripts/new_song.sh <song>` を実行(先に `--dry-run` で確認)。
3. 回答を `spec/00-concept.md` に下書きし、承認を取る(`approve.py`)。
4. `uv run scripts/spec_status.py <song>` で次に決める要素を案内する。
