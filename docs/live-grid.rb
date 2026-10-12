# グリッド記法のヘルパー(Sonic Pi 内蔵のみ)。規約は docs/coding-rules.md、検証は scripts/check_grid.py。
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
