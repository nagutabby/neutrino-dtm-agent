---
name: live-start
description: ユーザーが Sonic Pi のライブコーディングで曲を始めるとき。プロジェクトを作り、ユーザーのコードを読んで現状(テンポ・キー・鳴っているステム・足りない要素)を把握する。
---

1. `scripts/setup.sh` で環境を確認(✘ があれば直し方を伝えて止まる)。
2. 曲が未作成なら `scripts/new_session.sh --dry-run` → 実行。「いま扱う曲は `<song>`」と宣言。
3. ユーザーのコードを `projects/<song>/current.rb` に保存してもらう(貼ってもらえば AI が保存してよい)。空なら、狙い(雰囲気・テンポ・キー)を自由記述で1問だけ聞く。候補・例は出さない。
4. `uv run scripts/live_check.py projects/<song>/current.rb` を通し、コードを読んで `session.md` に BPM(`use_bpm`)・キー/スケール・鳴っているステム(`live_loop` ごと)を書く。読み取れない項目は本人に聞く。
5. 現状を3行で要約し、次の選択肢(① 今の音を改善 / ② 次のステムを提案 / ③ 自分で進める)を伝える。決めるのはユーザー。
