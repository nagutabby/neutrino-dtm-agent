---
name: live-improve
description: ユーザーが今鳴らしているコード(current.rb)を、小さな変更案で良くする。『もっと良くしたい』『この音どう?』『気になる』と言われたとき。
---

1. `work/current.rb` を読む(最新か不明ならユーザーに保存し直してもらう)。必要なら `work/notes.md`。
2. ユーザーが気になる点を言っていればそれを最優先。無ければ AGENTS.md の「改善の観点」から**1観点だけ**選ぶ。
3. 案は最大3つ。各案は1つの変更で、コードの該当部分の before → after と数値(`cutoff: 80 → 100` など)で示す。`proposals/NN_<label>.rb` に保存する(`current.rb` は書き換えない)。
4. `uv run scripts/live_check.py work/proposals/NN_<label>.rb` を通す。試聴が有益なら録音前に一言断って `live_render.py proposals/NN_<label>.rb --seconds N`(全体コードの案なら単体、貼り足しなら `current.rb` と一緒に)を実行し、`wav_stats.py` で数値を見る。
5. 「何が変わるか / なぜ(理論+数値)/ 聴きどころ(何秒付近)/ 試せる課題」を短く。再生コマンドを添える。
6. 採否を聞き、`work/notes.md` に1行追記する。採用されたらユーザー自身が貼り替える(依頼されたときだけ `current.rb` を更新)。
