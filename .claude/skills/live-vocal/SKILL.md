---
name: live-vocal
description: NEUTRINO で歌わせた声を調声してボコーダー変換し、Sonic Pi に載せるボーカルのステムを作る。『ボーカルを足して』『ボコーダーで歌わせて』と言われたとき。
---

AGENTS.md「ボーカル」節と `docs/vocal-tuning.md` に従う。1回に1フレーズ(4〜8小節)・案は最大3つ。

1. `work/current.rb` からキー・BPM・コード進行・展開(どこで鳴らすか)を読み取る(推測しない)。読み取れなければ聞く。
2. 意味のないひらがなの歌詞とメロディを `work/vocals/NN_<label>.json` に書く(コードトーン中心、MIDI 55〜72、音符は小節をまたがない、合計は小節数×4拍)。実行前に「NEUTRINO を動かす(音は鳴らない・CPU を使う)」と一言伝える。
3. `uv run scripts/neutrino_sing.py work/vocals/NN_<label>.json`(歌声合成)。
4. `uv run scripts/neutrino_tune.py work/vocals/NN_<label>_vN --preset vocoder`(調声)。出力された「音高のずれ」「4kHz 以上の比」を読み、足りなければパラメータを**1つだけ**動かして作り直す(版は進み、上書きしない)。
5. `uv run scripts/vocode.py <tuned>.wav <tuned>.f0 --bpm <BPM> --beats <拍数>`(ボコーダー変換。頭の1小節の無音は自動で捨てる)。`wav_stats.py` でピーク・帯域比を確認。
6. `proposals/NN_vocal_*.rb` に `live_loop`(`sample "<絶対パス>"` を拍数だけ `sleep`、`arr` や展開に合わせて鳴らす位置を決める)を書き、`live_check.py` を通す。重ねた録音は、録音前に一言断る。
7. 解説(母音の響き・子音の位置・既存ステムとの帯域)、聴く箇所(秒)、試せる課題を1つ添える。採否を聞き、採用なら `work/notes.md` に追記する。
8. 英語の響きが欲しいとき、または NEUTRINO を動かさず軽く試したいときは `docs/vocal-helper.rb`(`vsing`)を使う。
