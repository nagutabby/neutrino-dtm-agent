# Dark Future Bass x Phonk（Eb マイナー / BPM 140 / 64小節 ≒ 115秒）
# スタイル②: AI が Sonic Pi のコードを書き、ユーザーが聴いて方向・採否を決めた。制作メモは dark_future_bass_phonk_notes.md
# 使い方: このファイル全体を Sonic Pi に貼って実行する（ヘルパー関数を含む）。64小節で自動的に止まる。構成は grid_song_* の関数で切り替える
# Dark Future Bass x Phonk / Eb minor / 140 BPM / ハーフタイム
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
  chords.map { |c| c.is_a?(Array) ? c : [c] }
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
        raise "grid: chord: true には進行に種類が必要です" if o[:chord] && type.nil?
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

# --- 溜め・跳ね・付点・息継ぎ（この曲だけの関数。docs/live-grid.rb には入れていない）---
# 溜め: 強い音（lvl: X = 1.0 / x = 0.75 / o = 0.4）ほど深く遅らせる。遅れ = amount × lvl（拍）。戻り値を time_warp に渡す
#   cells: を渡すと、小節内のそのマスの音だけ遅らせる（例 [2, 6, 10, 14] = 裏拍）
define :grid_tame do |i, lvl, amount = 0.12, o = {}|
  cells = o[:cells]
  cells && !cells.include?(i % grid_bar_cells) ? 0 : amount * lvl
end

# 跳ね: 裏のマスを amount × 1マス だけ遅らせる。every: 1 = 16分の裏（奇数マス）/ 2 = 8分の裏（4で割って2余るマス）。amount 0.33 で3連符の跳ね
define :grid_swing do |i, amount = 0.33, o = {}|
  every = o[:every] || 1
  off = every == 1 ? (i % 2 == 1) : (i % 4 == 2)
  off ? amount * grid_step : 0
end

# 付点リズム: 正の数 = 音の長さ（マス）、負の数 = 休み（マス）からグリッド文字列を作る。足りない分は休みで埋める。例: [3, 1, -2] → "X--X.." + 休み
define :grid_dotted do |lens|
  s = lens.map { |l| l > 0 ? "X" + "-" * (l - 1) : "." * (-l) }.join
  s + "." * ((-s.size) % grid_bar_cells)
end

# 息継ぎ: 音（正の数 = マス）のあとに、長さに比例した休み（長さ × ratio、最低 1マス）を入れる。負の数 = 最初から入れる休み。
#   before: キックやスネアの直前にしたいマス（小節内）。直前のマスが音なら、そこから先を休みにして音を短くする（頭にあれば消す）
define :grid_breath do |lens, ratio = 0.5, o = {}|
  s = lens.map { |l| l < 0 ? "." * (-l) : "X" + "-" * (l - 1) + "." * [(l * ratio + 0.5).floor, 1].max }.join
  s += "." * ((-s.size) % grid_bar_cells)
  c = s.chars
  total = c.size
  (total / grid_bar_cells).times do |b|
    (o[:before] || []).each do |onset|
      t = (b * grid_bar_cells + onset - 1) % total
      next if c[t] == "."
      c[t] = "."
      k = t + 1
      while k < total && c[k] == "-"
        c[k] = "."
        k += 1
      end
    end
  end
  c.join
end

# 繰り返しのフレーズ: 音の列（notes）と強さ（accs）を 2回並べ、最後の 1音だけ変える。[音の列, 強さの列] を返す
#   1回目の終わりは tail_a（続く感じ）、2回目の終わりは tail_b（着地）。強さも tail_acc_a / tail_acc_b で別にできる
#   山なりにするには、notes を「上がる音 → 頂点 → 下がる音」の順に書く（頂点の強さを 1.0 にすると溜めも深くなる）
define :grid_repeat_phrase do |notes, accs, tail_a, tail_b, tail_acc_a = 0.75, tail_acc_b = 1.0|
  [notes + [tail_a] + notes + [tail_b], accs + [tail_acc_a] + accs + [tail_acc_b]]
end

# 耳の疲労度: パターン（グリッド文字列）と音色オプション（cutoff:）から 0〜100 のスコアと判定を返す。
#   密度（音の頭の割合 × 45）+ 高域（cutoff が 90 を超えた分 × 0.9）+ 連続攻撃（音の頭が隣り合って続く最大数 × 1.8）。65 超 = 警告 / 30 未満 = 快適（基準を少し厳しくした: 重み 40/0.8/1.5 → 45/0.9/1.8、警告 70 → 65）
#   数えるのは音の頭（X x o と数字）だけで、伸ばし（-）は数えない
define :grid_fatigue_score do |pattern, opts = {}|
  cells = grid_cells(pattern)
  total_cells = cells.size.to_f

  # 1. 密度スコア: 音符（強弱があるマス）の割合（詰まり具合）
  notes = cells.count { |c| grid_level(c) != nil }
  density_ratio = notes / total_cells
  density_score = density_ratio * 45 # 最大45点

  # 2. 高域スコア: カットオフが高いほど耳に刺さる（デフォルト130と仮定）
  cutoff = opts[:cutoff] || 130
  cutoff_score = [(cutoff - 90), 0].max * 0.9 # 90以上から加点、最大36点

  # 3. 連続攻撃スコア: 休符（'.'）が連続せず、ずっと音が鳴り続けているか
  max_consecutive = 0
  current_consecutive = 0
  cells.each do |c|
    if grid_level(c) != nil
      current_consecutive += 1
      max_consecutive = [max_consecutive, current_consecutive].max
    else
      current_consecutive = 0
    end
  end
  consecutive_score = [max_consecutive, 16].min * 1.8 # 連続するほど疲れる（最大28.8点）

  # 合計スコア（100点満点に近いほど、耳が疲れる攻撃的な音）
  score = (density_score + cutoff_score + consecutive_score).round(1)

  # 判定メッセージ
  warning = if score > 65
    "警告: 音圧・高域がキツく、リスナーがすぐに疲れる可能性があります（アグレッシブすぎ）"
  elsif score < 30
    "快適: 空間（間）が多く、耳に優しいチルな状態です"
  else
    "良好: Phonk / Future Bass として適切な緊張感とグルーヴがあります"
  end

  [score, warning]
end

use_bpm 140
set_sched_ahead_time! 1   # 先読みを 1 秒に増やす（ループが多いと「thread got too far behind time」になるため）
grid_res 4
grid_meter 4

# --- 曲の構成（セクションごとの鳴らす楽器・進行。構成の確認で決める。work/structure.md に記録）---
# 64小節: イントロ 8 → ビルド 6 → ドロップ前の静寂 2 → ドロップ 16 → ブレイク 8 → ドロップ 16 → アウトロ 8
# 各ステムの live_loop は grid_gate の中で鳴らす。grid_gate は「いま何小節目か」を数えて、そのセクションで鳴らすステムなら中身を実行し、鳴らさないなら同じ長さだけ sleep する
define :grid_song_section do |bar|
  if bar < 8 then :intro
  elsif bar < 14 then :build
  elsif bar < 16 then :predrop
  elsif bar < 32 then :drop
  elsif bar < 40 then :break
  elsif bar < 56 then :drop
  elsif bar < 64 then :outro
  else :end
  end
end
# 土台（リズムと低音: ドラム・ベース・低音ピアノ・パワーコード）と上モノ（和音と高音: スタブ・glitch・ピアノ（上）・カウンター・ライザー）に分ける。セクションごとに、それぞれ何を鳴らすか決める
define :grid_song_base do |sec|
  case sec
  when :intro  then [:hat, :bass_sub]
  when :build  then [:kick, :kick3, :snare, :hat, :piano_lo, :kick_rev, :bass_sub, :bass_saw]
  when :predrop then [:kick_rev]   # ドロップ前の静寂: ドラムもベースも止めて、逆再生キックだけ残す
  when :drop   then [:kick, :kick3, :kick_strong, :kick_rev, :snare, :hat, :bass_sub, :bass_saw, :piano_lo, :power]
  when :break  then [:piano_lo, :bass_sub]
  when :outro  then [:hat, :piano_lo, :bass_sub]
  else []
  end
end
define :grid_song_top do |sec|
  case sec
  when :intro  then [:stabs]
  when :build  then [:stabs]
  when :predrop then []
  when :drop   then [:stabs, :dom7, :glitch, :piano_up]
  when :break  then [:stabs, :piano_up]
  when :outro  then [:stabs]
  else []
  end
end
# セクションの頭からの小節数（0 始まり）。ピアノのリフの 16小節ループを、各セクションの頭から始めるために使う
define :grid_song_rel do |bar|
  starts = [0, 8, 14, 16, 32, 40, 56]
  bar - starts.select { |st| st <= bar }.max
end
define :grid_song_stems do |sec|
  grid_song_base(sec) + grid_song_top(sec)
end
# ベースの根音（MIDI。27 未満は 1オクターブ上げる）。4小節ぶん
define :grid_song_roots do |sec|
  names = case sec
          when :intro, :outro then [:eb1, :eb1, :cb1, :cb1]
          when :build then [:ab1, :cb1, :db1, :bb1]
          when :break then [:gb1, :db1, :eb1, :cb1]
          else [:eb1, :cb1, :ab1, :bb1]
          end
  names.map { |r| n = note(r); n += 12 while n < 27; n }
end
# コード進行（4小節）
define :grid_song_chords do |sec|
  case sec
  when :intro, :outro then grid_prog [:eb4, :m9], [:eb4, :m9], [:cb4, :major7], [:cb4, :major7]
  when :build then grid_prog [:ab4, :minor7], [:cb4, :major7], [:db4, :major7], [:bb3, :dom7]
  when :break then grid_prog [:gb4, :major7], [:db4, :major7], [:eb4, :m9], [:cb4, :major7]
  else grid_prog [:eb4, :m9], [:cb4, :major7], [:ab4, :minor7], [:bb3, :dom7]
  end
end
# bars 小節ぶんを 1回として、鳴らすステムなら blk を呼ぶ（blk の中で sleep する）。鳴らさないなら bars 小節ぶん sleep。64 小節を過ぎたらそのループを止める
define :grid_gate do |name, bars, &blk|
  tick_bar = tick(name) * bars
  sec = grid_song_section(tick_bar)
  stop if sec == :end
  if grid_song_stems(sec).include?(name)
    blk.call(sec, grid_song_roots(sec), tick_bar)
  else
    sleep bars * 4
  end
end

# --- 音色・パターン ---
kick  = grid_voice :sample, :bd_klub, amp: 1.0, lpf: 100
kick3 = grid_voice :sample, :bd_haus, amp: 0.9, lpf: 100   # 重ねるキック（太く長い bd_fat）。kick と同じ k_pat で鳴らす
k_pat = "X..x ..x. X... ..x. | X..x ..x. ..X. ...."

snare = grid_voice :sample, :perc_snap, amp: 1.2   # フィンガースナップ
s_pat = ".... .... X... .... | .... .... X... ...."

hat   = grid_voice :sample, :hat_snap, amp: 0.4, finish: 0.5
h_pat = "x.o. x.o. x.o. x.o. | x.o. x.o. x.o. x.o."   # 8分の刻み、強弱だけ
# ハットのビルド: ドロップに向かって、8分 → 8分 + 裏の 16分 → 16分の連打 と、刻みを細かくして盛り上げる（2小節ごとに 1段階）
#   ビルド 9-10小節: 8分 / 11-12小節: 8分の間に弱い 16分を足す / 13-14小節: 16分の連打（拍の頭を強く）。そのあと 15-16小節は静寂
h_pat_build = [
  h_pat,
  "x.oo x.oo x.oo x.oo | x.oo x.oo x.oo x.oo",
  "Xxxx Xxxx Xxxx Xxxx | Xxxx Xxxx Xxxx Xxxx",
]
define :grid_hat_pat do |sec, bar, base, build|
  if sec == :build
    build[[(bar - 8) / 2, build.size - 1].min]
  else
    base
  end
end

# ベース: アタック遅め(:mid = 0.1拍)・リリース短め(:cut = 0.03拍)。進行は i - bVI - iv - V(Eb - Cb - Ab - Bb)。ベースは根音だけ。音量は sub 0.8・saw 0.125（sub を厚く。saw は半分のまま）
bass_p = grid_prog :eb1, :cb1, :ab1, :bb1   # ベースは根音だけ（種類は不要）
sub    = grid_voice :synth, :sine, amp: 0.8, attack: :mid, release: :cut
saw    = grid_voice :synth, :saw, amp: 0.125, attack: :mid, release: :cut, cutoff: 75
# ベースは 4分音符（4マスごと、1小節に 4音）。1・3拍目を強く、2・4拍目をふつうにして、頭は拍に置く
b_bars = Array.new(4) { "X--- x--- X--- x---" }
b_pat  = b_bars.join(" | ")

# 808 スライド（採用: D）: 3拍目の半ばで5度上へ跳ね、4拍目の頭から根音へ滑り降りる（5度の跳ね。0.2拍）
# 根音の高さ（MIDI）: fold 27（27 より低い音は 1オクターブ上げる）を自分で計算する。滑らせるので sub と saw を別々に書かず、まとめて鳴らす
bass_midi = [:eb1, :cb1, :ab1, :bb1].map { |r| n = note(r); n += 12 while n < 27; n }
# 1音ぶん: i = マス番号, len = 音のマス数, lvl = 強さ。grid_each の中から呼ぶ
define :grid_slide_note do |i, len, lvl, syn, amp, extra, rts|
  use_synth syn
  begin
    b = (i / 16) % 4
    cp = i % 16
    r = rts[b]
    nxt = rts[(b + 1) % 4]
    o = { amp: amp * lvl, attack: 0.1, sustain: [len * 0.25 - 0.13, 0.05].max, release: 0.03 }.merge(extra)
    if cp == 8
      nd = play r, **o, note_slide: 0.1
      time_warp 0.5 do control nd, note: r + 7 end
    elsif cp == 12
      nd = play r + 7, **o, note_slide: 0.2
      control nd, note: r
    else
      play r, **o
    end
  end
end

# コード: supersaw のスタブ。進行は [根音, 種類]。chord: true で和音全体を鳴らす（4小節、1小節に1つ）
# つなぎ = 共通音保持 / 2小節目後半の Eb7(セカンダリードミナント)/ 4小節目は Bb7（属七。ループの頭の Ebm へ戻る）
chord_p  = grid_prog [:eb4, :m9], [:cb4, :major7], [:ab4, :minor7], [:bb3, :dom7]   # i / bVI / iv / V7（Eb マイナーの属七。Bb7 の3度 D はスケール外）。9th は外した（Ebm9 だけ残す）
dom_p    = grid_prog [:eb4, :dom7]   # 2小節目の後半だけ使う Eb7（次の Abm7 へ向かうセカンダリードミナント）
stab     = grid_voice :synth, :supersaw, amp: 0.8, attack: :fast, release: :short, cutoff: 100, detune: 0.2, cut: 0.13
c_bar    = "X--. ..x- ..X- ...."
c_pat    = "#{c_bar} | X--. ..x- .... .... | #{c_bar} | #{c_bar}"   # 2小節目は前半だけ
# glitch: 小節の最後の1拍（12〜15マス）だけ、同じ和音を 16分でこま切れにする（音を短く切る cut 0.05）。2小節目は軽く 1音、4小節目は 4連で目立たせる
glitch   = grid_voice :synth, :supersaw, amp: 0.6, attack: :fast, release: :short, cutoff: 100, detune: 0.2, cut: 0.05
g_pat    = ".... .... .... .... | .... .... .... ..x. | .... .... .... .... | .... .... .... xoXx"
d_pat    = ".... .... .... .... | .... .... ..X- .... | .... .... .... .... | .... .... .... ...."   # 2小節目の後半だけ Db7

# --- サイドチェイン（キックに合わせて、ほかの音を凹ませる）---
# Sonic Pi には外部入力のサイドチェインがないので、with_fx :level の amp をキックの位置で一瞬下げて、すぐ戻すことで作る（疑似サイドチェイン）。
#   キックの主な位置（k_pat の X: 小節の 0・8マス、偶数小節は 0・10マス）で amp を depth まで落とし、rel 拍かけて 1 に戻す。
#   凹ませるのは、ベース・コード（スタブと glitch）・ピアノ 2本・パワーコード。キック・スネア・ハット・カウンター・vox・リバースキックは凹ませない
sc_depth = 0.3    # キックの瞬間の音量（1.0 = そのまま、0 = 無音）。小さいほど深く凹む
sc_rel   = 0.35   # 元の音量に戻る長さ（拍）。長いほどゆっくり息をする
sc_pat   = "X... .... X... .... | X... .... ..X. ...."
define :grid_pump_hit do |node, depth, rel|
  control node, amp: depth, amp_slide: 0.01
  time_warp 0.02 do
    control node, amp: 1, amp_slide: rel
  end
end

# --- 止める（ブレイク）: ドロップの 4小節ごとの終わりで、すべての音をスパッと止めて無音にする ---
# 4小節目・12小節目…の終わりは 0.5 拍、8小節目・16小節目…の終わりは 1 拍、master の amp を 0 にする。無音のあとの小節の頭のキックとベースが目立つ。
# リバースキックだけは master の外に置いて、無音の中を通り抜けて、小節の頭へ吸い込まれるようにする
gap4 = 0.5   # 4小節ごとの無音の長さ（拍）
gap8 = 1.0   # 8小節ごとの無音の長さ（拍）
with_fx :level, amp: 1 do |master|
  live_loop :gap do
    b = tick(:gap)
    stop if b >= 64
    if grid_song_section(b) == :drop && b % 4 == 3
      g = (b % 8 == 7) ? gap8 : gap4
      sleep 4 - g
      control master, amp: 0, amp_slide: 0.005
      sleep g - 0.03
      control master, amp: 1, amp_slide: 0.005   # 小節線の少し前に戻して、頭の音が欠けないようにする
      sleep 0.03
    else
      sleep 4
    end
  end

# ============ 土台（リズムと低音）============
# --- ステム ---
with_fx :lpf, cutoff: 100 do
  live_loop :kick do grid_gate(:kick, 2) { |sec, rts| grid_play kick, k_pat } end
  live_loop :kick3 do grid_gate(:kick3, 2) { |sec, rts| grid_play kick3, k_pat } end   # キックを重ねて強くする
  # スナップだけ弱い EQ: 低域を足し(+0.4 @523Hz)、高域を削る(-0.3 @1047Hz)
  with_fx :eq, low_shelf: 0.4, low_shelf_note: 72, high_shelf: -0.3, high_shelf_note: 84 do
    live_loop :snare do grid_gate(:snare, 2) { |sec, rts| grid_play snare, s_pat } end
  end
end

# ハットは高域が命なので、全体の lpf 100 の外。専用の lpf 110(約 4.2kHz 以上を削る)
with_fx :lpf, cutoff: 110 do
  live_loop :hat do grid_gate(:hat, 2) { |sec, rts, bar| grid_play hat, grid_hat_pat(sec, bar, h_pat, h_pat_build) } end
end

# サブ(サイン波)+ 1オクターブ上の鋸波(倍音)
# ベースのディストーション: distort 0.4（量 0〜1）。サイン波のサブに倍音を足して、小さいスピーカーでも低音が聞こえるようにし、荒さを出す。歪みで大きくなるので amp: 0.7 で戻す
with_fx :level, amp: 1 do |sc_bass|   # サイドチェイン: bass
  live_loop :pump_bass do grid_each(sc_pat) { |i, len, lvl, c| grid_pump_hit sc_bass, sc_depth, sc_rel } end
with_fx :distortion, distort: 0.4, mix: 1.0, amp: 0.7 do
  live_loop :bass_sub do grid_gate(:bass_sub, 4) { |sec, rts| grid_each(b_pat) { |i, len, lvl, c| grid_slide_note i, len, lvl, :sine, 0.8, {}, rts } } end
  live_loop :bass_saw do grid_gate(:bass_saw, 4) { |sec, rts| grid_each(b_pat) { |i, len, lvl, c| grid_slide_note i, len, lvl, :saw, 0.125, { cutoff: 75 }, rts } } end
end
end

# --- 低音ピアノのリフ（高音ピアノは外した）---
# :piano はほかのシンセよりずっと大きい。amp は 0.04 前後から始める。vel（弾く強さ）hard（鍵盤の硬さ）を下げて、柔らかく
# リフ: ベースの根音を 1オクターブ上（Eb2 付近）で弾き、根音 → 根音 → 5度 → オクターブ（→ 5度）と跳ねる。位置はキックの 0・3・6・8・10・14 マスに合わせる。3度は使わない（和音が長調と短調で変わるため）
piano_lo_amp = 0.24
lo_pat_bars = ["X..x ..x. X... ..x.",   # 奇数小節: 頭 0 3 6 8 14（キックと同じ）
               "X..x ..x. ..X. ...."]   # 偶数小節: 頭 0 3 6 10
lo_offsets  = [[0, 0, 7, 12, 7],        # 奇数小節: 根音 根音 5度 オクターブ 5度（半音数）
               [0, 0, 7, 12]]           # 偶数小節
lo_pat  = (lo_pat_bars * 2).join(" | ")
lo_off  = (lo_offsets * 2).flatten

# --- ピアノのリフ 16小節ループ（4小節 × 4フレーズ: A → A' → B → C）---
#   A: 今までのリフ / A': A とほぼ同じで 4小節目の終わりに 16分の駆け上がり / B: 高めの音を混ぜた別のリズム / C: 8分の刻みに変えて盛り上げ、最後は 16分で駆け上がる
#   各フレーズは 4小節。セクションの頭（grid_song_rel）から数えて、16小節ごとに一周する。8小節のセクションは A と A' だけ
#   音の高さは根音から 半音数。3度は使わない: 0 = 根音 / 7 = 5度 / 12 = オクターブ / 19 = オクターブ + 5度
riff_a  = ["X..x ..x. X... ..x.", "X..x ..x. ..X. ...."]
riff_a2 = ["X..x ..x. X... ..x.", "X..x ..x. ..X. ..xx"]
riff_b  = ["X.x. ..x. X..x ..x.", "X..x ..X. x.x. ...."]
riff_c  = ["X.x. x.x. X.x. x.x.", "X.x. x.x. X.x. xxxx"]
riff_pats = [(riff_a * 2), (riff_a + riff_a2), (riff_b * 2), (riff_c * 2)].map { |bars| bars.join(" | ") }
riff_offs = [
  ([0, 0, 7, 12, 7] + [0, 0, 7, 12]) * 2,                              # A: 5音 + 4音
  [0, 0, 7, 12, 7] + [0, 0, 7, 12] + [0, 0, 7, 12, 7] + [0, 0, 7, 12, 19, 12],  # A': 最後の小節が 6音
  ([0, 7, 12, 7, 12, 19] + [0, 0, 7, 7, 12]) * 2,                      # B: 6音 + 5音
  ([0, 7, 0, 7, 0, 7, 12, 7] + [0, 7, 0, 7, 0, 7, 12, 12, 19, 19]).then { |x| x + x },  # C: 8音 + 10音
]
riff_pats.each_with_index do |pt, n|
  raise "riff #{n}: 音の数（#{riff_offs[n].size}）がパターンの音の数（#{pt.count("Xxo")}）と違う" if riff_offs[n].size != pt.count("Xxo")
end
with_fx :level, amp: 1 do |sc_pianolo|   # サイドチェイン: pianolo
  live_loop :pump_pianolo do grid_each(sc_pat) { |i, len, lvl, c| grid_pump_hit sc_pianolo, sc_depth, sc_rel } end
with_fx :reverb, room: 0.9, mix: 0.5, damp: 0.5 do   # リバーブ: room は部屋の広さ、mix は原音との割合、damp は高域の吸収（大きいほど暗い残響）
    live_loop :piano_lo do
      grid_gate(:piano_lo, 4) do |sec, rts, bar|
        use_synth :piano
        ph = (grid_song_rel(bar) / 4) % 4   # 16小節ループのどのフレーズか
        offs = riff_offs[ph]
        k = 0
        grid_each(riff_pats[ph]) do |i, len, lvl, c|
          # 4小節で 1周（ベースの根音を追う）。強い音ほど少し遅らせる（溜め）
          time_warp grid_tame(i, lvl, 0.1) do
            play rts[(i / 16) % 4] + 12 + offs[k], amp: piano_lo_amp * lvl, hard: 0.25, vel: 0.25, sustain: [len * 0.25 - 0.1, 0.1].max, release: 0.3
          end
          k += 1
        end
      end
    end
end
end

# --- 強いキック（リフと重ねる）+ リバースキック ---
# 強いキック: 低音ピアノのリフ（lo_pat）と同じ位置に、重いキック（bd_boom）を重ねる。リフの頭ごとに、低域の太いキックが一緒に鳴る
kick2 = grid_voice :sample, :bd_boom, amp: 1.2, lpf: 100
with_fx :lpf, cutoff: 100 do
  live_loop :kick_strong do grid_gate(:kick_strong, 4) { |sec, rts| grid_play kick2, lo_pat } end
end

# --- パワーコード（根音 + 5度 + オクターブ。3度を弾かないので、長調・短調のどちらにも聞こえて、重く攻撃的になる）---
# ペダルポイント: 根音 Eb（Eb3 + Bb3 + Eb4）に固定して、ベースが Cb・Ab・Bb に動いても同じ和音を刻み続ける。ギターのように歪ませる。3度がないので、Cbmaj7 の明るさも出ない
#   頭の X は長く（コードの響きを残す）、x は短く切る（ブリッジミュート風のチャグ）。位置は 0 2 6 8 12 14（キックの 0・6・8・14 と重なる）
pc_pat = "X.x. ..x. X... x.x."
pc_amp = 0.25
with_fx :level, amp: 1 do |sc_power|   # サイドチェイン: power
  live_loop :pump_power do grid_each(sc_pat) { |i, len, lvl, c| grid_pump_hit sc_power, sc_depth, sc_rel } end
with_fx :reverb, room: 0.5, mix: 0.2 do
  with_fx :lpf, cutoff: 100 do
    with_fx :distortion, distort: 0.6, mix: 1.0, amp: 0.6 do   # distort は歪みの量（0〜1）。歪みで大きくなるので amp: 0.6 で戻す
      live_loop :power do
        grid_gate(:power, 1) do |sec, rts|
          use_synth :dsaw
          grid_each(pc_pat) do |i, len, lvl, c|
            r = rts[0] + 24   # ペダルポイント: 根音 Eb に固定（和音が Cb・Ab・Bb に動いても動かさない）
            # X（長く 0.5 拍）か x（短く 0.12 拍）か。lvl は X=1.0 / x=0.75
            sus = lvl >= 1.0 ? 0.5 : 0.12
            play [r, r + 7, r + 12], amp: pc_amp * lvl, attack: 0.01, sustain: sus, release: 0.1, cutoff: 85, detune: 0.1
          end
        end
      end
    end
  end
end
end

# ============ 上モノ（和音と高音）============
# 和音のスタブ（supersaw）。lpf 100 の下に置く
with_fx :level, amp: 1 do |sc_chords|   # サイドチェイン: chords
  live_loop :pump_chords do grid_each(sc_pat) { |i, len, lvl, c| grid_pump_hit sc_chords, sc_depth, sc_rel } end
with_fx :lpf, cutoff: 100 do
  live_loop :stabs do grid_gate(:stabs, 4) { |sec, rts| grid_play stab, c_pat, on: grid_song_chords(sec), chord: true } end
  live_loop :dom7 do grid_gate(:dom7, 4) { |sec, rts| grid_play stab, d_pat, on: dom_p, chord: true } end
  # glitch だけディストーション: distort 0.5（量 0〜1）。短い刻みがざらつく。歪みで大きくなるので amp: 0.6 で戻す
  with_fx :distortion, distort: 0.5, mix: 1.0, amp: 0.6 do
    live_loop :glitch do grid_gate(:glitch, 4) { |sec, rts| grid_play glitch, g_pat, on: grid_song_chords(sec), chord: true } end
  end
end
end

# --- 1オクターブ上のピアノ（リフに重ねる）---
# 低音ピアノのリフと同じ音を、同じリズム（lo_pat）で 1オクターブ上（+12 半音。ベースの根音から数えて +24）に重ねる。音色もベロシティも低音ピアノと同じ
piano_up_amp = 0.2
with_fx :level, amp: 1 do |sc_pianoup|   # サイドチェイン: pianoup
  live_loop :pump_pianoup do grid_each(sc_pat) { |i, len, lvl, c| grid_pump_hit sc_pianoup, sc_depth, sc_rel } end
with_fx :reverb, room: 0.9, mix: 0.5, damp: 0.5 do
    live_loop :piano_up do
      grid_gate(:piano_up, 4) do |sec, rts, bar|
        use_synth :piano
        ph = (grid_song_rel(bar) / 4) % 4   # 16小節ループのどのフレーズか
        offs = riff_offs[ph]
        k = 0
        grid_each(riff_pats[ph]) do |i, len, lvl, c|
          time_warp grid_tame(i, lvl, 0.1) do
            play rts[(i / 16) % 4] + 24 + offs[k], amp: piano_up_amp * lvl, hard: 0.25, vel: 0.25, sustain: [len * 0.25 - 0.1, 0.1].max, release: 0.3
          end
          k += 1
        end
      end
    end
end
end

# --- カウンターメロディ（パッドのように伸びる音なので、曲からは外した。grid_song_top に :counter を足せば戻る）---
# カウンターメロディ: 高い長い音(ロングトーン)。1小節に1音、14マス伸ばして最後の2マスで息継ぎ。コードトーンの Gb5(Ebm の短3度、Cbmaj7 の5度、Abm7 の7度)を保ち、最後の小節だけ F5 に半音下がる
# 1小節ごとのリズム（grid_dotted: 正=音のマス数, 負=休み）。4小節
cm_len_bars = [[14, -2]] * 4
cm_len_bars = cm_len_bars.cycle.first(4) if cm_len_bars.size < 4
cm_pat   = cm_len_bars.map { |l| grid_dotted(l) }.join(" | ")
cm_notes = %i[gb5 gb5 gb5 f5]
cm_acc   = [0.8]*4
raise "cm: 音の数（#{cm_notes.size}）と acc（#{cm_acc.size}）が違う" if cm_notes.size != cm_acc.size
raise "cm: 音の数（#{cm_notes.size}）がパターンの音の数（#{cm_pat.count("X")}）と違う" if cm_notes.size != cm_pat.count("X")
with_fx :reverb, room: 0.7, mix: 0.3 do   # メロディと同じ設定のリバーブ
with_fx :lpf, cutoff: 100 do
  live_loop :counter do
    grid_gate(:counter, 4) do |sec, rts|
      use_synth :blade
      k = 0
      grid_each(cm_pat) do |i, len, lvl, c|
        play cm_notes[k], amp: 0.3 * cm_acc[k], attack: 0.03, sustain: [len * 0.25 - 0.13, 0.03].max, release: 0.1, cutoff: 90
        k += 1
      end
    end
  end
end
end
end

# リバースキック: キックを逆再生（rate: -1）して、2小節目と4小節目の終わり（小節線の直前）に重ねる。逆再生の長さ d 拍ぶん前から鳴らし始め、小節線ちょうどで終わる
#   ループは 2小節（8拍）周期。sample_duration は拍で返る
with_fx :lpf, cutoff: 100 do
  live_loop :kick_rev do
    grid_gate(:kick_rev, 2) do |sec, rts|
      d = sample_duration(:bd_808, rate: 1)
      sleep 8 - d
      sample :bd_808, rate: -1, amp: 1.0, attack: 0.0, release: 0.05
      sleep d
    end
  end
end

