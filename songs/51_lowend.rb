# 曲: kawaii future bass(145 BPM、キー C、約93秒)。Sonic Pi で全体をそのまま実行する
# 掛け声の素材: 自分で用意した wav(ishi-ni-san-anime-voice_130bpm.wav)を 1.1 倍速にして使う。
#   ffmpeg -i ishi-ni-san-anime-voice_130bpm.wav -af atempo=1.1 87_user_voice_x1.1_v1.wav
#   できた wav の絶対パスを、下の shout_wav に書き換える

use_bpm 145

# イントロ(ドロップ1の直前)の無音の長さ(拍)。1拍
intro_cut = 1

# ブレイクの終わり(ドロップ2の直前)の無音の長さ(拍)。掛け声が入るので3拍
cut = 3

# 音の長さ(sustain / release)にかける倍率。1 で元の長さ、大きいほど音が伸びる
legato_scale = 2

# supersaw から柔らかい dtri(三角波を2つ重ねた音)に置き換えたぶんの音量補正。dtri は同じ amp だと約8dB大きいので 0.45 倍
dtri_gain = 0.45


# イントロ案C「伸ばしから刻みへ」
# 1〜4小節: コードを1小節ずつ伸ばす(残響を多めに)。5〜8小節: 付点8分の刻みに変わる

live_loop :intro_chords do
  use_synth :dtri
  chords = [
    chord(:F4, :major7),
    chord(:G4, '7'),
    chord(:E4, :minor7),
    chord(:A4, :minor7)
  ]
  with_fx :reverb, room: 0.8, mix: 0.4 do
    chords.each do |c|
      play c, cutoff: 90, attack: 0.5, sustain: 3, release: 1, amp: (0.8) * dtri_gain
      sleep 4
    end
  end
  with_fx :lpf, cutoff: 95 do
    chords.each_with_index do |c, k|
      [0.75, 0.75, 0.75, 0.75, 1].each_with_index do |s, i|
        pos = [0, 0.75, 1.5, 2.25, 3][i]
        # 最後の小節は、無音(intro_cut)の手前までで鳴らすのをやめる
        if k < 3 || pos < 4 - intro_cut
          play c, cutoff: 100 + i * 3, attack: 0.02, sustain: (i == 0 ? 0.6 : 0.1) * legato_scale, release: 0.2 * legato_scale, amp: ((i == 0 ? 1.2 : 0.9) * 0.8) * dtri_gain
        end
        sleep s
      end
    end
  end
  stop
end

# --- イントロのドラム(案C): 8小節を1回鳴らし、終わりに :drop を送る ---
live_loop :intro_drums do
  8.times do |bar|
    with_fx :lpf, cutoff: 70 + 5 * bar do
      if bar < 6
        4.times do
          sample :bd_haus, amp: 1.0
          sleep 1
        end
      elsif bar == 6
        [0.75, 0.75, 0.75, 0.75, 1].each do |d|
          sample :elec_snare, amp: 0.5
          sleep d
        end
      else
        # ロールは (4 - intro_cut) 拍ぶん。残りの intro_cut 拍は無音にして、そのままドロップへ
        ((4 - intro_cut) * 4).to_i.times do |i|
          sample :elec_snare, amp: 0.15 + 0.04 * i
          sleep 0.25
        end
        sleep intro_cut
      end
    end
  end
  cue :drop
  stop
end

# --- ライザー: 5小節目(16拍目)から、無音(intro_cut)の手前まで上がり続ける ---
# 案A: ノイズ。lpf の cutoff が 60 -> 125 に開き、音量が 0.05 -> 0.4 に上がる
live_loop :riser do
  len = 16 - intro_cut
  sleep 16
  with_fx :reverb, room: 0.8, mix: 0.3 do
    s = synth :noise, cutoff: 60, cutoff_slide: len, amp: 0.05, amp_slide: len, attack: 0.01, sustain: len, release: 0.05
    control s, cutoff: 125, amp: 0.4
    sleep len
  end
  stop
end


# 案B「間引き」+リズム補強(リードなし)。シンセ主役: ドラムとベースを下げ、コードと浮遊感を少し大きく(ローパスの調整はしない)。
# キックは0・1.5(弱)・2.25・3.0拍目(付点8分の格子。3.0はスネアと重なる)、スネアは1・3拍目(0始まり)と3.75拍目のゴースト、ハットなし、コードは3+3+2、ベースは1.5・3.5拍目、アルペジオは8分。
# ===== 曲の構成(145 BPM、全56小節 = 約92秒) =====
#  小節   0-8   イントロ        : 伸ばしのコード -> 刻み、4つ打ち、ライザー、1拍の無音のあとドロップ1へ(掛け声なし)
#  小節   8-24  ドロップ1(16)  : 前半8小節は土台(キック・スネア・ハット・コード・ベース・サブ・パッド・浮遊感)、後半8小節でアルペジオが加わる
#  小節  24-36  ブレイク(12)    : ドラム・ベース・サブを抜く。伸ばしのコード(控えめ) + パッド + ストリングスのメロディ(主役)。後半4小節でキック・ライザー・スネアロール、無音のあと掛け声
#  小節  36-52  ドロップ2(16)  : 全部入り(ドロップ1の後半と同じ厚み)
#  小節  52-56  アウトロ(4)     : ドラムを間引いて、最後にシンバル
# 以下の小節番号は「ドロップ1の頭 = 0」から数える(ドロップ1 0-16 / ブレイク 16-28 / ドロップ2 28-44 / アウトロ 44-48)

# 小節 bar が、範囲 ranges([[はじめ, 終わり], ...] 終わりは含まない)のどれかに入っているか
define :on_air do |bar, ranges|
  ranges.any? { |r| bar >= r[0] && bar < r[1] }
end

# 小節 bar のコード番号(0=Fmaj7 1=G7 2=Em7 3=Am7)。最後の小節(47)だけ Fmaj7(IV)に戻して、解決しきらずに終わる
define :chord_i do |bar|
  bar == 47 ? 0 : bar % 4
end

# 変化案(2+3): 転調なし。ドロップ2は「アルペジオを4小節遅らせる -> 8小節目からハット -> 12小節目からメロディのオクターブ上」と少しずつ足す。
# 4小節の最後の小節(3,7,11…)は、キックを間引いてスネアのフィルを入れる。メロディは1周おきに終わりの音を G6 に上げる。
# 転調: 小節 bar(ドロップ1の頭=0)で、全体を何半音ずらすか
define :shift_at do |bar|
  0   # 転調はしない(ほかの方法で変化を付ける)。ずらしたいときはここを 2 などにする
end

# コード(音の配列)を bar の転調ぶんずらす
define :tr_chord do |c, bar|
  c.to_a.map { |n| n + shift_at(bar) }
end

# 終わり方: 最後の小節だけ Fmaj7(IV)。メロディは E6(長7度)で止まり、解決しきらない
# --- ドロップ: :drop を受けて一斉に始まる。各パートは「鳴らす小節の範囲」で出入りする ---
live_loop :kick, sync: :drop do
  48.times do |bar|
    if on_air(bar, [[0, 16], [24, 27], [28, 44]])
      sample :bd_haus, amp: 1.1
      sleep 1.5
      sample :bd_haus, amp: 0.7
      if bar % 4 == 3
        sleep 2.5   # 4小節の最後は、キックを間引いて次の頭を引き立てる
      else
        sleep 0.75
        sample :bd_haus, amp: 0.9
        sleep 0.75
        sample :bd_haus, amp: 0.85
        sleep 1
      end
    else
      sleep 4
    end
  end
  stop
end

live_loop :snare, sync: :drop do
  48.times do |bar|
    if on_air(bar, [[0, 16], [28, 44]])
      sleep 1
      sample :elec_snare, amp: 0.45
      sleep 2
      sample :elec_snare, amp: 0.45
      if bar % 4 == 3
        # 4小節の最後は、16分のフィルで次の頭へ向かう
        [0.2, 0.25, 0.3].each_with_index do |a, i|
          sleep 0.25
          sample :elec_snare, amp: a
        end
        sleep 0.25
      else
        sleep 0.75
        sample :elec_snare, amp: 0.18
        sleep 0.25
      end
    else
      sleep 4
    end
  end
  stop
end

# (案B: ドロップのハットは休み。ドロップ全体でオフビートの刻みをなくして落ち着かせる)

live_loop :chords, sync: :drop do
  use_synth :dtri
  chords = [chord(:F4, :major7), chord(:G4, '7'), chord(:E4, :minor7), chord(:A4, :minor7)]
  48.times do |bar|
    if on_air(bar, [[0, 16], [28, 48]])
      if bar == 47
        play tr_chord(chords[chord_i(bar)], bar), cutoff: 105, attack: 0.05, sustain: 2.5, release: 2.5, amp: (1.1) * dtri_gain
        sleep 4
      else
        [1.5, 1.5, 1].each_with_index do |d, i|
          play tr_chord(chords[chord_i(bar)], bar), cutoff: 105, attack: 0.03, sustain: (i == 0 ? 0.9 : 0.4), release: 0.5, amp: ((i == 0 ? 1.2 : 0.9)) * dtri_gain
          sleep d
        end
      end
    else
      sleep 4
    end
  end
  stop
end

live_loop :bass, sync: :drop do
  use_synth :subpulse
  roots = [:f2, :g2, :e2, :a2]
  48.times do |bar|
    if on_air(bar, [[0, 16], [28, 48]])
      sleep 1.5
      play note(roots[chord_i(bar)]) + shift_at(bar), attack: 0.01, sustain: 1.2, release: 0.5, amp: 0.6
      sleep 2
      play note(roots[chord_i(bar)]) + shift_at(bar), attack: 0.01, sustain: 0.3, release: 0.4, amp: 0.5
      sleep 0.5
    else
      sleep 4
    end
  end
  stop
end

# --- ロングサブ(グライド): 範囲ごとに1本の音を鳴らし続け、小節の最後の0.25拍で次のルートへ滑らせる ---
live_loop :sub, sync: :drop do
  roots = [:f1, :g1, :e1, :a1].map { |r| note(r) }
  pos = 0
  [[0, 16], [28, 48]].each do |r|
    sleep((r[0] - pos) * 4)
    s = synth :sine, note: roots[0] + shift_at(r[0]), note_slide: 0.25, attack: 0.05, sustain: (r[1] - r[0]) * 4 - 0.55, release: 0.5, amp: 0.5
    (r[1] - r[0]).times do |k|
      sleep 3.75
      control s, note: roots[chord_i(r[0] + k + 1)] + shift_at(r[0] + k + 1)
      sleep 0.25
    end
    pos = r[1]
  end
  stop
end

# --- パッド(ストリングス風): ブレイクの最後の小節(27)は無音にするので鳴らさない ---
live_loop :pad, sync: :drop do
  use_synth :blade
  chords = [chord(:f3, :major7), chord(:g3, '7'), chord(:e3, :minor7), chord(:a3, :minor7)]
  with_fx :reverb, room: 0.8, mix: 0.35 do
    48.times do |bar|
      if on_air(bar, [[0, 27], [28, 48]])
        play tr_chord(chords[chord_i(bar)], bar), cutoff: 90, attack: 1, sustain: 2.5, release: (bar == 47 ? 2.5 : 0.5), vibrato_rate: 5, vibrato_depth: 0.1, vibrato_delay: 0.5, amp: (bar >= 16 && bar < 28 ? 1.3 : 0.7)
      end
      sleep 4
    end
  end
  stop
end

# --- アルペジオ(16分の上下): ドロップ1の後半(小節8)から入る。ブレイクは弦を主役にするため休む ---
live_loop :arp, sync: :drop do
  use_synth :pluck
  chords = [chord(:f5, :major7), chord(:g5, '7'), chord(:e5, :minor7), chord(:a5, :minor7)]
  with_fx :reverb, room: 0.7, mix: 0.3 do
    48.times do |bar|
      if on_air(bar, [[8, 16], [32, 48]])
        notes = tr_chord(chords[chord_i(bar)], bar)
        seq = [notes[0], notes[1], notes[2], notes[3], notes[2], notes[1]]
        8.times do |i|
          play seq[i % 6], release: 0.6, amp: (i % 4 == 0 ? 0.5 : 0.35)
          sleep 0.5
        end
      else
        sleep 4
      end
    end
  end
  stop
end

# --- 浮遊感のシンセ(スネアに沿う): ドロップのときだけ ---
live_loop :float, sync: :drop do
  use_synth :dsaw
  chords = [chord(:f4, :major7), chord(:g4, '7'), chord(:e4, :minor7), chord(:a4, :minor7)]
  with_fx :reverb, room: 0.9, mix: 0.5 do
    48.times do |bar|
      if on_air(bar, [[0, 16], [28, 48]])
        notes = tr_chord(chords[chord_i(bar)], bar).map { |n| n + 12 }
        sleep 1
        play notes, cutoff: 90, detune: 0.3, attack: 0.05, sustain: 0.3, release: 2.5, amp: 0.7
        sleep 2
        play notes, cutoff: 90, detune: 0.3, attack: 0.05, sustain: 0.3, release: 2.5, amp: 0.7
        sleep 1
      else
        sleep 4
      end
    end
  end
  stop
end

# ===== ブレイク(小節16-28)専用のパート =====

# 前半8小節(16-24)は伸ばしのコード、後半4小節(24-28)は付点の刻み。最後は無音(cut)の手前でやめる
live_loop :break_chords, sync: :drop do
  use_synth :dtri
  chords = [
    chord(:F4, :major7),
    chord(:G4, '7'),
    chord(:E4, :minor7),
    chord(:A4, :minor7)
  ]
  sleep 16 * 4
  with_fx :reverb, room: 0.8, mix: 0.4 do
    2.times do
      chords.each do |c|
        play c, cutoff: 90, attack: 0.5, sustain: 3, release: 1, amp: (0.9) * dtri_gain
        sleep 4
      end
    end
  end
  with_fx :lpf, cutoff: 95 do
    chords.each_with_index do |c, k|
      [0.75, 0.75, 0.75, 0.75, 1].each_with_index do |s, i|
        pos = [0, 0.75, 1.5, 2.25, 3][i]
        if k < 3 || pos < 4 - cut
          play c, cutoff: 100 + i * 3, attack: 0.02, sustain: (i == 0 ? 0.6 : 0.1) * legato_scale, release: 0.2 * legato_scale, amp: ((i == 0 ? 1.2 : 0.9) * 0.5) * dtri_gain
        end
        sleep s
      end
    end
  end
  stop
end

# ライザー: ブレイクの小節24から、無音(cut)の手前まで上がり続ける
live_loop :break_riser, sync: :drop do
  len = 16 - cut
  sleep 24 * 4
  with_fx :reverb, room: 0.8, mix: 0.3 do
    s = synth :noise, cutoff: 60, cutoff_slide: len, amp: 0.05, amp_slide: len, attack: 0.01, sustain: len, release: 0.05
    control s, cutoff: 125, amp: 0.4
    sleep len
  end
  stop
end

# スネア: 小節26は付点の刻み、小節27は(4 - cut)拍ぶんのロール、残りは無音
live_loop :break_snare, sync: :drop do
  sleep 26 * 4
  [0.75, 0.75, 0.75, 0.75, 1].each do |d|
    sample :elec_snare, amp: 0.5
    sleep d
  end
  ((4 - cut) * 4).to_i.times do |i|
    sample :elec_snare, amp: 0.15 + 0.04 * i
    sleep 0.25
  end
  sleep cut
  stop
end

# --- アウトロのドラム(小節44-48)「間引き」: キックは各小節の頭だけ、ハットは小さくなって消える。最後にシンバル ---
live_loop :outro_drums, sync: :drop do
  sleep 44 * 4
  4.times do |bar|
    sample :bd_haus, amp: 1.5 - 0.3 * bar
    4.times do
      sleep 0.5
      sample :drum_cymbal_closed, amp: 0.3 - 0.07 * bar
      sleep 0.5
    end
  end
  sample :drum_cymbal_open, amp: 0.5
  stop
end

# --- 掛け声: ユーザー用意の wav(1.1倍速)。ブレイクの終わり、ドロップ2(144拍目)の cut 拍前に1回だけ。ドロップ1の前には入れない ---
shout_wav = "/Users/nagutabby/sonicpi-live-agent/work/vocals/87_user_voice_x1.1_v1.wav"

live_loop :shout, delay: 32 + 28 * 4 - cut do
  with_fx :hpf, cutoff: 70 do
    with_fx :reverb, room: 0.5, mix: 0.2 do
      sample shout_wav, amp: 1.8
      sleep 3
    end
  end
  stop
end

# --- ドロップ2の後半(小節36〜)に、疎らなハットを足して高域を少し出す ---
live_loop :hat2, sync: :drop do
  48.times do |bar|
    if on_air(bar, [[36, 44]])
      sleep 1.5
      sample :drum_cymbal_closed, amp: 0.35
      sleep 2
      sample :drum_cymbal_closed, amp: 0.35
      sleep 0.5
    else
      sleep 4
    end
  end
  stop
end

# --- メロディ 案B「付点のフック」(dtri): 付点8分(0.75拍)×4 + 1拍。コードの刻みと同じリズムで、跳ねる。ブレイクは0.7倍 ---
live_loop :pico, sync: :drop do
  use_synth :dtri
  phrase = [
    [:e6, :c6, :a5, :c6, :e6],
    [:d6, :b5, :g5, :b5, :d6],
    [:e6, :b5, :g5, :b5, :e6],
    [:c6, :e6, :a5, :e6, :c6]
  ]
  with_fx :reverb, room: 0.5, mix: 0.2 do
    48.times do |bar|
      if on_air(bar, [[8, 27], [28, 48]])
        level = bar < 28 ? 0.7 : 1.0
        ns = phrase[chord_i(bar)].dup
        ns[4] = :g6 if chord_i(bar) == 3 && (bar / 4).odd?   # 1周おきに、終わりの音を G6(Am7の7度)に上げて開く
        ns.zip([0.75, 0.75, 0.75, 0.75, 1]).each do |n, d|
          play note(n) + shift_at(bar), cutoff: 105, attack: 0.02, sustain: d * 0.5, release: 0.2, amp: (0.4 * level) * dtri_gain
          # ドロップ2の最後の8小節(40〜)は、1オクターブ上を弱く重ねる
          play note(n) + shift_at(bar) + 12, cutoff: 105, attack: 0.02, sustain: d * 0.5, release: 0.2, amp: 0.35 * dtri_gain if bar >= 40
          sleep d
        end
      else
        sleep 4
      end
    end
  end
  stop
end
