---
name: coach-review
description: ユーザーの聴いた感想から、次の一手(spec の修正案)を示す。
---

0. まだ聴いていなければ `scripts/play.sh <path> [--start 秒]` を提示して聴いてもらう。
1. 感想を聞く(`docs/templates` の聴き返し観点: 速さ・明るさ・低音・歌いやすさ・うるささ)。
2. 原因を技術で説明し、**spec の差分案**を最大3つ提示 → `spec-revise` へ。
3. 学んだことを `notes.md` の下書きに追記(ユーザーが追記・承認)。
