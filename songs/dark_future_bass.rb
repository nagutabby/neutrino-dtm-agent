# Dark Future Bass(完成版 v1)/ 68小節 ≒ 125.5秒 / BPM130・F ナチュラルマイナー / スタイル②(AI がコードを書き、ユーザーが聴いて方向を決めた)
#
# ■ 声(ボーカルチョップ)の素材について
#   声の wav(NEUTRINO で作った歌声をボコーダーにかけたもの)は、NEUTRINO の利用許諾により配布しない。このファイルは、下のパスに wav があるときだけ声が鳴る。
#   作り直すには(NEUTRINO を ~/NEUTRINO に置き、このリポジトリの scripts/ で。譜面の JSON は下に書いておく):
#     1) work/vocals/01_arp_a.json と 01_arp_b.json を作る(中身は下)
#     2) uv run scripts/neutrino_sing.py work/vocals/01_arp_a.json   (b も同じ)
#     3) uv run scripts/neutrino_tune.py work/vocals/01_arp_a_v1 --preset vocoder --pitch-lock 1.0   (b も同じ)
#     4) uv run scripts/vocode.py work/vocals/01_arp_a_tuned_v2.wav work/vocals/01_arp_a_tuned_v2.f0 --bpm 130 --beats 16   (b も同じ)
#        → work/vocals/01_arp_a_tuned_voc_v2.wav と 01_arp_b_tuned_voc_v2.wav ができる(下の vox_a・vox_b が指すファイル。パスは自分の環境に直す)
#   01_arp_a.json = {"bpm": 130, "notes": [["", "", 0.25], ["ら", "F4", 0.5], ["な", "Ab4", 0.25], ["お", "C5", 0.5], ["い", "Eb4", 0.75], ["ら", "C5", 1.0], ["な", "Ab4", 0.75], ["", "", 0.25], ["ま", "F4", 0.5], ["な", "Ab4", 0.25], ["あ", "C5", 0.5], ["い", "Db4", 0.75], ["ら", "C5", 1.0], ["お", "Ab4", 0.75], ["", "", 0.25], ["ら", "G4", 0.5], ["な", "Ab4", 0.25], ["お", "C5", 0.5], ["い", "Eb4", 0.75], ["ま", "C5", 1.0], ["あ", "Ab4", 0.75], ["", "", 0.25], ["な", "F4", 0.5], ["ら", "Bb4", 0.25], ["あ", "D4", 0.5], ["お", "F4", 0.75], ["い", "D4", 1.0], ["ら", "Bb4", 0.75]]}
#   01_arp_b.json = {"bpm": 130, "notes": [["", "", 0.25], ["ら", "F4", 0.5], ["な", "Ab4", 0.25], ["お", "C5", 0.5], ["い", "Eb4", 0.75], ["ら", "C5", 1.0], ["な", "Ab4", 0.75], ["", "", 0.25], ["ま", "F4", 0.5], ["な", "Ab4", 0.25], ["あ", "Bb4", 0.5], ["い", "Db4", 0.75], ["ら", "Bb4", 1.0], ["お", "Ab4", 0.75], ["", "", 0.25], ["ら", "F4", 0.5], ["な", "Ab4", 0.25], ["お", "C5", 0.5], ["い", "Db4", 0.75], ["ま", "C5", 1.0], ["あ", "Ab4", 0.75], ["", "", 0.25], ["な", "G4", 0.5], ["ら", "Bb4", 0.25], ["あ", "D4", 0.5], ["お", "Eb4", 0.75], ["い", "D4", 1.0], ["ら", "Bb4", 0.75]]}
#
# Dark Future Bass / 通しの全体(68小節 = 272拍 ≒ 125.5秒 + アウトロの余韻)/ BPM130・F ナチュラルマイナー
# 構成: イントロ 1-8(Pad のみ)→ ビルド 9-16 → ドロップA 17-32 → ビルドアップ 33-44(ブレイクの置き換え。stem を2小節ごとに増やす)→ ドロップB 45-60 → アウトロ 61-68(Pad のみ + 余韻)
# 各セクションは define の中に変数を閉じ込め(同じ名前を使っても混ざらない)、in_thread で必要な回数だけ回す。最後に in_thread の中で順に呼ぶ。
# 規約: docs/coding-rules.md。下のヘルパーは docs/live-grid.rb と同じ(貼り付け済み)
use_bpm 130

# グリッド記法のヘルパー(Sonic Pi 内蔵のみ)。規約は docs/coding-rules.md、検証は scripts/live_check.py。
# 使い方: このファイルの define 部分を current.rb の先頭(use_bpm の次)に貼る。使い方の例は examples/grid_demo.rb。
# 名前はすべて grid_ で始める(Sonic Pi のコア API の名前と衝突させないため)。
#
# グリッド: 既定は 1小節 = 4拍 = 16マス(1マス = 16分音符 = 0.25拍)。空白と | は見やすくするだけで無視される。
#   X = 強く(1.0) / x = ふつう(0.75) / o = 弱く(0.4) / 1〜9 = 強さを 0.1〜0.9 で細かく指定
#   . = 休み / - = 直前の音を1マス伸ばす(例: "x-- " は3マスぶん)
#   例: "x... x... x... x..." (四つ打ち)  ".... ..x. .... ..x." (裏拍)
# 小節数はマスの数から決まる(既定は 16マス = 1小節)。パターンは 1小節のマス数の倍数にする。
# 解像度と拍子(1曲で1つに固定。use_bpm の次に1回だけ書く。既定は grid_res 4 / grid_meter 4):
#   grid_res N   = 1拍あたりのマス数。4 = 16分音符 / 3 = 8分3連 / 6 = 16分3連 / 2 = 8分音符
#   grid_meter N = 1小節の拍数(4分音符いくつ分)。4 = 4/4(16マス)/ 3 = 3/4(12マス)/ 5 = 5/4(20マス)
#   1小節のマス数 = grid_res × grid_meter。3/4 = res 4, meter 3 / 6/8 = res 2, meter 3(8分音符6つ)/ 4/4 の3連符 = res 3, meter 4(12マス)
#   付点8分 = 0.75拍 = res 4 で 3マス("x--")。3連符は res 3 か 6 にする。
#
# 関数(どれもパターン・指定した長さぶん sleep する):
#   grid_play  voice, pattern, on:, chord:, steps:, fold:, note:   音を鳴らす
#   grid_chop  clip, pattern, from:, base:           元の wav を切り貼りして鳴らす
#   grid_roll  voice, 回数, 拍数, amp0:, amp_step:, rate0:, rate_step:   連打(だんだん強く・速く)
#   grid_each  pattern do |位置, 長さ(マス), 強さ, 文字| … end   音ごとに自分で書く(複雑な音色・FX用)
#   grid_ticks 拍数, 回数 do |k| … end              等間隔に n 回(cutoff をなめらかに動かすときなど)
# 音の立ち上がり・立ち下がり(grid_voice と grid_chop のオプション。数字でも書ける。単位は拍):
#   attack: :instant(0)/ :fast(0.01)/ :mid(0.1)/ :slow(0.4)     release: :cut(0.03)/ :short(0.15)/ :mid(0.4)/ :long(1.0)
#   env: 型で一括指定。:pluck(急に立ち上がって短く切る)/ :stab(急・やや短い。Future Bass のシンセ)/ :pad(ゆっくり立ち上がって長く残る)/ :swell(だんだん大きくなって急に切る)
#   env: と attack: / release: を両方書いたら、attack: / release: が優先
#   grid_rest  拍数                                   休み
# grid_play と grid_chop を呼ぶ live_loop では、sleep を別に書かない(二重に待つ)。

$grid_res = 4
$grid_meter = 4

define :grid_res do |n|
  $grid_res = n
end

define :grid_meter do |n|
  $grid_meter = n
end

# 1マスの長さ(拍)と、1小節のマス数
define :grid_step do
  1.0 / $grid_res
end

define :grid_bar_cells do
  $grid_res * $grid_meter
end

# 立ち上がり・立ち下がりの言葉(attack: / release: / env:)を数字(拍)にする。数字はそのまま通す。知らない言葉はエラー
define :grid_env do |opts|
  attacks = { instant: 0, fast: 0.01, mid: 0.1, slow: 0.4 }
  releases = { cut: 0.03, short: 0.15, mid: 0.4, long: 1.0 }
  types = { pluck: [:instant, :cut], stab: [:fast, :short], pad: [:slow, :long], swell: [:slow, :cut] }
  o = opts.dup
  e = o.delete(:env)
  raise "grid: env: :#{e} は知らない型です(#{types.keys.join(' ')})" if e && !types[e]
  a = o[:attack] || (e && types[e][0])
  r = o[:release] || (e && types[e][1])
  raise "grid: attack: :#{a} は知らない言葉です(#{attacks.keys.join(' ')})" if a.is_a?(Symbol) && !attacks[a]
  raise "grid: release: :#{r} は知らない言葉です(#{releases.keys.join(' ')})" if r.is_a?(Symbol) && !releases[r]
  o[:attack] = attacks.fetch(a, a) if a
  o[:release] = releases.fetch(r, r) if r
  o
end

# 音に名前を付ける。kind は :synth か :sample、name はシンセ名・サンプル名(またはパス)、opts は音色のパラメータ
# シンセの音の長さは、パターンの長さから決まる: sustain = マス数 × 1マスの長さ × gate - cut(gate 既定 1.0 / cut 既定 0。gate・cut は音色のパラメータには渡さない)
define :grid_voice do |kind, name, opts = {}|
  { kind: kind, name: name, opts: grid_env(opts) }
end

# コード進行に名前を付ける。1小節に1つ [根音, 種類]。例: grid_prog [:f3, :minor7], [:db3, :major7]
define :grid_prog do |*chords|
  chords
end

# 元の wav に名前を付ける。path は wav のパス、beats は元の長さ(拍。例: 16 = 4小節)
define :grid_clip do |path, beats|
  { name: path, beats: beats.to_f }
end

define :grid_cells do |pattern|
  pattern.delete(" |\n\t").chars
end

# 音の強さ: o < x < X、数字は 0.1〜0.9
define :grid_level do |c|
  { "X" => 1.0, "x" => 0.75, "o" => 0.4 }[c] || (c =~ /\A[1-9]\z/ ? c.to_i / 10.0 : nil)
end

# 1つの音の長さ(マス数): 自分 + 直後に続く "-" の数
define :grid_len do |cells, i|
  n = 1
  n += 1 while cells[i + n] == "-"
  n
end

# 音 n を、lo から12半音の範囲(lo..lo+11)に収める
define :grid_fold do |n, lo|
  n += 12 while n < lo
  n -= 12 while n > lo + 11
  n
end

# 休み(拍)
define :grid_rest do |beats|
  sleep beats
end

# パターンの音ごとにブロックを呼ぶ。ブロックの引数は |マスの位置, 長さ(マス数), 強さ, 文字|。パターンの長さぶん sleep する
define :grid_each do |pattern, &blk|
  cells = grid_cells(pattern)
  cells.each_with_index do |c, i|
    lvl = grid_level(c)
    blk.call(i, grid_len(cells, i), lvl, c) if lvl
    sleep grid_step
  end
end

# beats 拍を count 等分して、ブロックを |k| で count 回呼ぶ(k は 0 から)。beats 拍ぶん sleep する
define :grid_ticks do |beats, count, &blk|
  count.times do |k|
    blk.call(k)
    sleep beats.to_f / count
  end
end

# 連打。beats 拍に hits 回を等間隔で鳴らす(サンプル用)。amp0 から amp_step ずつ強く、rate0 から rate_step ずつ速く(省略可)
define :grid_roll do |voice, hits, beats, o = {}|
  grid_ticks(beats, hits) do |k|
    opts = voice[:opts].dup
    opts[:amp] = o[:amp0] + k * (o[:amp_step] || 0) if o[:amp0]
    opts[:rate] = o[:rate0] + k * (o[:rate_step] || 0) if o[:rate0]
    sample voice[:name], opts
  end
end

# voice を pattern どおりに鳴らす。オプション o:
#   on: 進行(grid_prog)。小節ごとに根音(既定)またはコード(chord: true)を鳴らす
#   fold: on: の根音を、この音(MIDI 番号)から12半音の範囲に収める(ベースの音域をそろえる。例 29 = F1〜E2)
#   steps: on: の根音に足す半音数の並び(音ごとに順に使う。例 [0, 0, 7, 12])
#   note: on: が無いときの音(シンセ用。例 :f2)
define :grid_play do |voice, pattern, o = {}|
  k = 0
  grid_each(pattern) do |i, len, lvl, c|
    opts = voice[:opts].merge(amp: (voice[:opts][:amp] || 1.0) * lvl)
    if voice[:kind] == :sample
      sample voice[:name], opts
    else
      if o[:on]
        root, type = o[:on][(i / grid_bar_cells) % o[:on].size]
        root = note(root)
        root = grid_fold(root, o[:fold]) if o[:fold]
        root += o[:steps][k % o[:steps].size] if o[:steps]
        n = o[:chord] ? chord(root, type) : root
      else
        n = o[:note]
      end
      gate = opts.delete(:gate) || 1.0
      cut = opts.delete(:cut) || 0
      opts[:sustain] = [len * grid_step * gate - cut, 0.05].max if len > 1 || gate != 1.0 || cut != 0 || !opts[:sustain]
      with_synth(voice[:name]) { play n, opts }
    end
    k += 1
  end
end

# 元の wav (grid_clip) を切り貼りして鳴らす(ボーカルチョップ)。元の wav は加工しない。
#   from: 各音が使う元の拍位置の並び(音の数と同じ個数)。省略すると、元の先頭から順に続けて進む。
#         :same なら、鳴らす位置と同じ元の位置を使う(base: で元の位置を拍ぶんずらせる。4小節の声を1小節ずつ使うときなど)
#   amp: / pan: / attack: / release: / env: は sample に渡す(attack 0.008 / release 0.06 が既定。切り口のプチ音を消す)
define :grid_chop do |clip, pattern, o = {}|
  pos = 0.0
  k = 0
  grid_each(pattern) do |i, len, lvl, c|
    l = len * grid_step
    from = o[:from] == :same ? (o[:base] || 0) + i * grid_step : (o[:from] ? o[:from][k] : pos)
    k += 1
    rest = o.reject { |key, _| key == :from || key == :base }
    rest = { attack: 0.008, release: 0.06 }.merge(rest) unless rest[:env]
    opts = grid_env(rest)
    opts = opts.merge(amp: (opts[:amp] || 1.0) * lvl, start: from / clip[:beats],
                      finish: [(from + l) / clip[:beats], 1.0].min)
    sample clip[:name], opts
    pos = from + l
  end
end


# ======== intro(32拍)========
define :grid_song_intro do
  # --- リズム(8小節 = 128マス)---
  # 数字は音の強さ(0.1〜0.9)。5 → 9 へ少しずつ強くして自然に入る。
  # 1小節目は前半2拍だけ鳴らす。2〜7小節目は最後の1拍(4マス)を休む。8小節目は最後の2拍を休み、ビルドへの息継ぎにする
  pad_r = "5--- ---- .... .... | 6--- ---- ---- .... | 6--- ---- ---- .... | 7--- ---- ---- .... | 7--- ---- ---- .... | 8--- ---- ---- .... | 8--- ---- ---- .... | 9--- ---- .... ...."
  # --- 進行(4小節を2回。音の高さは低い順)---
  pad_p = [
    [:f3, :ab3, :c4, :eb4],   # Fm7
    [:f3, :ab3, :c4, :eb4],   # Fm7
    [:f3, :ab3, :c4, :db4],   # Dbmaj7(Fm7 から Eb が Db に下がるだけ = 近接転回)
    [:f3, :ab3, :c4, :db4],   # Dbmaj7
  ]
  # --- 音: supersaw。ドロップの Pad(cutoff 78)より暗く(cutoff 60)---
  pad = grid_voice :synth, :supersaw, cutoff: 60, detune: 0.2, env: :pad, amp: 0.4
  in_thread do  # pad
    1.times do
        with_fx :reverb, room: 0.9, mix: 0.5, damp: 0.6 do
          grid_each(pad_r) do |i, len, lvl, c|
            with_synth(pad[:name]) do
              play pad_p[(i / grid_bar_cells) % pad_p.size],
                   pad[:opts].merge(amp: pad[:opts][:amp] * lvl, sustain: [len * grid_step - pad[:opts][:attack], 0.05].max)
            end
          end
        end
    end
  end
  sleep 32
end


# ======== build(32拍)========
define :grid_song_build do
  # --- リズム(8小節 = 128マス)---
  # Pad: 数字は音の強さ。6 → 9 へ少しずつ強くする。ドロップへ切れ目なくつなぐため、最後まで鳴らし続ける
  pad_r  = "6--- ---- ---- ---- | 6--- ---- ---- ---- | 7--- ---- ---- ---- | 7--- ---- ---- ---- | 8--- ---- ---- ---- | 8--- ---- ---- ---- | 9--- ---- ---- ---- | 9--- ---- ---- ----"
  # キック: 前半4小節は小節の頭だけ(心臓の鼓動)。後半4小節はドロップと同じ付点で跳ねるキック
  kick_p = "X... .... .... .... | X... .... .... .... | X... .... .... .... | X... .... .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... ...."
  # --- 進行(4小節を2回。音の高さは低い順)---
  pad_p = [
    [:f3, :ab3, :c4, :eb4],   # Fm7
    [:f3, :ab3, :bb3, :db4],  # Bbm7(Fm7 から C が Bb、Eb が Db に下がるだけ = 近接転回)
    [:f3, :ab3, :c4, :db4],   # Dbmaj7(Bbm7 から Bb が C に上がるだけ)
    [:g3, :bb3, :d4, :eb4],   # Ebmaj7(全体が全音〜半音上がる。次の Fm7 は ♭VII → i の解決)
  ]
  # --- 音 ---
  pad  = grid_voice :synth, :supersaw, cutoff: 60, detune: 0.2, env: :pad, amp: 0.45
  kick = grid_voice :sample, :bd_tek, amp: 1.3
  kick2 = grid_voice :sample, :drum_heavy_kick, amp: 0.9
  tom  = grid_voice :sample, :drum_tom_lo_hard, amp: 0.6, pan: 0.0, rate: 0.75, hpf: 40
  heavy = grid_voice :sample, :bd_boom, amp: 0.55
  # --- 曲全体のチョップ: ビルドの最後の1.5小節(26〜32拍)で、鳴っている音を with_fx :slicer(音をリズムに合わせて切る FX)で区切る ---
  # 26〜28拍: 16分(phase 0.25)/ 28〜32拍: 32分(phase 0.125)。32分を一番細かい区切りにして、ドロップの頭へ。
  # wave: 1 = 矩形波(音が出る/止まるを繰り返す)。smooth 0.005 は切り替えのなめらかさ(小さいほど細かい区切りが残る)。mix 0 の間は何もしない(素通り)。
  # Pad・キック・メロディ・bass・タムが、同じ時刻で同じように区切られる
  define :grid_gate do |&blk|
    with_fx :slicer, phase: 0.25, wave: 1, pulse_width: 0.5, smooth: 0.005, mix: 0 do |sl|
      in_thread do
        sleep 26
        control sl, mix: 1, phase: 0.25
        sleep 2
        control sl, phase: 0.125
      end
      blk.call
    end
  end
  in_thread do  # pad
    1.times do
        grid_gate do
          with_fx :reverb, room: 0.9, mix: 0.5, damp: 0.6 do
            grid_each(pad_r) do |i, len, lvl, c|
              bar = i / grid_bar_cells
              # 目覚め: 小節が進むごとに cutoff が 60 → 78(ドロップの Pad と同じ)へ開く
              opts = pad[:opts].merge(amp: pad[:opts][:amp] * lvl, cutoff: 60 + 18 * bar / 7.0,
                                      sustain: [len * grid_step - pad[:opts][:attack], 0.05].max)
              with_synth(pad[:name]) { play pad_p[bar % pad_p.size], opts }
            end
          end
        end
    end
  end
  in_thread do  # kick
    1.times do
        grid_gate do
          grid_play kick, kick_p
        end
    end
  end
  # 別のキック(heavy kick)を同じ位置に重ねて、インパクトを出す。bd_tek は硬い立ち上がり、drum_heavy_kick は太い胴鳴り
  in_thread do  # kick2
    1.times do
        grid_gate do
          grid_play kick2, kick_p
        end
    end
  end
  # --- メロディ(13-16小節の4小節だけ。ドロップのメロディを少し見せる)---
  # [拍の位置, 音名, 長さ(拍)] の並びを小節ごとに。各コードのコードトーンで、3つの音が「上がって、戻って、上がる」形を、コードの高さに合わせて移す
  # 13: Fm の C・Ab / 14: Bbm の Db・Bb / 15: Db の F・Db / 16: Eb の G・Bb・Eb。すべてそのコードのトライアド(根音・3度・5度)の音。鳴らすときは、各音をパワーコードにする
  mel_notes = [
    [[0, :c5, 1.5], [2, :ab4, 1], [3, :c5, 1]],
    [[0, :db5, 1.5], [2, :bb4, 1], [3, :db5, 1]],
    [[0, :f5, 1.5], [2, :db5, 1], [3, :f5, 1]],
    [[0, :g5, 1.5], [2, :bb4, 1], [3, :eb5, 1]],
  ]
  # リードシンセの立ち上がり(拍)。遅いほどパッドのようにふわっと入る。音の長さ = 立ち上がり + 保持なので、保持は(長さ - 立ち上がり)にする
  lead_attack = 0.5
  # 小節ごとの音量: 少しずつ強くして、だんだん姿を見せる
  mel_amp = [0.5, 0.6, 0.7, 0.8]
  # パワーコード = 根音 + 5度(3度を含まない2音)。メロディの音を一番上にして、その5度下を重ねる。
  # 5度下が F ナチュラルマイナーの外の音(Gb など)になるときだけ、4度下(パワーコードの転回形)にする
  mel_scale = [5, 7, 8, 10, 0, 1, 3]   # F G Ab Bb C Db Eb の音名の種類(C=0)
  define :grid_power do |top|
    low = mel_scale.include?((top - 7) % 12) ? top - 7 : top - 5
    [low, top]
  end
  # 音色: リードシンセ(dsaw = 少しずらした2本の鋸波)を、パッドのように伸ばす。立ち上がり 0.5 拍(lead_attack)・残りを保持・余韻 1 拍。
  # EQ はかけない。短いリバーブ(room 0.55・mix 0.35・damp 0.7)だけ。
  # 高い音(パワーコード)は右(pan 0.3)、1オクターブ下は単音(dsaw)で、bass(saw)と一緒に、0.1拍(約43ms)遅らせて重ねる(pan 0.15)
  in_thread do  # melody
    1.times do
        grid_gate do
          sleep 16
          mel_notes.each_with_index do |bar, b|
            t = 0
            bar.each_with_index do |(beat, n, len), idx|
              sleep beat - t
              hold = len
              rel = 1.0
              with_fx :reverb, room: 0.55, mix: 0.35, damp: 0.7 do
                with_synth(:dsaw) do
                  play grid_power(note(n)), amp: mel_amp[b] * 0.4, attack: lead_attack, sustain: [hold - lead_attack, 0.05].max, release: rel, cutoff: 100, detune: 0.15, pan: 0.3   # 高い音: メロディの音を一番上にしたパワーコード
                  time_warp 0.1 do
                    play note(n) - 12, amp: mel_amp[b] * 0.28, attack: lead_attack, sustain: [hold - lead_attack, 0.05].max, release: rel, cutoff: 100, detune: 0.15, pan: 0.15   # 1オクターブ下は単音
                  end
                end
              end
              # bass: 低音パート(1オクターブ下の単音)と同じ高さ・同じ長さで、同じ 0.1拍遅れで重ねる。ドロップの bass と同じ saw。リバーブの外でドライに鳴らす
              time_warp 0.1 do
                with_synth(:saw) { play note(n) - 12, amp: mel_amp[b] * 0.5, attack: 0.02, sustain: hold, release: 0.5, cutoff: 78, res: 0.25, pan: 0 }
              end
              t = beat
            end
            sleep 4 - t
          end
        end
    end
  end
  # ドロップ前の低いドラム(最後の2小節だけ): 低いタム(rate 0.75)が 4 分 → 8 分 → 16 分と詰まり、最後の2拍は16分で鳴り続けて、そのままドロップの頭につながる。数字は音の強さ
  pre_drop_r = "5..6 ..7. 7..8 ..8. | 8.8. 8.8. 9999 9999"
  in_thread do  # pre_drop
    1.times do
        grid_gate do
          sleep 24
          grid_play tom, pre_drop_r
        end
    end
  end
  # ドロップ直前(16小節目の最後の1拍 = 31〜32拍)の glitch アクセント: glitch_perc2 を 16分で3発、だんだん高く(rate 1.0 → 1.6)。スライサーの外に置く(区切られない)
  in_thread do  # glitch_pre
    1.times do
        sleep 31
        3.times do |k|
          sample :glitch_perc2, rate: 1.0 + 0.3 * k, amp: 0.8
          sleep 0.25
        end
        sleep 0.25   # 31 + 0.75 + 0.25 = 32拍
    end
  end
  sleep 32
end


# ======== dropA(64拍)========
define :grid_song_dropA do
  set :last_pass, false
  in_thread do
    sleep 48
    set :last_pass, true
  end
  # --- リズム(付点で跳ねる: 0 → 3マス目 → 6マス目)---
  kick_p = "X..x ..x. .... .... | X..x ..x. .... ..o. | X..x ..x. .... .... | X..x ..x. .... x.o."
  # --- 音 ---
  kick = grid_voice :sample, :bd_tek, amp: 1.3
  # --- サイドチェイン風(キックが鳴った直後に音量を下げ、元に戻す)---
  # 引き金のパターン(X・x の位置が「キックが鳴る」とみなす場所)。depth = 沈む深さ(0 = 無音、1 = 沈まない)、rel = 元に戻るまでのマス数
  # with_fx :level のかけ方: 音量(amp)を grid_duck がマスごとに control で動かす。パターンの長さぶん sleep するので、in_thread の中で呼ぶ
  define :grid_duck do |fx, pattern, depth, rel|
    cells = grid_cells(pattern)
    last = -100
    cells.each_with_index do |c, i|
      lvl = grid_level(c)
      last = i if lvl && lvl >= 0.7
      t = [(i - last).to_f / rel, 1.0].min
      control fx, amp: depth + (1 - depth) * t
      sleep grid_step
    end
  end
  in_thread do  # kick
    4.times do
        grid_play kick, kick_p
    end
  end
  # Dark Future Bass / Pad 案 b / current.rb(キック c)に重ねる / BPM140・F ナチュラルマイナー
  # 進行(4小節): 借用 IV(Fm7 → Dbmaj7 → Abmaj7 → Bb)。4小節目の Bb は F メジャーから借りたメジャーコード(♮6 の D が入る)
  # 声部: 下の pad_p は、各コードの構成音を隣のコードと近い音に並べた形(近接転回)。4小節目の D(♮6)が一瞬だけ明るく差し、1小節目の Fm7 に戻ると暗く閉じる
  # --- リズム(4小節 = 64マス。毎小節の頭で鳴らして、1小節伸ばす)---
  pad_r = "X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ----"
  # --- 進行(1小節に1コード。音の高さは低い順)---
  pad_p = [
    [:f3, :ab3, :c4, :eb4],  # Fm7
    [:f3, :ab3, :c4, :db4],  # Dbmaj7
    [:g3, :ab3, :c4, :eb4],  # Abmaj7
    [:f3, :bb3, :d4, :f4],  # Bb(借用 IV)
  ]
  # --- 音: 鋸波を重ねた supersaw。ゆっくり立ち上がり、長く残る(env: :pad)---
  pad = grid_voice :synth, :supersaw, cutoff: 78, detune: 0.2, env: :pad, amp: 0.4
  # grid_each で、小節ごとに pad_p から1コードを取って鳴らす。長さぶん sleep されるので sleep は書かない
  in_thread do  # pad
    4.times do
        with_fx :level, amp: 1, amp_slide: 0.04 do |duck_fx|
          in_thread { grid_duck duck_fx, kick_p, 0.35, 4 }
          with_fx :reverb, room: 0.9, mix: 0.5, damp: 0.6 do
            grid_each(pad_r) do |i, len, lvl, c|
              with_synth(pad[:name]) do
                play pad_p[(i / grid_bar_cells) % pad_p.size],
                     pad[:opts].merge(amp: pad[:opts][:amp] * lvl, sustain: [len * grid_step - pad[:opts][:attack], 0.05].max)
              end
            end
          end
        end
    end
  end
  # Dark Future Bass / スネア案 b / current.rb(キック c + Pad b)に重ねる / BPM140
  # スネア = ハーフタイムの3拍目(各小節の 8 マス目)。キックは 0・3・6 マス目なので重ならない
  # --- ロングテイル: 3拍目だけ。リバーブを深く(room 1、mix 0.55、damp 0.7)で暗い余韻に ---
  snare_p = ".... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... ...."
  snare = grid_voice :sample, :sn_dolf, amp: 0.85, hpf: 110
  in_thread do  # snare
    4.times do
        with_fx :reverb, room: 1, mix: 0.55, damp: 0.7 do
          grid_play snare, snare_p
        end
    end
  end
  # Dark Future Bass / bass 案 b / current.rb(キック c + Pad b + スネア b)に重ねる / BPM140・F ナチュラルマイナー
  # 根音は Pad の進行(Fm7 → Dbmaj7 → Abmaj7 → Bb)に合わせる。音域は F2〜(87Hz〜)。sub bass(F1 付近)は次のステムで別に足す
  # --- 進行(Pad と同じ。1小節に1つ。根音を鳴らす)---
  bass_p = grid_prog [:f2, :minor7], [:db2, :major7], [:ab2, :major7], [:bb2, :major]
  # --- キックに揃える: キックと同じ位置(0・3・6 マス目)で短く切る ---
  bass_r = "X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... ...."
  bass = grid_voice :synth, :saw, cutoff: 78, res: 0.25, env: :stab, amp: 0.6
  in_thread do  # bass
    4.times do
        grid_play bass, bass_r, on: bass_p, fold: 36
    end
  end
  # Dark Future Bass / sub bass 案 a / current.rb(キック c + Pad b + スネア b + bass b)に重ねる / BPM140
  # 根音は bass_p(current.rb にある進行)を使う。sub bass は bass の1オクターブ下(F1 = 43.7Hz 付近)。fold: 25 で Db1〜C2 に収める
  # --- 根音ロング: 毎小節の頭から1小節伸ばす ---
  sub_r = "X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ----"
  sub = grid_voice :synth, :sine, attack: 0.02, release: 0.3, amp: 0.7
  in_thread do  # sub
    4.times do
        with_fx :level, amp: 1, amp_slide: 0.04 do |duck_fx|
          in_thread { grid_duck duck_fx, kick_p, 0.35, 4 }
          grid_play sub, sub_r, on: bass_p, fold: 25
        end
    end
  end
  # --- 16分の抑揚: x・o・X を並べて、ノリを作る。2・4小節目の最後に少し詰める ---
  hat_p = "x.ox .oxo x.ox .oxo | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox oxox"
  hat = grid_voice :sample, :hat_snap, amp: 0.45, hpf: 100, pan: 0.2
  in_thread do  # hat
    4.times do
        grid_play hat, hat_p
    end
  end
  # --- キックと揃えたスタブ: キックの位置(0・3・6 マス目)で和音を短く ---
  keys_r = "X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... ...."
  keys = grid_voice :synth, :piano, vel: 0.25, hard: 0.8, release: 0.3, amp: 0.5, pan: -0.2
  in_thread do  # keys
    4.times do
        grid_play keys, keys_r, on: bass_p, fold: 48, chord: true
    end
  end
  # Solo Violin(メロディ)+ Cello(メロディの 3度下を 1オクターブ低くハモる)。
  # 前半(0〜7マス目)= ベース・キックが強く打つので長い音、後半(8〜15マス目)= ベースが落ち着くので細かく。supersaw の和音は前半だけ(13 と同じ)。
  # --- 和音(前半だけ。13_sup_callresp と同じ)---
  sup_chord_r = "X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... ...."
  sup_chord = grid_voice :synth, :supersaw, cutoff: 100, detune: 0.3, attack: 0.02, release: 0.4, amp: 1.0, pan: 0.0
  # --- 弦楽器のメロディ ---
  # 1小節に 7音: 前半の長い音(1つ)+ 後半の細かいフレーズ(6つ)。長い音は和音の5度・7度・3度で、前の小節の終わりからグライドでつながる
  str_hold = [:f5, :c5, :eb5, :d5]          # Fm7 の根音 / Dbmaj7 の 7度(C)/ Abmaj7 の 5度(Eb)/ Bb の 3度(D)
  str_phrase = [
    [:c5, :eb5, :f5, :eb5, :c5, :ab4],      # Fm7: 上がって戻る(問い)
    [:db5, :f5, :ab5, :f5, :c5, :db5],      # Dbmaj7: より高く
    [:eb5, :g5, :ab5, :g5, :eb5, :c5],      # Abmaj7: 一番高く、最後は下がる
    [:f5, :d5, :bb4, :c5, :d5, :f5],        # Bb(借用 IV): 答え。最後は F で、次の Fm7 の根音 F5 につながる
  ]
  str_n = str_phrase.each_with_index.map { |ph, b| [str_hold[b]] + ph }
  # リズム: 0マス目から 8マス(2拍)の長い音 → 後半は x.xo x.xo の6音
  str_r = "x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo"
  # --- Solo Violin(メロディ)と Cello(ハモリ)---
  # Solo Violin: blade(ビブラート付き)。長い音はビブラートが遅れて入り(vibrato_delay)、音量が膨らむ(swell)。右寄り。
  # 楽器: チップチューン系(8ビットゲーム機のような矩形波)。glitch の質感(デジタル・硬い倍音)に近づける。メロディ = chiplead。ハモリ(chipbass)はなくし、アルペジオを散りばめる
  # (前の版は blade〔ヴァイオリン〕と blade〔チェロ〕、その次は chiplead + chipbass のハモリ。メロディ・進行・強弱・9度は変えていない)
  lead_hi = grid_voice :synth, :chiplead, release: 0.3, amp: 0.4, pan: 0.2
  # 強弱(dynamics)。小節ごとの全体の大きさ(だんだん強く、4小節目は着地へ少し弱める)と、フレーズ内の音ごとの大きさ(山の頂点で最大、終わりで着地)。
  # 並びは [長い音, 細かい6音]。数字は 0〜1 の大きさ
  # 各小節のコードの 9度の音名(C=0): Fm7 = G(7)/ Dbmaj7 = Eb(3)/ Abmaj7 = Bb(10)/ Bb(借用 IV)= C(0)
  ninth_pc = [7, 3, 10, 0]
  dyn_bar = [0.9, 0.95, 1.0, 0.95]   # ドロップに入ってからも小さくならないよう、最初の小節も 0.9 から
  dyn_note = [
    [0.9, 0.7, 0.8, 1.0, 0.8, 0.7, 0.6],     # Fm7: 山は 3音目(F5)
    [0.8, 0.8, 0.9, 1.0, 0.85, 0.7, 0.65],   # Dbmaj7: 山は 4音目(Ab5、一番高い音)
    [0.9, 0.8, 0.95, 1.0, 0.9, 0.75, 0.6],   # Abmaj7: 山は 4音目(Ab5)
    [0.8, 0.9, 0.75, 0.6, 0.7, 0.85, 1.0],   # Bb(借用 IV): 最後の F5 へ向けて強くなり、着地を強調
  ]
  in_thread do  # sup_chord
    4.times do
        with_fx :level, amp: 1, amp_slide: 0.04 do |duck_fx|
          in_thread { grid_duck duck_fx, kick_p, 0.3, 6 }
          with_fx :reverb, room: 0.7, mix: 0.3, damp: 0.6 do
            grid_each(sup_chord_r) do |i, len, lvl, c|
              opts = sup_chord[:opts].merge(amp: sup_chord[:opts][:amp] * lvl, sustain: [len * grid_step - sup_chord[:opts][:attack], 0.05].max)
              with_synth(sup_chord[:name]) { play pad_p[(i / grid_bar_cells) % pad_p.size].map { |n| note(n) + 12 }, opts }
            end
          end
        end
    end
  end
  # Solo Violin: str_n の音をそのままの高さで弾く(音程は滑らせない)。長い音は 1拍かけて音量が膨らみ、細かい音は dyn_note × 小節の強弱 × 強さ(x・o)で鳴らす。
  # 深いリバーブ(room 0.9、mix 0.45)で響かせる
  in_thread do  # lead_hi
    4.times do
        with_fx :reverb, room: 0.9, mix: 0.45, damp: 0.5 do
          with_fx :eq, high_shelf: -0.6, high_shelf_note: 88, high_shelf_slope: 0.5 do   # chiptune の高音を削る(約 1.3kHz より上を下げる)
          k = 0
          held_last = false   # 最後の音を伸ばし切ったか(伸ばしたら、リバーブの尾が切れないよう、ループの終わりで待つ)
          grid_each(str_r) do |i, len, lvl, c|
            bar = (i / grid_bar_cells) % str_n.size
            k = 0 if i % grid_bar_cells == 0
            n = note(str_n[bar][k])
            loud = lead_hi[:opts][:amp] * lvl * dyn_bar[bar] * dyn_note[bar][k]
            if len > 2
              # 長い音: 小さく始めて、1拍かけて loud まで膨らむ(swell)
              s = synth lead_hi[:name], lead_hi[:opts].merge(note: n, amp: loud * 0.35, amp_slide: 1.0, attack: 0.2, sustain: len * grid_step - 0.2)
              control s, amp: loud
              # 9度のテンション: 長い音の上に、そのコードの 9度を最高音として重ねる(短3度以上離れた一番近い音)。音量は 0.7 倍
              nine = n + 3
              nine += 1 until nine % 12 == ninth_pc[bar]
              s9 = synth lead_hi[:name], lead_hi[:opts].merge(note: nine, amp: loud * 0.7 * 0.35, amp_slide: 1.0, attack: 0.2, sustain: len * grid_step - 0.2)
              control s9, amp: loud * 0.7
            else
              # ドロップの最後のメロディ(最後の小節の最後の音)は、短く切らずに伸ばし切る(3拍保持 + 2拍の余韻)。ドロップAは 4小節ループなので、最後の回(get[:last_pass])だけ
              if bar == str_n.size - 1 && k == str_n[bar].size - 1 && (str_n.size > 4 || get[:last_pass] == true)
                held_last = true
                synth lead_hi[:name], lead_hi[:opts].merge(note: n, amp: loud, attack: 0.03, sustain: 3.0, release: 2.0)
              else
                with_synth(lead_hi[:name]) { play n, lead_hi[:opts].merge(amp: loud, attack: 0.03, sustain: [len * grid_step - 0.03, 0.05].max) }
              end
            end
            k += 1
          end
          sleep 4 if held_last   # 伸ばした音の響きを待つ
          end
        end
    end
  end
  # --- チップ系のアルペジオ(ハモリの代わり): 和音の構成音を、メロディの隙間に散りばめる ---
  # 1小節(16マス)に 6発だけ(1・3・4・6・9・13 マス目)。メロディの音(0・8・10・11・12・14・15 マス目)と重ならない位置。o = 弱、x = ふつう
  arp_bar = ".o.o x.x. .o.. .o.."
  # 和音の構成音の何番目(0〜3)を鳴らすか。下から上、また下へ: 0 → 1 → 2 → 3 → 2 → 1(1小節に 6発)
  arp_order = [0, 1, 2, 3, 2, 1]
  # パン(左右)。1発ごとに交互に振り分けて、散りばめる
  arp_pan = [-0.5, 0.5, -0.3, 0.3, -0.6, 0.6]
  arp = grid_voice :synth, :chiplead, release: 0.2, amp: 0.25
  arp_r = ([arp_bar] * 4).join(" | ")
  in_thread do  # lead_arp
    4.times do
        with_fx :reverb, room: 0.6, mix: 0.3, damp: 0.6 do
          with_fx :eq, high_shelf: -0.6, high_shelf_note: 88, high_shelf_slope: 0.5 do   # chiptune の高音を削る(約 1.3kHz より上を下げる)
          k = 0
          grid_each(arp_r) do |i, len, lvl, c|
            bar = (i / grid_bar_cells) % pad_p.size
            k = 0 if i % grid_bar_cells == 0
            note_n = note(pad_p[bar][arp_order[k % arp_order.size]]) + 12   # 和音の構成音を 1オクターブ上げる(F4〜E♭5 付近)
            with_synth(arp[:name]) { play note_n, arp[:opts].merge(amp: arp[:opts][:amp] * lvl, pan: arp_pan[k % arp_pan.size], attack: 0.01, sustain: [len * grid_step * 0.5, 0.05].max) }
            k += 1
          end
          end
        end
    end
  end
  # --- ボコーダーの声の16分チョップ(アルペジオに重ねる)---
  # 声は NEUTRINO で歌わせ(work/vocals/01_arp_*.json)、調声して、ボコーダーにかけたもの(vocode.py。DSP のみ)。アルペジオと同じ音を、同じタイミングで歌っている。
  # 元の wav は 4小節 = 16拍(BPM130 で 7.385秒)。アルペジオの6つの位置で、各音の頭から 16分(0.25拍)ずつ切って鳴らす
  vox_a = grid_clip "/Users/nagutabby/sonicpi-live-agent/work/vocals/01_arp_a_tuned_voc_v2.wav", 16   # Fm7 → Dbmaj7 → Abmaj7 → Bb(ドロップAの進行)
  vox_b = grid_clip "/Users/nagutabby/sonicpi-live-agent/work/vocals/01_arp_b_tuned_voc_v2.wav", 16   # Fm7 → Bbm7 → Dbmaj7 → Ebmaj7(ドロップB 後半の進行)
  vox_pos = [0.25, 0.75, 1.0, 1.5, 2.25, 3.25]                                    # 1小節の中の、アルペジオの6つの位置(拍)。声の各音の頭と同じ
  vox_from4 = (0..3).flat_map { |b| vox_pos.map { |p| b * 4 + p } }                # 4小節ぶん(24個)
  in_thread do  # lead_vox
    4.times do
        with_fx :reverb, room: 0.85, mix: 0.5, damp: 0.5 do
          grid_chop vox_a, arp_r, from: vox_from4, amp: 0.7, pan: 0.0, attack: 0.03   # attack は標準 0.008拍 → 0.03拍(約14ms)。頭が少し丸くなる
        end
    end
  end
  # --- グリッチのスタッター: 最後の1拍に、短い音を 16分で繰り返し、高さを上げる(glitch)---
  in_thread do  # fill
    4.times do
        sleep 15
        8.times do |k|
          sample :hat_snap, rate: 1.0 + 0.1 * k, amp: 0.5 + 0.05 * k, finish: 0.15
          sleep 0.125
        end
    end
  end
  sleep 64
end


# ======== buildup(48拍)========
define :grid_song_buildup do
  # ---- 12小節 = 192マス。rest(休みの1小節)を先頭に並べて、stem が入る小節を遅らせる ----
  bar_rest = ".... .... .... ...."
  define :grid_bars do |*bars|
    bars.join(" | ")
  end
  # --- 進行(Pad・弦)と、ピアノ・bass の進行 ---
  bu_p = [
    [:f3, :ab3, :c4, :db4],   # Dbmaj7
    [:g3, :ab3, :c4, :eb4],   # Abmaj7(Dbmaj7 から F が G、Db が Eb に上がるだけ = 近接転回)
    [:g3, :bb3, :d4, :eb4],   # Ebmaj7(Ab が Bb、C が D に上がるだけ)
    [:f3, :ab3, :c4, :eb4],   # Fm7(G が F、Bb が Ab、D が C に下がり、主和音へ)
  ]
  bu_keys_prog = grid_prog [:db3, :major7], [:ab3, :major7], [:eb3, :major7], [:f3, :minor7]
  bu_bass_prog = grid_prog [:db2, :major7], [:ab2, :major7], [:eb2, :major7], [:f2, :minor7]
  # ---- 1-2小節目から: Pad(だんだん強く・cutoff が開く)。ライザーは 7小節目から ----
  # 数字は音の強さ。2小節ごとに 5 → 9 へ上げる
  bu_pad_r = grid_bars("5--- ---- ---- ----", "5--- ---- ---- ----", "6--- ---- ---- ----", "6--- ---- ---- ----", "7--- ---- ---- ----", "7--- ---- ---- ----",
                       "8--- ---- ---- ----", "8--- ---- ---- ----", "9--- ---- ---- ----", "9--- ---- ---- ----", "9--- ---- ---- ----", "9--- ---- ---- ----")
  bu_pad = grid_voice :synth, :supersaw, cutoff: 60, detune: 0.2, env: :pad, amp: 0.4
  # ---- 3-4小節目から: 低音ピアノ(小節の頭と3拍目)----
  bu_keys_r = grid_bars(*([bar_rest] * 2 + ["X--- ---- o--- ----"] * 10))
  bu_keys = grid_voice :synth, :piano, vel: 0.2, hard: 0.5, release: 0.5, amp: 0.5, pan: -0.2
  # ---- 5-6小節目から: Solo Violin + Cello(ブレイクと同じメロディ。2回目と3回目の繰り返しだけ鳴らし、音量は1小節ごとに少しずつ上げる)----
  bu_mel = [
    [[0, :c5, 3],  [3, :db5, 1]],     # Dbmaj7
    [[0, :eb5, 3], [3, :c5, 1]],      # Abmaj7
    [[0, :g5, 3],  [3, :d5, 1]],      # Ebmaj7
    [[0, :c5, 2],  [2, :ab4, 2]],     # Fm7
  ]
  # 5〜12小節目(8小節)で 0.2 → 1.0 へ、1小節ごとに少しずつ大きくする(最初は小さく、駆け上がるにつれて大きく)
  bu_ramp_from = 0.2
  bu_bar = [0.8, 0.9, 1.0, 0.85]
  # 楽器: チップチューン系(8ビットゲーム機のような矩形波)。glitch の質感(デジタル・硬い倍音)に近づける。メロディ = chiplead。ハモリ(chipbass)はなくし、アルペジオを散りばめる
  # (前の版は blade〔ヴァイオリン〕と blade〔チェロ〕、その次は chiplead + chipbass のハモリ。メロディ・進行・強弱・9度は変えていない)
  lead_hi = grid_voice :synth, :chiplead, release: 0.3, amp: 0.3, pan: 0.2
  define :grid_bow do |voice, pitch, loud, len|
    s = synth voice[:name], voice[:opts].merge(note: pitch, amp: loud * 0.35, amp_slide: len * 0.5, attack: 0.2, sustain: len - 0.2)
    control s, amp: loud
  end
  # ---- 7-8小節目から: キック(心臓の鼓動 → 2拍目の裏 → ドロップと同じ付点)----
  bu_kick_r = grid_bars(*([bar_rest] * 6 + ["X... .... .... ...."] * 2 + ["X... .... ..x. ...."] * 2 + ["X..x ..x. .... ...."] * 2))
  bu_kick = grid_voice :sample, :bd_tek, amp: 1.3
  # ---- 9-10小節目から: ハイハット(8分 → 16分)+ bass + sub ----
  bu_hat_r = grid_bars(*([bar_rest] * 8 + ["x.o. x.o. x.o. x.o."] * 2 + ["x.ox .oxo x.ox .oxo"] * 2))
  bu_hat = grid_voice :sample, :hat_snap, amp: 0.45, hpf: 100, pan: 0.2
  bu_bass_r = grid_bars(*([bar_rest] * 8 + ["X..x ..x. .... ...."] * 4))
  bu_bass = grid_voice :synth, :saw, cutoff: 78, res: 0.25, env: :stab, amp: 0.6
  bu_sub_r = grid_bars(*([bar_rest] * 8 + ["X--- ---- ---- ----"] * 4))
  bu_sub = grid_voice :synth, :sine, attack: 0.02, release: 0.3, amp: 0.7
  # ---- 11-12小節目から: スネア(3拍目)+ 低いタム(4分 → 8分 → 16分と詰まる)----
  bu_snare_r = grid_bars(*([bar_rest] * 10 + [".... .... X... ...."] * 2))
  bu_snare = grid_voice :sample, :sn_dolf, amp: 0.85, hpf: 110
  bu_tom_r = grid_bars(*([bar_rest] * 10 + ["5..6 ..7. 7..8 ..8.", "8.8. 8.8. 9999 9999"]))
  bu_tom = grid_voice :sample, :drum_tom_lo_hard, amp: 0.6, pan: 0.0, rate: 0.75, hpf: 40
  # ---- 全体のチョップ: 最後の6拍(42〜48拍)で、鳴っている全部の音をスライサーで区切る(42〜44拍 16分 → 44〜48拍 32分)----
  define :grid_gate_at do |start, &blk|
    with_fx :slicer, phase: 0.25, wave: 1, pulse_width: 0.5, smooth: 0.005, mix: 0 do |sl|
      in_thread do
        sleep start
        control sl, mix: 1, phase: 0.25
        sleep 2
        control sl, phase: 0.125
      end
      blk.call
    end
  end
  in_thread do  # bu_pad
    1.times do
        grid_gate_at 42 do
          with_fx :reverb, room: 0.9, mix: 0.5, damp: 0.6 do
            grid_each(bu_pad_r) do |i, len, lvl, c|
              bar = i / grid_bar_cells
              # cutoff が 60 → 100 へ開く(駆け上がる)
              opts = bu_pad[:opts].merge(amp: bu_pad[:opts][:amp] * lvl, cutoff: 60 + 40 * bar / 11.0, sustain: [len * grid_step - bu_pad[:opts][:attack], 0.05].max)
              with_synth(bu_pad[:name]) { play bu_p[bar % bu_p.size], opts }
            end
          end
        end
    end
  end
  in_thread do  # bu_keys
    1.times do
        grid_gate_at 42 do
          grid_play bu_keys, bu_keys_r, on: bu_keys_prog, fold: 48, chord: true
        end
    end
  end
  in_thread do  # bu_strings
    1.times do
        grid_gate_at 42 do
          with_fx :reverb, room: 0.9, mix: 0.45, damp: 0.5 do
            with_fx :eq, high_shelf: -0.6, high_shelf_note: 88, high_shelf_slope: 0.5 do   # chiptune の高音を削る(約 1.3kHz より上を下げる)
            sleep 16   # 1-4小節目は鳴らさない
            2.times do |rep|
              bu_mel.each_with_index do |notes, b|
                t = 0
                notes.each do |(beat, n, len)|
                  sleep beat - t
                  idx = rep * 4 + b                                   # 0〜7(5〜12小節目)
                  loud = (bu_ramp_from + (1.0 - bu_ramp_from) * idx / 7.0) * bu_bar[b]
                  grid_bow lead_hi, note(n), lead_hi[:opts][:amp] * loud, len
                  t = beat
                end
                sleep 4 - t
              end
            end
            end
          end
        end
    end
  end
  # --- チップ系のアルペジオ(ハモリの代わり): 和音の構成音を、メロディの隙間に散りばめる ---
  # 1小節(16マス)に 6発だけ(1・3・4・6・9・13 マス目)。メロディの音(0・8・10・11・12・14・15 マス目)と重ならない位置。o = 弱、x = ふつう
  arp_bar = ".o.o x.x. .o.. .o.."
  # 和音の構成音の何番目(0〜3)を鳴らすか。下から上、また下へ: 0 → 1 → 2 → 3 → 2 → 1(1小節に 6発)
  arp_order = [0, 1, 2, 3, 2, 1]
  # パン(左右)。1発ごとに交互に振り分けて、散りばめる
  arp_pan = [-0.5, 0.5, -0.3, 0.3, -0.6, 0.6]
  arp = grid_voice :synth, :chiplead, release: 0.2, amp: 0.2
  # 5〜12小節目(8小節)で、弦(メロディ)と同じように、0.2 → 1.0 へ1小節ごとに大きくする
  in_thread do  # bu_arp
    1.times do
        grid_gate_at 42 do
          with_fx :reverb, room: 0.6, mix: 0.3, damp: 0.6 do
            with_fx :eq, high_shelf: -0.6, high_shelf_note: 88, high_shelf_slope: 0.5 do   # chiptune の高音を削る(約 1.3kHz より上を下げる)
            sleep 16   # 1-4小節目は鳴らさない
            k = 0
            grid_each(grid_bars(*([arp_bar] * 8))) do |i, len, lvl, c|
              bar_local = i / grid_bar_cells                       # 0〜7(5〜12小節目)
              k = 0 if i % grid_bar_cells == 0
              ramp = bu_ramp_from + (1.0 - bu_ramp_from) * bar_local / 7.0
              note_n = note(bu_p[(4 + bar_local) % bu_p.size][arp_order[k % arp_order.size]]) + 12
              with_synth(arp[:name]) { play note_n, arp[:opts].merge(amp: arp[:opts][:amp] * lvl * ramp, pan: arp_pan[k % arp_pan.size], attack: 0.01, sustain: [len * grid_step * 0.5, 0.05].max) }
              k += 1
            end
            end
          end
        end
    end
  end
  in_thread do  # bu_kick
    1.times do
        grid_gate_at 42 do
          grid_play bu_kick, bu_kick_r
        end
    end
  end
  in_thread do  # bu_hat
    1.times do
        grid_gate_at 42 do
          grid_play bu_hat, bu_hat_r
        end
    end
  end
  in_thread do  # bu_bass
    1.times do
        grid_gate_at 42 do
          grid_play bu_bass, bu_bass_r, on: bu_bass_prog, fold: 36
        end
    end
  end
  in_thread do  # bu_sub
    1.times do
        grid_gate_at 42 do
          grid_play bu_sub, bu_sub_r, on: bu_bass_prog, fold: 25
        end
    end
  end
  in_thread do  # bu_snare
    1.times do
        grid_gate_at 42 do
          with_fx :reverb, room: 1, mix: 0.55, damp: 0.7 do
            grid_play bu_snare, bu_snare_r
          end
        end
    end
  end
  in_thread do  # bu_toms
    1.times do
        grid_gate_at 42 do
          grid_play bu_tom, bu_tom_r
        end
    end
  end
  # ---- ライザー: 7小節目(24拍目)から 22拍かけて、ノイズのローパスが開き、音量が上がる。もう1本、F3 から F5 へ音程が上がる dsaw を重ねる(駆け上がる)。チョップの外 ----
  # 長すぎたので、始まりを遅らせた(3小節目の 8拍目 → 7小節目の 24拍目)。音量は前のまま(ノイズの最大 0.35、dsaw の最大 0.18)
  in_thread do  # bu_riser
    1.times do
        sleep 24
        with_fx :reverb, room: 0.8, mix: 0.3 do
          with_fx :rlpf, cutoff: 60, cutoff_slide: 22, res: 0.4 do |lp|
            nz = synth :noise, amp: 0.02, amp_slide: 22, sustain: 22.5, release: 0.3, attack: 0
            tn = synth :dsaw, note: :f3, note_slide: 22, amp: 0.02, amp_slide: 22, sustain: 22.5, release: 0.3, attack: 0, cutoff: 100, detune: 0.2
            control lp, cutoff: 125
            control nz, amp: 0.35
            control tn, note: :f5, amp: 0.18
            sleep 24
          end
        end
    end
  end
  # ---- ドロップB直前(47拍目 = 最後の1拍)の glitch アクセント: glitch_perc2 を16分で3発、だんだん高く。チョップの外 ----
  in_thread do  # bu_glitch
    1.times do
        sleep 47
        3.times do |k|
          sample :glitch_perc2, rate: 1.0 + 0.3 * k, amp: 0.8
          sleep 0.25
        end
        sleep 0.25
    end
  end
  sleep 48
end


# ======== dropB(64拍)========
define :grid_song_dropB do
  # --- リズム(付点で跳ねる: 0 → 3マス目 → 6マス目)---
  kick_p = "X..x ..x. .... .... | X..x ..x. .... ..o. | X..x ..x. .... .... | X..x ..x. .... x.o. | X..x ..x. .... .... | X..x ..x. .... ..o. | X..x ..x. .... .... | X..x ..x. .... x.o. | X..x ..x. .... .... | X..x ..x. .... ..o. | X..x ..x. .... .... | X..x ..x. .... x.o. | X..x ..x. .... .... | X..x ..x. .... ..o. | X..x ..x. .... .... | X..x ..x. .... x.o."
  # --- 音 ---
  kick = grid_voice :sample, :bd_tek, amp: 1.3
  # --- サイドチェイン風(キックが鳴った直後に音量を下げ、元に戻す)---
  # 引き金のパターン(X・x の位置が「キックが鳴る」とみなす場所)。depth = 沈む深さ(0 = 無音、1 = 沈まない)、rel = 元に戻るまでのマス数
  # with_fx :level のかけ方: 音量(amp)を grid_duck がマスごとに control で動かす。パターンの長さぶん sleep するので、in_thread の中で呼ぶ
  define :grid_duck do |fx, pattern, depth, rel|
    cells = grid_cells(pattern)
    last = -100
    cells.each_with_index do |c, i|
      lvl = grid_level(c)
      last = i if lvl && lvl >= 0.7
      t = [(i - last).to_f / rel, 1.0].min
      control fx, amp: depth + (1 - depth) * t
      sleep grid_step
    end
  end
  in_thread do  # kick
    1.times do
        grid_play kick, kick_p
    end
  end
  # Dark Future Bass / Pad 案 b / current.rb(キック c)に重ねる / BPM140・F ナチュラルマイナー
  # 進行(4小節): 借用 IV(Fm7 → Dbmaj7 → Abmaj7 → Bb)。4小節目の Bb は F メジャーから借りたメジャーコード(♮6 の D が入る)
  # 声部: 下の pad_p は、各コードの構成音を隣のコードと近い音に並べた形(近接転回)。4小節目の D(♮6)が一瞬だけ明るく差し、1小節目の Fm7 に戻ると暗く閉じる
  # --- リズム(4小節 = 64マス。毎小節の頭で鳴らして、1小節伸ばす)---
  pad_r = "X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ----"
  # --- 進行(1小節に1コード。音の高さは低い順)---
  # 前半8小節: ドロップAと同じ(Fm7 → Dbmaj7 → Abmaj7 → Bb)×2。後半8小節: Fm7 → Bbm7 → Dbmaj7 → Ebmaj7 ×2(近接転回:隣のコードと近い音を並べる)
  pad_p_a = [
    [:f3, :ab3, :c4, :eb4],   # Fm7
    [:f3, :ab3, :c4, :db4],   # Dbmaj7
    [:g3, :ab3, :c4, :eb4],   # Abmaj7
    [:f3, :bb3, :d4, :f4],    # Bb(借用 IV)
  ]
  pad_p_b = [
    [:f3, :ab3, :c4, :eb4],   # Fm7
    [:f3, :ab3, :bb3, :db4],  # Bbm7(Fm7 から C が Bb、Eb が Db に下がるだけ)
    [:f3, :ab3, :c4, :db4],   # Dbmaj7(Bbm7 から Bb が C に上がるだけ)
    [:g3, :bb3, :d4, :eb4],   # Ebmaj7
  ]
  pad_p = pad_p_a + pad_p_a + pad_p_b + pad_p_b
  # --- 音: 鋸波を重ねた supersaw。ゆっくり立ち上がり、長く残る(env: :pad)---
  pad = grid_voice :synth, :supersaw, cutoff: 78, detune: 0.2, env: :pad, amp: 0.4
  # grid_each で、小節ごとに pad_p から1コードを取って鳴らす。長さぶん sleep されるので sleep は書かない
  in_thread do  # pad
    1.times do
        with_fx :level, amp: 1, amp_slide: 0.04 do |duck_fx|
          in_thread { grid_duck duck_fx, kick_p, 0.35, 4 }
          with_fx :reverb, room: 0.9, mix: 0.5, damp: 0.6 do
            grid_each(pad_r) do |i, len, lvl, c|
              with_synth(pad[:name]) do
                play pad_p[(i / grid_bar_cells) % pad_p.size],
                     pad[:opts].merge(amp: pad[:opts][:amp] * lvl, sustain: [len * grid_step - pad[:opts][:attack], 0.05].max)
              end
            end
          end
        end
    end
  end
  # Dark Future Bass / スネア案 b / current.rb(キック c + Pad b)に重ねる / BPM140
  # スネア = ハーフタイムの3拍目(各小節の 8 マス目)。キックは 0・3・6 マス目なので重ならない
  # --- ロングテイル: 3拍目だけ。リバーブを深く(room 1、mix 0.55、damp 0.7)で暗い余韻に ---
  snare_p = ".... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... .... | .... .... X... ...."
  snare = grid_voice :sample, :sn_dolf, amp: 0.85, hpf: 110
  in_thread do  # snare
    1.times do
        with_fx :reverb, room: 1, mix: 0.55, damp: 0.7 do
          grid_play snare, snare_p
        end
    end
  end
  # Dark Future Bass / bass 案 b / current.rb(キック c + Pad b + スネア b)に重ねる / BPM140・F ナチュラルマイナー
  # 根音は Pad の進行(Fm7 → Dbmaj7 → Abmaj7 → Bb)に合わせる。音域は F2〜(87Hz〜)。sub bass(F1 付近)は次のステムで別に足す
  # --- 進行(Pad と同じ。1小節に1つ。根音を鳴らす)---
  bass_p_a = [[:f2, :minor7], [:db2, :major7], [:ab2, :major7], [:bb2, :major]]
  bass_p_b = [[:f2, :minor7], [:bb2, :minor7], [:db2, :major7], [:eb2, :major7]]
  bass_p = bass_p_a + bass_p_a + bass_p_b + bass_p_b   # 16小節ぶん(grid_prog は配列を返すだけなので、そのまま足してよい)
  # --- キックに揃える: キックと同じ位置(0・3・6 マス目)で短く切る ---
  bass_r = "X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... ...."
  bass = grid_voice :synth, :saw, cutoff: 78, res: 0.25, env: :stab, amp: 0.6
  in_thread do  # bass
    1.times do
        grid_play bass, bass_r, on: bass_p, fold: 36
    end
  end
  # Dark Future Bass / sub bass 案 a / current.rb(キック c + Pad b + スネア b + bass b)に重ねる / BPM140
  # 根音は bass_p(current.rb にある進行)を使う。sub bass は bass の1オクターブ下(F1 = 43.7Hz 付近)。fold: 25 で Db1〜C2 に収める
  # --- 根音ロング: 毎小節の頭から1小節伸ばす ---
  sub_r = "X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ---- | X--- ---- ---- ----"
  sub = grid_voice :synth, :sine, attack: 0.02, release: 0.3, amp: 0.7
  in_thread do  # sub
    1.times do
        with_fx :level, amp: 1, amp_slide: 0.04 do |duck_fx|
          in_thread { grid_duck duck_fx, kick_p, 0.35, 4 }
          grid_play sub, sub_r, on: bass_p, fold: 25
        end
    end
  end
  # --- 16分の抑揚: x・o・X を並べて、ノリを作る。2・4小節目の最後に少し詰める ---
  hat_p = "x.ox .oxo x.ox .oxo | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox oxox | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox oxox | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox oxox | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox .oxo | x.ox .oxo x.ox oxox"
  hat = grid_voice :sample, :hat_snap, amp: 0.45, hpf: 100, pan: 0.2
  in_thread do  # hat
    1.times do
        grid_play hat, hat_p
    end
  end
  # --- キックと揃えたスタブ: キックの位置(0・3・6 マス目)で和音を短く ---
  keys_r = "X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... .... | X..x ..x. .... ...."
  keys = grid_voice :synth, :piano, vel: 0.25, hard: 0.8, release: 0.3, amp: 0.5, pan: -0.2
  in_thread do  # keys
    1.times do
        grid_play keys, keys_r, on: bass_p, fold: 48, chord: true
    end
  end
  # Solo Violin(メロディ)+ Cello(メロディの 3度下を 1オクターブ低くハモる)。
  # 前半(0〜7マス目)= ベース・キックが強く打つので長い音、後半(8〜15マス目)= ベースが落ち着くので細かく。supersaw の和音は前半だけ(13 と同じ)。
  # --- 和音(前半だけ。13_sup_callresp と同じ)---
  sup_chord_r = "X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... .... | X--- ---- .... ...."
  sup_chord = grid_voice :synth, :supersaw, cutoff: 100, detune: 0.3, attack: 0.02, release: 0.4, amp: 1.0, pan: 0.0
  # --- 弦楽器のメロディ ---
  # 1小節に 7音: 前半の長い音(1つ)+ 後半の細かいフレーズ(6つ)。長い音は和音の5度・7度・3度で、前の小節の終わりからグライドでつながる
  # ドロップAと同じ弾き方: ドロップAの4小節のフレーズを、16小節ぶん4回繰り返す(後半8小節でコードが替わっても、同じフレーズ)
  str_hold_a = [:f5, :c5, :eb5, :d5]
  str_phrase_a = [
    [:c5, :eb5, :f5, :eb5, :c5, :ab4],      # Fm7
    [:db5, :f5, :ab5, :f5, :c5, :db5],      # Dbmaj7
    [:eb5, :g5, :ab5, :g5, :eb5, :c5],      # Abmaj7
    [:f5, :d5, :bb4, :c5, :d5, :f5],        # Bb(借用 IV)。最後は F5 で、アウトロの Fm7 の根音につながる
  ]
  str_n = str_phrase_a.each_with_index.map { |ph, b| [str_hold_a[b]] + ph } * 4
  # リズム: 0マス目から 8マス(2拍)の長い音 → 後半は x.xo x.xo の6音
  str_r = "x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo | x--- ---- x.xo x.xo"
  # --- Solo Violin(メロディ)と Cello(ハモリ)---
  # Solo Violin: blade(ビブラート付き)。長い音はビブラートが遅れて入り(vibrato_delay)、音量が膨らむ(swell)。右寄り。
  # 楽器: チップチューン系(8ビットゲーム機のような矩形波)。glitch の質感(デジタル・硬い倍音)に近づける。メロディ = chiplead。ハモリ(chipbass)はなくし、アルペジオを散りばめる
  # (前の版は blade〔ヴァイオリン〕と blade〔チェロ〕、その次は chiplead + chipbass のハモリ。メロディ・進行・強弱・9度は変えていない)
  lead_hi = grid_voice :synth, :chiplead, release: 0.3, amp: 0.4, pan: 0.2
  # 強弱(dynamics)。小節ごとの全体の大きさ(だんだん強く、4小節目は着地へ少し弱める)と、フレーズ内の音ごとの大きさ(山の頂点で最大、終わりで着地)。
  # 並びは [長い音, 細かい6音]。数字は 0〜1 の大きさ
  # 9度の音名(C=0)。ドロップAと同じ [Fm7 = G(7), Dbmaj7 = Eb(3), Abmaj7 = Bb(10), Bb = C(0)] を4回繰り返す(フレーズがドロップAと同じなので、トップノートの 9度もドロップAと同じにする)
  ninth_pc = [7, 3, 10, 0] * 4
  dyn_bar = [0.9, 0.95, 1.0, 0.95] * 4   # ドロップに入ってからも小さくならないよう、最初の小節も 0.9 から
  dyn_note_a = [
    [0.9, 0.7, 0.8, 1.0, 0.8, 0.7, 0.6],     # Fm7
    [0.8, 0.8, 0.9, 1.0, 0.85, 0.7, 0.65],   # Dbmaj7
    [0.9, 0.8, 0.95, 1.0, 0.9, 0.75, 0.6],   # Abmaj7
    [0.8, 0.9, 0.75, 0.6, 0.7, 0.85, 1.0],   # Bb(借用 IV)
  ]
  dyn_note = dyn_note_a * 4
  in_thread do  # sup_chord
    1.times do
        with_fx :level, amp: 1, amp_slide: 0.04 do |duck_fx|
          in_thread { grid_duck duck_fx, kick_p, 0.3, 6 }
          with_fx :reverb, room: 0.7, mix: 0.3, damp: 0.6 do
            grid_each(sup_chord_r) do |i, len, lvl, c|
              opts = sup_chord[:opts].merge(amp: sup_chord[:opts][:amp] * lvl, sustain: [len * grid_step - sup_chord[:opts][:attack], 0.05].max)
              with_synth(sup_chord[:name]) { play pad_p[(i / grid_bar_cells) % pad_p.size].map { |n| note(n) + 12 }, opts }
            end
          end
        end
    end
  end
  # Solo Violin: str_n の音をそのままの高さで弾く(音程は滑らせない)。長い音は 1拍かけて音量が膨らみ、細かい音は dyn_note × 小節の強弱 × 強さ(x・o)で鳴らす。
  # 深いリバーブ(room 0.9、mix 0.45)で響かせる
  in_thread do  # lead_hi
    1.times do
        with_fx :reverb, room: 0.9, mix: 0.45, damp: 0.5 do
          with_fx :eq, high_shelf: -0.6, high_shelf_note: 88, high_shelf_slope: 0.5 do   # chiptune の高音を削る(約 1.3kHz より上を下げる)
          k = 0
          held_last = false   # 最後の音を伸ばし切ったか(伸ばしたら、リバーブの尾が切れないよう、ループの終わりで待つ)
          grid_each(str_r) do |i, len, lvl, c|
            bar = (i / grid_bar_cells) % str_n.size
            k = 0 if i % grid_bar_cells == 0
            n = note(str_n[bar][k])
            loud = lead_hi[:opts][:amp] * lvl * dyn_bar[bar] * dyn_note[bar][k]
            if len > 2
              # 長い音: 小さく始めて、1拍かけて loud まで膨らむ(swell)
              s = synth lead_hi[:name], lead_hi[:opts].merge(note: n, amp: loud * 0.35, amp_slide: 1.0, attack: 0.2, sustain: len * grid_step - 0.2)
              control s, amp: loud
              # 9度のテンション: 長い音の上に、そのコードの 9度を最高音として重ねる(短3度以上離れた一番近い音)。音量は 0.7 倍
              nine = n + 3
              nine += 1 until nine % 12 == ninth_pc[bar]
              s9 = synth lead_hi[:name], lead_hi[:opts].merge(note: nine, amp: loud * 0.7 * 0.35, amp_slide: 1.0, attack: 0.2, sustain: len * grid_step - 0.2)
              control s9, amp: loud * 0.7
            else
              # ドロップの最後のメロディ(最後の小節の最後の音)は、短く切らずに伸ばし切る(3拍保持 + 2拍の余韻)。ドロップAは 4小節ループなので、最後の回(get[:last_pass])だけ
              if bar == str_n.size - 1 && k == str_n[bar].size - 1 && (str_n.size > 4 || get[:last_pass] == true)
                held_last = true
                synth lead_hi[:name], lead_hi[:opts].merge(note: n, amp: loud, attack: 0.03, sustain: 3.0, release: 2.0)
              else
                with_synth(lead_hi[:name]) { play n, lead_hi[:opts].merge(amp: loud, attack: 0.03, sustain: [len * grid_step - 0.03, 0.05].max) }
              end
            end
            k += 1
          end
          sleep 4 if held_last   # 伸ばした音の響きを待つ
          end
        end
    end
  end
  # --- チップ系のアルペジオ(ハモリの代わり): 和音の構成音を、メロディの隙間に散りばめる ---
  # 1小節(16マス)に 6発だけ(1・3・4・6・9・13 マス目)。メロディの音(0・8・10・11・12・14・15 マス目)と重ならない位置。o = 弱、x = ふつう
  arp_bar = ".o.o x.x. .o.. .o.."
  # 和音の構成音の何番目(0〜3)を鳴らすか。下から上、また下へ: 0 → 1 → 2 → 3 → 2 → 1(1小節に 6発)
  arp_order = [0, 1, 2, 3, 2, 1]
  # パン(左右)。1発ごとに交互に振り分けて、散りばめる
  arp_pan = [-0.5, 0.5, -0.3, 0.3, -0.6, 0.6]
  arp = grid_voice :synth, :chiplead, release: 0.2, amp: 0.25
  arp_r = ([arp_bar] * 16).join(" | ")
  in_thread do  # lead_arp
    1.times do
        with_fx :reverb, room: 0.6, mix: 0.3, damp: 0.6 do
          with_fx :eq, high_shelf: -0.6, high_shelf_note: 88, high_shelf_slope: 0.5 do   # chiptune の高音を削る(約 1.3kHz より上を下げる)
          k = 0
          grid_each(arp_r) do |i, len, lvl, c|
            bar = (i / grid_bar_cells) % pad_p.size
            k = 0 if i % grid_bar_cells == 0
            note_n = note(pad_p[bar][arp_order[k % arp_order.size]]) + 12   # 和音の構成音を 1オクターブ上げる(F4〜E♭5 付近)
            with_synth(arp[:name]) { play note_n, arp[:opts].merge(amp: arp[:opts][:amp] * lvl, pan: arp_pan[k % arp_pan.size], attack: 0.01, sustain: [len * grid_step * 0.5, 0.05].max) }
            k += 1
          end
          end
        end
    end
  end
  # --- ボコーダーの声の16分チョップ(アルペジオに重ねる)---
  # 声は NEUTRINO で歌わせ(work/vocals/01_arp_*.json)、調声して、ボコーダーにかけたもの(vocode.py。DSP のみ)。アルペジオと同じ音を、同じタイミングで歌っている。
  # 元の wav は 4小節 = 16拍(BPM130 で 7.385秒)。アルペジオの6つの位置で、各音の頭から 16分(0.25拍)ずつ切って鳴らす
  vox_a = grid_clip "/Users/nagutabby/sonicpi-live-agent/work/vocals/01_arp_a_tuned_voc_v2.wav", 16   # Fm7 → Dbmaj7 → Abmaj7 → Bb(ドロップAの進行)
  vox_b = grid_clip "/Users/nagutabby/sonicpi-live-agent/work/vocals/01_arp_b_tuned_voc_v2.wav", 16   # Fm7 → Bbm7 → Dbmaj7 → Ebmaj7(ドロップB 後半の進行)
  vox_pos = [0.25, 0.75, 1.0, 1.5, 2.25, 3.25]                                    # 1小節の中の、アルペジオの6つの位置(拍)。声の各音の頭と同じ
  vox_from4 = (0..3).flat_map { |b| vox_pos.map { |p| b * 4 + p } }                # 4小節ぶん(24個)
  # ドロップB: 前半8小節はフレーズA、後半8小節(和音が替わる)はフレーズB。どちらも 4小節のフレーズを2回ずつ
  vox_arp8 = ([arp_bar] * 8).join(" | ")
  in_thread do  # lead_vox
    1.times do
        with_fx :reverb, room: 0.85, mix: 0.5, damp: 0.5 do
          grid_chop vox_a, vox_arp8, from: vox_from4 + vox_from4, amp: 0.7, pan: 0.0, attack: 0.03   # attack は標準 0.008拍 → 0.03拍(約14ms)。頭が少し丸くなる
          grid_chop vox_b, vox_arp8, from: vox_from4 + vox_from4, amp: 0.7, pan: 0.0, attack: 0.03   # attack は標準 0.008拍 → 0.03拍(約14ms)。頭が少し丸くなる
        end
    end
  end
  # --- 低いタムのゴースト: 3拍目のスネアの前後に、弱いタムを置く(コンガ風)---
  perc_p = ".... .... .... .o.. | .... .... .... ..o. | .... .... .... .o.. | .... .... .... o.o."
  perc = grid_voice :sample, :drum_tom_mid_soft, amp: 0.6, pan: -0.3, rate: 1.2
  in_thread do  # perc
    4.times do
        grid_play perc, perc_p
    end
  end
  # --- 4小節の終わりに、グリッチ音を32分で3発(高さを上げる)---
  in_thread do  # glitch
    4.times do
        sleep 15.25
        3.times do |k|
          sample :glitch_perc2, rate: 1.0 + 0.3 * k, amp: 0.7
          sleep 0.25
        end
    end
  end
  # (ピッチドロップは削除。ドロップBの最後は、アウトロの頭の Fm7 へそのままつなぐ。余韻は各楽器のリリースとリバーブの尾で残る)
  sleep 64
end


# ======== outro(40拍)========
define :grid_song_outro do
  # --- リズム(8小節 = 128マス)---
  # 数字は音の強さ。2小節ごとに 1つの和音を伸ばし、9 → 5 へ少しずつ弱くなる(イントロの逆)。最後の和音は余韻(release)で長く残す
  pad_r = "9--- ---- ---- ---- | ---- ---- ---- ---- | 8--- ---- ---- ---- | ---- ---- ---- ---- | 7--- ---- ---- ---- | ---- ---- ---- ---- | 6--- ---- ---- ---- | ---- ---- ---- ----"
  # --- 進行(2小節に1コード。音の高さは低い順。近接転回: 1 → 2 は Eb が Db に、2 → 3 は C が Bb に、3 → 4 は Bb が C・Db が Eb に動く)---
  pad_p = [
    [:f3, :ab3, :c4, :eb4],   # Fm7
    [:f3, :ab3, :c4, :db4],   # Dbmaj7
    [:f3, :ab3, :bb3, :db4],  # Bbm7
    [:f3, :ab3, :c4, :eb4],   # Fm7(主和音に戻る)
  ]
  # --- 音: イントロと同じ supersaw(cutoff は 70 → 50 へ閉じる。暗く静かに消える)---
  pad = grid_voice :synth, :supersaw, cutoff: 70, detune: 0.2, env: :pad, amp: 0.4
  # 1回だけ鳴らして止まる(stop)。reverb は最後の和音の余韻まで生かすため、鳴らし終わってから 8拍(約 3.4秒)待つ
  in_thread do  # pad
    1.times do
        with_fx :reverb, room: 1, mix: 0.7, damp: 0.4 do
          grid_each(pad_r) do |i, len, lvl, c|
            bar = i / grid_bar_cells
            chord_i = bar / 2
            last = (chord_i == 3)
            opts = pad[:opts].merge(amp: pad[:opts][:amp] * lvl, cutoff: 70 - 20 * bar / 7.0,
                                    sustain: [len * grid_step - pad[:opts][:attack], 0.05].max)
            # 2小節ぶん(8拍)伸ばす。最後の和音だけ release を 6拍に伸ばして、余韻を残す
            opts = opts.merge(sustain: 8 - pad[:opts][:attack], release: 6.0) if last
            with_synth(pad[:name]) { play pad_p[chord_i], opts }
          end
          sleep 8
        end
    end
  end
  sleep 40
end


# ======== 通して鳴らす ========
# 曲の進行は in_thread の中で順に呼ぶ(メインの流れを待たせないため。録音スクリプトは、メインの流れが指定の秒数で終わることを前提にしている)
in_thread do
  grid_song_intro
  grid_song_build
  grid_song_dropA
  grid_song_buildup
  grid_song_dropB
  grid_song_outro
end
