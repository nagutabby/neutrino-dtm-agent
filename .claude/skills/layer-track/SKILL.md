---
name: layer-track
description: トラックを1本ずつ作り、単体+累積ミックスを提示、技術解説して承認を得る固定フロー。
---

予告 → 生成(approved spec のみ、最大3案) → 検証(`midi_validate.py`/`spec_check.py`) → `register_track.py` → `render_track.sh`(単体 stem)→ `mix_tracks.sh`(承認済みのみ累積) → 提示(パスと聴きどころ) → **技術解説(数値付き)** → AskUserQuestion(採用/修正/やり直し/自分で直す) → 承認なら `approve.py <song> <spec> --track-version N` と `notes.md` 追記。
承認前に次のトラックへ進まない。1ステップ1トラック。
