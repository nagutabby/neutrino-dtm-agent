# グリッド記法のヘルパー(Sonic Pi 内蔵のみ)。規約は docs/coding-rules.md、検証は scripts/check_grid.py。
# 使い方: このファイルの define 部分を current.rb の先頭(use_bpm の次)に貼る。使い方の例は examples/grid_demo.rb。
# 名前はすべて grid_ で始める(Sonic Pi のコア API の名前と衝突させないため)。
#
# グリッド: 1小節 = 4拍 = 16マス(1マス = 16分音符 = 0.25拍)。空白と | は見やすくするだけで無視される。
#   x = ふつう / X = 強く / o = 弱く(ゴースト) / . = 休み / - = 直前の音を1マス伸ばす(例: "x-- " は3マスぶん)
#   例: "x... x... x... x..." (四つ打ち)  ".... ..x. .... ..x." (裏拍)
# 小節数はマスの数から決まる(16マス = 1小節、32マス = 2小節)。パターンは 16 の倍数にする。
# grid_play / grid_chop は、パターンの長さぶん sleep する(live_loop の中で sleep を別に書かない)。

# 音に名前を付ける。kind は :synth か :sample、name はシンセ名・サンプル名(またはパス)、opts は音色のパラメータ
define :grid_voice do |kind, name, opts = {}|
  { kind: kind, name: name, opts: opts }
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

# 音の強さ: o < x < X
define :grid_level do |c|
  { "X" => 1.0, "x" => 0.75, "o" => 0.4 }[c]
end

# 1つの音の長さ(マス数): 自分 + 直後に続く "-" の数
define :grid_len do |cells, i|
  n = 1
  n += 1 while cells[i + n] == "-"
  n
end

# voice を pattern どおりに鳴らす。オプション o:
#   on: 進行(grid_prog)。小節ごとに根音(既定)またはコード(chord: true)を鳴らす
#   note: on: が無いときの音(シンセ用。例 :f2)
define :grid_play do |voice, pattern, o = {}|
  cells = grid_cells(pattern)
  cells.each_with_index do |c, i|
    lvl = grid_level(c)
    if lvl
      len = grid_len(cells, i)
      opts = voice[:opts].merge(amp: (voice[:opts][:amp] || 1.0) * lvl)
      if voice[:kind] == :sample
        sample voice[:name], opts
      else
        if o[:on]
          root, type = o[:on][(i / 16) % o[:on].size]
          n = o[:chord] ? chord(root, type) : note(root)
        else
          n = o[:note]
        end
        opts = opts.merge(sustain: len * 0.25) if len > 1
        with_synth(voice[:name]) { play n, opts }
      end
    end
    sleep 0.25
  end
end

# 元の wav (grid_clip) を切り貼りして鳴らす(ボーカルチョップ)。元の wav は加工しない。
#   from: 各音が使う元の拍位置の並び(音の数と同じ個数)。省略すると、元の先頭から順に続けて進む
#   amp: / pan: / attack: / release: は sample にそのまま渡す(attack 0.008 / release 0.06 が既定。切り口のプチ音を消す)
define :grid_chop do |clip, pattern, o = {}|
  cells = grid_cells(pattern)
  pos = 0.0
  k = 0
  cells.each_with_index do |c, i|
    lvl = grid_level(c)
    if lvl
      len = grid_len(cells, i) * 0.25
      from = o[:from] ? o[:from][k] : pos
      k += 1
      opts = { attack: 0.008, release: 0.06 }.merge(o.reject { |key, _| key == :from })
      opts = opts.merge(amp: (opts[:amp] || 1.0) * lvl, start: from / clip[:beats],
                        finish: [(from + len) / clip[:beats], 1.0].min)
      sample clip[:name], opts
      pos = from + len
    end
    sleep 0.25
  end
end
