# ボコーダー風ボーカル用ヘルパー(Sonic Pi 内蔵のみ)
# 使い方: このファイルの define 部分を proposals/NN_vocal_*.rb の先頭に貼り、末尾の例のように live_loop から vsing を呼ぶ。
# 歌詞は意味のない音節(ローマ字)。母音の響きと子音の質感を聴くためのもの。

# 母音のフォルマント(Hz)。定数だと再実行で警告が出るので define にしている。F1, F2, F3 の共鳴。数値は目安で、耳で調整する。
define :formants do |v|
  tbl = {
    "a" => [800, 1200, 2500],
    "i" => [300, 2300, 3000],
    "u" => [350, 1200, 2400],
    "e" => [500, 1900, 2500],
    "o" => [500, 900, 2400]
  }
  tbl.fetch(v, tbl["a"])
end

# 1音節を鳴らす(sleep はしない。呼び出し側の live_loop で dur 分 sleep する)。syl は "ka" "ra" "n" "a" などのローマ字、nt は音高(note)、dur は長さ(拍)。
# 母音は saw を F1/F2/F3 の bpf 3 つに通して作る。子音の頭に短いノイズを足す。
define :vsing do |syl, nt, dur, amp_v = 1.0, pan_v = 0|
  cons = syl[0..-2]
  fs = formants(syl[-1])
  if %w[s sh h f].include?(cons)
    synth :noise, release: 0.08, amp: amp_v * 0.25, pan: pan_v
  elsif %w[t k p ch].include?(cons)
    synth :pnoise, release: 0.03, amp: amp_v * 0.3, pan: pan_v
  end
  fs.each_with_index do |f, i|
    with_fx :bpf, centre: hz_to_midi(f), res: 0.85, amp: [1.0, 0.6, 0.3][i] * amp_v do
      synth :saw, note: nt, attack: 0.02, sustain: [dur - 0.1, 0.05].max, release: 0.08,
        cutoff: 130, amp: 1.2, pan: pan_v
    end
  end
end

# --- 例(C マイナー。current.rb のキー・音域に合わせて書き換える) ---
live_loop :vocal do
  with_fx :reverb, room: 0.6, mix: 0.3 do
    syls = (ring "ka", "ra", "ri", "o", "ma", "na")
    notes = (ring :c4, :eb4, :g4, :bb4, :g4, :eb4)
    lens = (ring 1.0, 0.5, 0.5, 1.0, 1.0, 1.0)
    vsing syls.tick, notes.look, lens.look, 0.9, -0.1
  end
  sleep lens.look
end
