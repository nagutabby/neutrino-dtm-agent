# 完成版: Dark Kawaii Future Bass(約100秒 / BPM145 / Fマイナー)。plan = :a の構成を録音した mp3 が songs/73_section_v1.mp3
# 声(ボコーダー)は NEUTRINO で作った wav を sample で鳴らしている(主旋律+下ハモリ+上ハモリ)。wav は配布しないので git に入っていない(work/vocals/ に自分で作る。手順は AGENTS.md「ボーカル」節)
# 73: 約100秒(60小節)のセクション。BPM145 / Fマイナー。各パートが60小節を1回ずつ鳴らして止まる
# plan を :a / :b / :c に変えると構成が切り替わる
#   :a 王道        イントロ8 / ヴァース8 / ビルド8 / ドロップA16 / ブレイク4 / ドロップB16
#   :b ドロップ先出し イントロ4 / ドロップA8 / ヴァース8 / ビルド8 / ドロップB32
#   :c 長いブレイク  イントロ8 / ヴァース8 / ビルド4 / ドロップA16 / ブレイク8 / ドロップB16
# 62: リードを外し、ワブルシンセ(supersaw)がメロディの主役。1小節に1音をしっかり伸ばす
# 73 の変更: 低いピアノ(アルペジオ・ドロップの和音・ビルドの連打)も約0.7倍に下げる(トップノートに合わせる)
# 73 の変更: ワブルに EQ(声と重なる 1〜3kHz 付近を削る)/ ボコーダーの上ハモリを追加 / ピアノのトップノートをさらに小さく(amp 0.18->0.12)
# 72 の変更: ドロップの8小節ごとの最後の2小節で、ワブル・ボコーダー・ピアノを同じシンコペーションで一斉に刻む(tutti)
# 71 の変更: ドロップのワブルとビルドアップのピアノを部分的に刻み、シンコペーションで抑揚をつける
# 70 の変更: ボコーダーの声を刻んでシンコペーションで抑揚をつける(元の声の同じ位置から切り出す)
# 69 の変更: clap を低く(胴鳴り追加・中心 2.1kHz->1.2kHz)、リバーブで伸ばす
# 68 の変更: 67b(ドラムの密度)+67c(厚みと広がり)を採用 / ドロップ前に無音の拍 / ピアノのトップノート・ビブラフォンを小さく硬く / サブベース+ベースの2層にEQ / ボコーダーを大きく+下ハモリ
# 67c の変更: ドロップに厚みと広がり。コードのパッドを左右に重ねる / ワブルの上下の層を左右に振る / 周回ごとに cutoff を開く
# 66 の変更: ボコーダーの声を大きく(amp 0.5->0.9)、滑らかに(調声 v2: smooth 7 / glide-ms 90 / hf-boost 0.2 / cons-boost 0.3、attack-beats 1)
# 65 の変更: ドロップにボコーダーの声(う・あだけ) / イントロのピアノをトップノートから徐々に増やす / ドロップの音量を上げる(drop_gain)
# 64 の変更: ドロップでもピアノを鳴らす(低音の和音を1拍目と3拍目に弱く長く。メロディにしない)
# 63 の変更: clap を追加 / ワブルの揺らぎ(cutoffの振れ幅)を 13->7 に / 1オクターブ上・下のワブルを部分的に重ねる
use_bpm 145
plan = :a
drop_gain = 1.25   # ドロップの音量の倍率(1.25 = 約 +2dB)。大きすぎる/小さすぎるときはここだけ動かす

# --- 区間(0始まりの小節番号) ---
case plan
when :a
  intro  = 0..7;   verse = 8..15;  build = 16..23
  drop_a = 24..39; brk   = 40..43; drop_b = 44..59
  piano_on = [intro, verse, brk]
  vibes_on = [4..15, brk]
  risers   = [[16, 8], [40, 4]]    # [開始小節, 小節数]
  crashes  = [24, 44]              # ドロップの頭のクラッシュ
  brk_end  = 43                    # ブレイク終わりのロール(なければ -1)
when :b
  intro  = 0..3;   drop_a = 4..11; verse  = 12..19
  build  = 20..27; brk    = 0...0; drop_b = 28..59   # ブレイクなし(空の範囲)
  piano_on = [intro, verse]
  vibes_on = [2..3, verse]
  risers   = [[20, 8]]
  crashes  = [4, 28]
  brk_end  = -1
when :c
  intro  = 0..7;   verse = 8..15;  build = 16..19
  drop_a = 20..35; brk   = 36..43; drop_b = 44..59
  piano_on = [intro, verse, brk]
  vibes_on = [4..15, brk]
  risers   = [[16, 4], [40, 4]]
  crashes  = [20, 44]
  brk_end  = 43
end

# --- コード進行(区間ごと。1小節に1コード)[根音, 種類] ---
intro_p  = [[:f3, :minor7], [:f3, :minor7], [:db3, :major7], [:db3, :major7]]   # i - VI: 静かに漂う(イントロ・ヴァース)
build_p  = [[:bb2, :minor7], [:db3, :major7], [:eb3, :major7], [:c3, '7']]      # iv - VI - VII - V7: 上へ向かい緊張
drop_a_p = [[:f3, :minor7], [:db3, :major7], [:ab2, :major7], [:eb3, :major7]]  # i - VI - III - VII: 開放感
brk_p    = [[:ab2, :major7], [:eb3, :major7], [:bb2, :minor7], [:c3, '7']]      # III - VII - iv - V7: 明るく浮いてドロップBへ
drop_b_p = [[:f3, :minor7], [:db3, :major7], [:bb2, :minor7], [:c3, '7']]       # i - VI - iv - V7: 締めに向かう

# --- メロディ(ワブルシンセが吹く。1小節に1音)。4小節で1周し、周回ごとに [1周目, 2周目] を交互に ---
drop_a_m = [[:c5, :db5, :eb5, :d5], [:f5, :f5, :g5, :f5]]    # 1周目: C5 から半音・全音で歩く / 2周目: F5 を軸に G5 へ
drop_b_m = [[:c5, :db5, :f5, :e5], [:f5, :ab5, :f5, :g5]]    # 1周目: C7 の E5 で次の Fm の頭(F5)を呼ぶ / 2周目: 高く歌う

# 60小節ぶんの表 prog[小節] = [根音(MIDI番号), 種類] を作る
prog = Array.new(60) { [note(:f3), :minor7] }
[[intro, intro_p], [verse, intro_p], [build, build_p], [drop_a, drop_a_p], [brk, brk_p], [drop_b, drop_b_p]].each do |r, cyc|
  r.each do |b|
    root, type = cyc[(b - r.first) % cyc.size]
    prog[b] = [note(root), type]
  end
end
prog[59] = [note(:f3), :minor7]     # 最後の小節だけ Fm に解決して終わる

# mel[小節] = メロディの音(MIDI番号)。ドロップ以外は nil
mel = Array.new(60)
[[drop_a, drop_a_m], [drop_b, drop_b_m]].each do |r, ms|
  r.each do |b|
    k = b - r.first
    mel[b] = note(ms[(k / 4) % 2][k % 4])
  end
end
mel[59] = note(:f5)                 # 最後は F5 で終わる

# オクターブ重ね: lo = 1オクターブ下、hi = 1オクターブ上を重ねる小節
#   ドロップA: 2周目(5〜8小節目 ...)に下を重ねる / ドロップB: 下は常に、上は2周目だけ重ねる
lo_on = Array.new(60, false)
hi_on = Array.new(60, false)
drop_a.each { |b| lo_on[b] = ((b - drop_a.first) / 4).odd? }
drop_b.each do |b|
  lo_on[b] = true
  hi_on[b] = ((b - drop_b.first) / 4).odd?
end

# ワブルを刻む小節: ドロップAは4小節ごとの最後の小節、ドロップBは4小節ごとの後半2小節
chopped = Array.new(60, false)
drop_a.each { |b| chopped[b] = (b % 4 == 3) }
drop_b.each { |b| chopped[b] = (b % 4 >= 2) }
# 全員で刻む小節(tutti): ドロップの8小節ごとの最後の2小節。ワブル・ボコーダー・ピアノが同じパターンで一斉に鳴る
tutti = Array.new(60, false)
[drop_a, drop_b].each { |r| r.each { |b| tutti[b] = ((b - r.first) % 8 >= 6) } }
tutti[59] = false                                  # 最終小節は F5 を伸ばして終わる
60.times { |b| chopped[b] = true if tutti[b] }     # tutti の小節はワブルも刻む
chopped[59] = false                                # 最終小節は F5 を伸ばして終わる
# 刻みのパターン [16分の位置, 長さ(16分いくつ分), アクセントの強さ]。拍の頭を外した位置から始まる音が多い
chop_a = [[0, 3, 1.0], [3, 3, 0.75], [6, 2, 0.9], [10, 3, 1.0], [13, 3, 0.7]]
chop_b = [[0, 2, 1.0], [3, 2, 0.8], [6, 3, 1.0], [9, 2, 0.75], [12, 4, 0.9]]
pat_of = lambda { |bar| bar.even? ? chop_a : chop_b }   # 小節ごとの刻みパターン(偶数小節=a、奇数小節=b)

# コードのパッド(dsaw)を重ねる小節: ドロップAの2周目・4周目、ドロップBは全部
pad_on = Array.new(60, false)
drop_a.each { |b| pad_on[b] = ((b - drop_a.first) / 4).odd? }
drop_b.each { |b| pad_on[b] = true }

# clap: ノイズ(cnoise)の短いバーストを3回、バンドパスで2kHz付近に絞る。sleep が本体の流れを止めないよう別スレッドで鳴らす
clap = lambda do |amp|
  in_thread do
    with_fx :reverb, room: 0.85, damp: 0.5, mix: 0.4 do      # 残響で伸ばす
      with_fx :lpf, cutoff: 84, amp: amp * 0.5 do                           # 低い胴鳴り(約 650Hz 以下。ピンクノイズ)
        synth :pnoise, attack: 0, sustain: 0.02, release: 0.25, amp: 1.0
      end
      with_fx :rbpf, centre: 86, res: 0.5, amp: amp * 0.5 do                      # 中心を 2.1kHz -> 約 1.2kHz に下げて高域を弱める
        2.times do
          synth :cnoise, attack: 0, sustain: 0, release: 0.03, amp: 1.0
          sleep 0.03
        end
        synth :cnoise, attack: 0, sustain: 0.01, release: 0.3, amp: 1.0
      end
    end
  end
end

# 音 n を、lo から12半音の範囲(lo..lo+11)に収める
win = lambda do |n, lo|
  n += 12 while n < lo
  n -= 12 while n > lo + 11
  n
end

# bar が、いずれかの範囲に入っているか
define :on_air do |bar, *ranges|
  ranges.any? { |r| r.include?(bar) }
end

be    = build.last                                      # ビルドアップの最終小節
fills = [drop_a.last, drop_b.last]                      # ドロップの終わりのタムのフィル
crashes = (crashes + drop_a.step(8).to_a + drop_b.step(8).to_a).uniq.sort   # ドロップ中も8小節ごとにクラッシュ
gap_bars = [drop_a.first - 1, drop_b.first - 1]          # ドロップ直前の小節。最後の1拍を無音にして落差を作る

# ---------- ドラム ----------
live_loop :kick do
  60.times do |bar|
    pat = if on_air(bar, drop_a, drop_b)
            "x.....x.....x.x."
          elsif on_air(bar, build)
            "x...x...x...x..."                          # ビルドは4つ打ちで煽る
          else
            "................"
          end
    pat = pat[0, 12] + "...." if gap_bars.include?(bar)    # ドロップ直前は最後の1拍を無音に
    amp = on_air(bar, build) ? 0.9 + 0.06 * (bar - build.first) : 1.4 * drop_gain
    pat.each_char.with_index do |c, i|
      sample :bd_haus, amp: amp if c == "x"
      sample :drum_heavy_kick, amp: 0.5 * drop_gain if c == "x" && i == 0 && on_air(bar, drop_a, drop_b)   # 1拍目に重い層
      sleep 0.25
    end
  end
  stop
end

# clap: ドロップで3拍目(スネアと重ねる)と、11番目のゴースト(弱く)
live_loop :clap do
  60.times do |bar|
    if on_air(bar, drop_a, drop_b)
      16.times do |i|
        clap.call(1.0 * drop_gain) if i == 8
        clap.call(0.35 * drop_gain) if i == 11
        sleep 0.25
      end
    else
      sleep 4
    end
  end
  stop
end

live_loop :snare do
  60.times do |bar|
    if on_air(bar, drop_a, drop_b)
      16.times do |i|
        if fills.include?(bar) && i >= 12
          sample :drum_tom_hi_hard, amp: 1.0 * drop_gain, rate: 1.5 - (i - 12) * 0.12   # 高いタムが下る
        elsif bar % 4 == 3 && i >= 12                 # 4小節ごとの最後の拍: スネアの16分フィル
          sample :sn_dolf, amp: (0.4 + 0.15 * (i - 12)) * drop_gain
        elsif i == 8
          sample :sn_dolf, amp: 1.2 * drop_gain
          sample :drum_snare_hard, amp: 0.5 * drop_gain
        end
        sleep 0.25
      end
    elsif on_air(bar, verse)
      16.times do |i|
        sample :perc_snap, amp: 0.6 if i == 8
        sleep 0.25
      end
    elsif on_air(bar, build) && bar < be - 3
      16.times do |i|
        sample :sn_dolf, amp: 0.7 + 0.05 * (bar - build.first) if i == 8
        sleep 0.25
      end
    elsif bar == be - 3 || bar == be - 2           # 8分のロール
      8.times do |i|
        sample :sn_dolf, amp: 0.5 + 0.04 * i
        sleep 0.5
      end
    elsif bar == be - 1                            # 16分のロール
      16.times do |i|
        sample :sn_dolf, amp: 0.6 + 0.03 * i
        sleep 0.25
      end
    elsif bar == be                                # 32分のロール。最後の1拍は無音にして溜める
      24.times do |i|
        sample :sn_dolf, amp: 0.7 + 0.02 * i
        sleep 0.125
      end
      sleep 1
    elsif bar == brk_end                           # ブレイクの終わりも16分ロール、最後の1拍は無音
      12.times do |i|
        sample :sn_dolf, amp: 0.6 + 0.03 * i
        sleep 0.25
      end
      sleep 1
    else
      sleep 4
    end
  end
  stop
end

# 高音のドラム(ハット・オープンハット)
live_loop :hat do
  60.times do |bar|
    if on_air(bar, drop_a, drop_b)
      amps = [0.45, 0.15, 0.3, 0.15]
      12.times do |i|
        sample :drum_cymbal_closed, amp: amps[i % 4] * drop_gain, rate: 1.2
        sample :drum_cymbal_open, amp: 0.25 * drop_gain, finish: 0.1, rate: 1.1 if i == 2 || i == 10   # 裏拍のオープンハット
        sleep 0.25
      end
      if bar % 4 == 3 && !fills.include?(bar)
        6.times do |i|                              # 4小節ごとの最後の拍だけ3連ロール
          sample :drum_cymbal_closed, amp: 0.2 + i * 0.05, rate: 1.2
          sleep 1.0 / 6
        end
      else
        4.times do |i|
          sample :drum_cymbal_closed, amp: amps[i] * drop_gain, rate: 1.2
          sleep 0.25
        end
      end
    elsif on_air(bar, verse)
      8.times do |i|
        sample :drum_cymbal_closed, amp: i.even? ? 0.3 : 0.18, rate: 1.2
        sample :drum_cymbal_open, amp: 0.2, finish: 0.12, rate: 1.1 if bar.odd? && i == 7
        sleep 0.5
      end
    elsif on_air(bar, build)
      16.times do |i|
        sample :drum_cymbal_closed, amp: 0.15 + 0.03 * (bar - build.first) + (i % 4 == 0 ? 0.1 : 0), rate: 1.2 unless gap_bars.include?(bar) && i >= 12
        sleep 0.25
      end
    else
      sleep 4
    end
  end
  stop
end

# ---------- サブベース(sine。F1〜E2)。EQで60Hz付近(low)と100Hz以下(low_shelf)を少し持ち上げて重みを出す(0.25〜0.3だと +5dB で割れる寸前だったので 0.08〜0.1) ----------
live_loop :sub do
  with_fx :eq, low_shelf: 0.08, low_shelf_note: 45, low: 0.1, low_note: 36, low_q: 0.8 do
    60.times do |bar|
      if on_air(bar, drop_a, drop_b)
        root = win.call(prog[bar][0], 29)               # F1(29)〜E2(40)の範囲の根音
        riff = { 1 => [root, 3], 8 => [root, 2], 10 => [root + 7, 2], 15 => [root + 12, 1] }
        16.times do |i|
          n = riff[i]
          if n
            use_synth :sine
            play n[0], attack: 0.01, sustain: n[1] * 0.25 - 0.06, release: 0.05, amp: 1.5 * drop_gain
          end
          sleep 0.25
        end
      else
        sleep 4
      end
    end
  end
  stop
end

# ---------- ベース(saw を1オクターブ上に。軽く歪ませて短く切る)。EQで130Hz付近を持ち上げ、300Hz付近のこもりを削る ----------
live_loop :bass do
  with_fx :eq, low: 0.1, low_note: 48, low_q: 0.8, mid: -0.15, mid_note: 62 do
    with_fx :distortion, distort: 0.3, mix: 0.5 do
      60.times do |bar|
        if on_air(bar, drop_a, drop_b)
          root = win.call(prog[bar][0], 29)
          riff = { 1 => [root, 3], 8 => [root, 2], 10 => [root + 7, 2], 15 => [root + 12, 1] }
          16.times do |i|
            n = riff[i]
            if n
              use_synth :saw
              play n[0] + 12, attack: 0.01, sustain: n[1] * 0.25 * 0.7 - 0.06, release: 0.05, cutoff: 78, amp: 0.45 * drop_gain
            end
            sleep 0.25
          end
        else
          sleep 4
        end
      end
    end
  end
  stop
end

# ---------- ワブルシンセ = メロディの主役(supersaw)。1小節に1音を伸ばし、頭で前の音から短くスライドして入る ----------
# 主音に、1オクターブ下(lo_on の小節)と1オクターブ上(hi_on の小節)を重ねる
live_loop :wobble do
  # 声(ボコーダー)と重なる 1〜3kHz 付近を削る: mid を 1.5kHz 付近で -0.2、2.6kHz 以上の high_shelf を -0.3
  with_fx :eq, mid: -0.2, mid_note: 90, mid_q: 0.6, high_shelf: -0.3, high_shelf_note: 100 do
    60.times do |bar|
      if on_air(bar, drop_a, drop_b) && chopped[bar]    # 刻む小節: 音を伸ばさず、シンコペーションで鳴らし直す
        use_synth :supersaw
        m = mel[bar]
        kicks = [0, 6, 12, 14]
        duck = [0.5, 0.7, 0.85, 1.0]                  # 刻む小節は沈みを浅くして、音の頭が聞こえるようにする
        layers = [[0, 0.9 * drop_gain, 0]]
        layers << [-12, 0.55 * drop_gain, -0.35] if lo_on[bar]
        layers << [12, 0.3 * drop_gain, 0.35] if hi_on[bar]
        t0 = 0
        pat_of.call(bar).each do |st, len, acc|
          sleep((st - t0) * 0.25)
          t0 = st
          d = duck[[st - (kicks.select { |k| k <= st }.max || 0), 3].min]
          layers.each do |off, a, pn|
            play m + off, attack: 0.01, sustain: [len * 0.25 - 0.1, 0.05].max, release: 0.15, cutoff: 88, detune: 0.3, res: 0.2,
              amp: a * acc * d * (tutti[bar] ? 1.15 : 1.0), pan: pn
          end
        end
        sleep((16 - t0) * 0.25)
      elsif on_air(bar, drop_a, drop_b)
        use_synth :supersaw
        m = mel[bar]
        prev = (bar > 0 && mel[bar - 1]) || m           # 前の小節の音(なければ同じ音)
        kicks = [0, 6, 12, 14]
        duck = [0.1, 0.4, 0.7, 1.0]                   # キックからの距離で音量が戻る(サイドチェイン風)
        layers = [[0, 0.9 * drop_gain, 0]]            # [オクターブのずれ, 音量, pan]
        layers << [-12, 0.55 * drop_gain, -0.35] if lo_on[bar]
        layers << [12, 0.3 * drop_gain, 0.35] if hi_on[bar]
        synths = layers.map do |off, a, pn|
          s = play prev + off, note_slide: 0.2, attack: 0.02, sustain: 4, release: 0.8, cutoff: 70, detune: 0.3, res: 0.2,
            amp: a, pan: pn, amp_slide: 0.06, cutoff_slide: 0.12
          control s, note: m + off                    # 0.2拍かけて m へスライド
          s
        end
        r, t = prog[bar]
        pads = []
        if pad_on[bar]                                 # コードのパッド: 左右に振った dsaw(音量は小さく、キックで沈む)
          use_synth :dsaw
          [-0.6, 0.6].each do |pn|
            chord(r, t).each do |n|
              pads << (play n, attack: 0.1, sustain: 4, release: 0.8, cutoff: 78, detune: 0.2, amp: 0.08 * drop_gain, pan: pn, amp_slide: 0.06)
            end
          end
        end
        ds = on_air(bar, drop_a) ? drop_a.first : drop_b.first
        lift = [(bar - ds) / 4, 3].min * 3             # 周回ごとに cutoff の中心を 0, 3, 6, 9 と開く
        last = 0
        32.times do |j|
          i = j / 2
          last = i if j.even? && kicks.include?(i)
          synths.each_with_index do |s, k|
            control s, cutoff: 82 + lift + 7 * Math.sin(j * Math::PI / 4), amp: layers[k][1] * duck[[i - last, 3].min]
          end
          pads.each { |s| control s, amp: 0.08 * drop_gain * duck[[i - last, 3].min] }
          sleep 0.125
        end
      else
        sleep 4
      end
    end
  end
  stop
end

# ---------- ピアノ(低音域で背後から支える。ローパスで高域を削る) ----------
live_loop :piano do
  60.times do |bar|
    if on_air(bar, *piano_on)
      r, t = prog[bar]
      # イントロはトップノートだけから始めて、少しずつ音を増やしメロディに昇格する(lvl 0〜3)。ヴァース以降は lvl 3
      lvl = on_air(bar, intro) ? (bar - intro.first) * 4 / intro.size : 3
      tones = chord(win.call(r + 12, 60), t)            # 60〜71の範囲のコードトーン(Fmなら F4 Ab4 C5 Eb5)
      top = [[0, tones[3], 4]]                           # lvl0: トップノート(7度)を1つだけ伸ばす
      top = [[0, tones[3], 2], [2, tones[2], 2]] if lvl == 1                          # lvl1: 2音
      top = [[0, tones[2], 1], [1, tones[3], 1], [2, tones[2], 1], [3, tones[1], 1]] if lvl == 2   # lvl2: 4分で歩く
      top = [[0, tones[3], 2], [2, tones[2], 2]] if lvl == 3                          # lvl3: 低いアルペジオの上でメロディ
      b  = win.call(r - 12, 36)
      cs = chord(b, t)
      notes = [cs[0], cs[2], cs[1], cs[3], cs[2], b + 14, cs[3], cs[2]]   # 根音・5度・3度・7度・5度・9度・7度・5度
      with_fx :lpf, cutoff: 90 do
        with_fx :reverb, room: 0.7, mix: 0.3 do
          use_synth :piano
          in_thread do                                   # トップノートのメロディ
            t0 = 0
            top.each do |at_beat, n, len|
              sleep at_beat - t0
              t0 = at_beat
              play n, vel: 0.4, hard: 0.7, sustain: len * 0.7, release: 0.4, amp: 0.12, pan: 0.1 unless gap_bars.include?(bar) && at_beat >= 2   # トップノート: 小さく硬く
            end
          end
          if lvl == 3                                    # 低いアルペジオはlvl3から
            8.times do |i|
              play notes[i], vel: 0.4, hard: 0.2, amp: 0.32, pan: -0.2 unless gap_bars.include?(bar) && i >= 6
              sleep 0.5
            end
          else
            sleep 4
          end
        end
      end
    elsif on_air(bar, drop_a, drop_b)                   # ドロップ: 低音の和音(根音・5度・3度)を1拍目と3拍目に。背後から支える
      r, t = prog[bar]
      b  = win.call(r - 12, 36)
      cs = chord(b, t)
      low = [cs[0], cs[2], cs[1] + 12]                  # Fmなら F2 C3 Ab3
      with_fx :lpf, cutoff: 85 do
        with_fx :reverb, room: 0.7, mix: 0.3 do
          use_synth :piano
          if tutti[bar]                                      # 全員で刻む小節: 同じリズムで低い和音を打つ
            t0 = 0
            pat_of.call(bar).each do |st, len, acc|
              sleep((st - t0) * 0.25)
              t0 = st
              play low, vel: 0.45 * acc, hard: 0.25, sustain: [len * 0.25 - 0.1, 0.05].max, release: 0.3, amp: 0.28 * drop_gain * acc, pan: -0.2
            end
            sleep((16 - t0) * 0.25)
          else
            2.times do
              play low, vel: 0.35, hard: 0.15, sustain: 1.5, release: 0.8, amp: 0.28 * drop_gain, pan: -0.2
              sleep 2
            end
          end
        end
      end
    elsif on_air(bar, build)                            # コードを8分で連打。小節ごとに強くなる
      r, t = prog[bar]
      with_fx :lpf, cutoff: 90 do
        with_fx :reverb, room: 0.6, mix: 0.25 do
          use_synth :piano
          vel0 = [0.3 + 0.05 * (bar - build.first), 0.65].min
          if bar >= build.first + build.size / 2           # ビルドの後半: シンコペーションの連打(アクセントで抑揚)
            t0 = 0
            [[0, 1.0], [3, 0.8], [6, 0.9], [10, 1.0], [13, 0.85]].each do |st, acc|
              next if gap_bars.include?(bar) && st >= 12
              sleep((st - t0) * 0.25)
              t0 = st
              play chord(win.call(r - 12, 36) + 12, t), vel: [vel0 * acc * 1.15, 0.8].min, hard: 0.3, amp: 0.32
            end
            sleep((16 - t0) * 0.25)
          else                                             # ビルドの前半: 8分の連打
            8.times do |i|
              play chord(win.call(r - 12, 36) + 12, t), vel: vel0, hard: 0.3, amp: 0.32 unless gap_bars.include?(bar) && i >= 6
              sleep 0.5
            end
          end
        end
      end
    else
      sleep 4
    end
  end
  stop
end

# ---------- ボコーダーの声(う・あだけ)を刻む。元の声の同じ位置から、シンコペーションのリズムで切り出して鳴らす ----------
# 4小節で1周。[16分の位置, 長さ(16分いくつ分), アクセントの強さ]。声は16拍 = 64個の16分
vocal_chop = [
  [[0, 3, 1.0], [3, 3, 0.75], [6, 2, 0.9], [10, 3, 1.0], [13, 3, 0.7]],   # 1小節目: 3-3-2 のあと裏から
  [[0, 2, 1.0], [3, 2, 0.8], [6, 3, 1.0], [9, 2, 0.75], [12, 4, 0.9]],    # 2小節目: 短く跳ねて、最後は伸ばす
  [[0, 3, 1.0], [3, 3, 0.7], [7, 2, 0.9], [10, 2, 1.0], [13, 3, 0.8]],    # 3小節目: 7番目(裏の裏)から入る
  [[1, 2, 0.9], [3, 3, 1.0], [6, 2, 0.7], [10, 3, 1.0], [14, 2, 0.9]]     # 4小節目: 頭を空けて裏から入る
]
voc_dir = "/Users/nagutabby/sonicpi-live-agent/work/vocals/"
live_loop :vocal do
  15.times do |q|                                   # 4小節ごと
    bar = q * 4
    main = nil
    if on_air(bar, drop_a)
      main = voc_dir + "03_ua_a_tuned_voc_v2.wav"
      low  = voc_dir + "05_ua_a_low_tuned_voc_v1.wav"   # 下ハモリ(3度下)
      high = voc_dir + "07_ua_a_high_tuned_voc_v1.wav"  # 上ハモリ(3度上)
    elsif on_air(bar, drop_b)
      main = voc_dir + "04_ua_b_tuned_voc_v2.wav"
      low  = voc_dir + "06_ua_b_low_tuned_voc_v1.wav"
      high = voc_dir + "08_ua_b_high_tuned_voc_v1.wav"
    end
    if main
      4.times do |k|
        t = 0
        (tutti[bar + k] ? pat_of.call(bar + k) : vocal_chop[k]).each do |st, len, acc|
          acc *= 1.1 if tutti[bar + k]                       # 全員で刻む小節は少し強く
          sleep((st - t) * 0.25)
          t = st
          s0 = (k * 16 + st) / 64.0
          s1 = s0 + len / 64.0
          sample main, start: s0, finish: s1, amp: 1.35 * acc, attack: 0.008, release: 0.06, pan: 0
          sample low,  start: s0, finish: s1, amp: 0.85 * acc, attack: 0.008, release: 0.06, pan: -0.3
          sample high, start: s0, finish: s1, amp: 0.55 * acc, attack: 0.008, release: 0.06, pan: 0.3
        end
        sleep((16 - t) * 0.25)
      end
    else
      sleep 16
    end
  end
  stop
end

# ---------- ビブラフォン(pretty_bell + トレモロ。コードトーンを2つ) ----------
live_loop :vibes do
  60.times do |bar|
    if on_air(bar, *vibes_on)
      r, t = prog[bar]
      tones = chord(win.call(r + 12, 60), t)          # 60〜71の範囲の根音(Fmなら F4 Ab4 C5 Eb5)
      pair = bar.even? ? [2, 3] : [1, 2]
      pair = [pair.first] if gap_bars.include?(bar)      # ドロップ前は2音目を鳴らさない
      with_fx :reverb, room: 0.5, mix: 0.12 do
        with_fx :tremolo, phase: 0.5, depth: 0.25, wave: 0 do
          pair.each do |k|
            use_synth :pretty_bell
            play tones[k], attack: 0.002, sustain: 0.25, release: 0.45, amp: 0.5, pan: 0.3   # 小さく、短く硬く
            sleep 2
          end
        end
      end
    else
      sleep 4
    end
  end
  stop
end

# ---------- riser(ノイズの hpf が上がり、saw の音程が F3->F5 へ上がる) ----------
live_loop :riser do
  t = 0
  risers.each do |st, n|
    sleep st * 4 - t
    len = n * 4
    with_fx :rhpf, cutoff: 50, res: 0.4, cutoff_slide: len do |f|
      control f, cutoff: 125
      s = synth :noise, attack: 0, sustain: len - 1, release: 0.1, amp: 0.05, amp_slide: len   # ドロップの1拍前に止める
      control s, amp: 0.7
      p = synth :saw, note: :f3, note_slide: len, attack: 0, sustain: len - 1, release: 0.1, cutoff: 90, amp: 0.03, amp_slide: len
      control p, note: :f5, amp: 0.2
      sleep len
    end
    t = st * 4 + len
  end
  stop
end

# ---------- ドロップの頭のクラッシュ ----------
live_loop :crash do
  t = 0
  crashes.each do |b|
    sleep b * 4 - t
    sample :drum_cymbal_soft, amp: 1.2
    t = b * 4
  end
  stop
end
