# phonk + NEUTRINO ボコーダー「ら」(F マイナー、130 BPM、全40小節)。work/proposals/81_vocal_vibrato20.rb の保存版。
# 声の wav(vocal_wav)は git に入れていない(*.wav は除外)。docs/vocal-tuning.md の手順で作り、パスを書き換えて使う。

# phonk 構成案: ドロップ前のワクワク感＋ドロップ後の収束感
use_bpm 130
root = :f1
one_loop = true # true: arr を1周(40小節)したら全 live_loop が止まる(録音用)。false で無限ループ

arr = ring(*([:intro] * 4 + [:build] * 2 + [:drop] * 12 + [:break] * 4 +
             [:build] * 2 + [:drop] * 12 + [:outro] * 4))  # ドロップを8→12小節に(全40小節)

# --- リズム ---
live_loop :kick do
  stop if one_loop && tick(:bars) >= arr.size
  if arr[tick % arr.size] == :drop
    2.times do
      pat = (ring 1, 0, 0, 1, 0, 0, 1, 0)
      8.times do |k|
        if pat[k] == 1
          sample :bd_boom, amp: 2.0
          sample :bd_haus, amp: 1.2, cutoff: 100
        end
        sleep 0.25
      end
    end
  else
    sleep 4
  end
end

live_loop :snare do
  stop if one_loop && tick(:bars) >= arr.size
  i = tick % arr.size
  s = arr[i]
  if s == :drop
    sleep 2
    sample :sn_dolf, amp: 1.5
    sample :perc_snap, amp: 1.0
    sleep 2
  elsif s == :build && arr[i + 1] != :build
    12.times do |k|
      sample :sn_dolf, amp: 0.3 + 0.08 * k
      sleep 0.25
    end
    sleep 1
  else
    sleep 4
  end
end

live_loop :hat do
  stop if one_loop && tick(:bars) >= arr.size
  i = tick % arr.size
  s = arr[i]
  if s == :break
    sleep 4
  else
    last_build = (s == :build && arr[i + 1] != :build)
    vol = (s == :drop) ? 1.0 : 0.6
    amps = (ring 0.7, 0.25, 0.4, 0.25)
    16.times do |k|
      sample :drum_cymbal_closed, amp: amps[k] * vol unless last_build && k >= 12
      sleep 0.25
    end
  end
end

# --- 低音 ---
live_loop :bass do
  stop if one_loop && tick(:bars) >= arr.size
  if arr[tick % arr.size] == :drop
    # :level で bass 全体を 0.8 倍(約 -2dB)
    with_fx :level, amp: 0.8 do
      # lpf を外側にして、歪みで増えた高音(倍音)も丸める。cutoff 85→72→64(約330Hz)
      with_fx :lpf, cutoff: 64 do
        with_fx :distortion, distort: 0.5, mix: 0.5 do
          2.times do
            [[0.75, 1.5, 0], [0.75, 1.2, 0], [0.5, 1.2, 1]].each do |len, a, off| # off=1 で最後だけ♭2度
              sub = synth :sine, note: note(root) + 12, note_slide: 0.05, release: len, amp: a * 1.5
              control sub, note: note(root) + off

              mid = synth :saw, note: note(root) + 24, note_slide: 0.05, release: len, amp: a * 0.6
              mid5 = synth :saw, note: note(root) + 31, note_slide: 0.05, release: len, amp: a * 0.4
              control mid, note: note(root) + 12 + off
              control mid5, note: note(root) + 19 + off

              sleep len
            end
          end
        end
      end
    end
  else
    sleep 4
  end
end

# --- 上もの ---
live_loop :chords do
  stop if one_loop && tick(:bars) >= arr.size
  s = arr[tick % arr.size]
  if s == :build
    sleep 4
  else
    use_synth :hollow
    r = note(root) + 24
    p_chord = [r, r + 7, r + 10]

    sleep 0.5
    play p_chord, release: 0.6, amp: 1.6
    sleep 0.75
    play p_chord, release: 0.6, amp: 1.3
    sleep 2.75
  end
end

# --- 展開に合わせたダイナミックなメロディ ---
live_loop :phonk_melody do
  stop if one_loop && tick(:bars) >= arr.size
  i = tick % arr.size
  s = arr[i]
  r = note(root) + 24

  # 【Drop用】パワー感のあるフレーズ
  drop_phrase1 = [[r, 0.75], [r + 7, 0.75], [r + 10, 0.5], [r + 7, 0.75], [r, 1.25]]
  drop_phrase2 = [[r, 0.75], [r + 7, 0.75], [r + 12, 0.5], [r + 10, 0.75], [r + 7, 1.25]] # 後半に高音オクターブアクセント

  # 【Build用】徐々に細かくなりピッチが上がるワクワク感パターン（2小節分）
  is_second_build = (s == :build && arr[i + 1] != :build)
  build_phrase = if !is_second_build
    # Build 1小節目: ゆったりオクターブ上昇
    [[r, 1.0], [r + 7, 1.0], [r + 12, 2.0]]
  else
    # Build 2小節目: 細かく刻んで高揚感を煽る
    [[r + 7, 0.5], [r + 10, 0.5], [r + 12, 0.5], [r + 14, 0.5], [r + 12, 0.25], [r + 14, 0.25], [r + 15, 0.5], [nil, 1.0]]
  end

  # 【Break / Outro用】音数を最小限にした収束感パターン
  break_phrase = [[r, 2.0], [nil, 2.0]]

  # セクションごとのフレーズ割り当て
  current_phrase = case s
  when :drop
    (i % 2 == 0) ? drop_phrase1 : drop_phrase2
  when :build
    build_phrase
  else
    break_phrase
  end

  # フィルターのカットオフ値を展開で動かす（Break/Outroでは篭もらせて収束感を出す）
  lpf_val = case s
  when :drop then 120
  when :build then (is_second_build ? 130 : 90)
  else 60 # Break/Intro/Outroはフィルターを閉じる
  end

  with_fx :lpf, cutoff: lpf_val do
    with_fx :reverb, room: 0.8, mix: (s == :break ? 0.6 : 0.3) do # Breakでは残響を伸ばす
      with_fx :distortion, distort: (s == :drop ? 0.3 : 0.1) do
        current_phrase.each do |n, len|
          if n
            synth :pretty_bell, note: n, release: (s == :drop ? 0.8 : 1.2), amp: 1.0
            synth :pretty_bell, note: n + 7, release: 0.6, amp: 0.5 if s == :drop
            synth :saw, note: n - 12, release: 0.5, amp: 0.4, cutoff: 85 if s == :drop
            if s == :drop || s == :build
              # 高音の弦楽器: 2オクターブ上の blade。ゆっくり立ち上げ、ビブラートを遅れてかける
              synth :blade, note: n + 24, attack: 0.2, sustain: len * 0.8, release: 0.5, amp: 0.4,
                cutoff: 100, vibrato_rate: 5.5, vibrato_depth: 0.15, vibrato_delay: 0.3
              # 低音の管楽器: 1オクターブ下の hollow(息っぽい音色)
              synth :hollow, note: n - 12, attack: 0.15, sustain: len * 0.7, release: 0.4, amp: 1.2, cutoff: 80
            end
          end
          sleep len
        end
      end
    end
  end
end

# --- ドロップで足す音 ---
live_loop :impact do
  stop if one_loop && tick(:bars) >= arr.size
  i = tick % arr.size
  if arr[i] == :drop && arr[i - 1] != :drop
    sample :drum_cymbal_open, amp: 1.2
    sample :bd_boom, amp: 2.0
  end
  sleep 4
end

live_loop :riser do
  stop if one_loop && tick(:bars) >= arr.size
  i = tick % arr.size
  if arr[i] == :build && arr[i - 1] == :build
    with_fx :hpf, cutoff: 60, cutoff_slide: 4.0 do |f|
      control f, cutoff: 130
      synth :noise, attack: 4.0, release: 0.1, amp: 0.8
      sleep 4
    end
  else
    sleep 4
  end
end

# --- ボコーダー「ら」: 唸り + 湧き上がり(12小節 = 48拍。ドロップの頭で1回だけ鳴らす) ---
# 作り方: 78_la_legato.json → neutrino_sing → neutrino_tune(vocoder)
#         → vocode --beats 48 --vibrato 20 --dynamics --attack-beats 1
#         (唸り(growl)はノイズが多いのでやめ、ビブラートと声の強弱に置き換えた。息継ぎなし)
vocal_wav = "/Users/nagutabby/sonicpi-live-agent/work/vocals/78_la_legato_tuned_voc_v3.wav"

live_loop :vocal_la do
  stop if one_loop && tick(:bars) >= arr.size
  i = tick % arr.size
  if arr[i] == :drop && arr[i - 1] != :drop
    with_fx :reverb, room: 0.8, mix: 0.35 do
      # attack: 全体の立ち上がり(4拍かけて音量が湧く)。amp 0.65→1.1(唸り・歪みをやめて RMS が約 5.6dB 下がったぶん)
      sample vocal_wav, amp: 1.1, attack: 4, pan: 0
    end
  end
  sleep 4
end
