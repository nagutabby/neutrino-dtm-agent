---
name: spec-revise
description: ユーザーのフィードバックやレビューの指摘を受け、spec の差分案を出して(step は了承後、auto は自動で)version を上げる。生成物は直接直さない。
---

1. 気になる点の原因を技術で説明する。
2. 該当 spec の **差分(before→after)** を提示(例: range C1〜C2 → C2〜C3、velocity 100 → 80)。
3. `step` はユーザーが了承したら、`auto` は了承を待たずに(差分案を最終報告に載せて)、spec の `version` を +1、`decisions` に日付と理由を追記、`status` は ready のまま(`needs-revision` にしていたなら `decide.py` で戻す)。
4. 次は `spec-regenerate`。生成物(MIDI/MusicXML)は直接編集しない。
