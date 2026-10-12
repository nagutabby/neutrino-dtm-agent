# グリッド記法のデモ(4小節ループ。BPM150 / Fマイナー)。先頭に docs/live-grid.rb の define 部分を貼って使う。
# 規約: docs/coding-rules.md / 検証: uv run scripts/check_grid.py examples/grid_demo.rb
use_bpm 150

# --- リズム(いつ鳴らすか)---
four    = "x... x... x... x..."          # 1小節
offbeat = ".... ..x. .... ..x. | .... ..x. .... ..x. | .... ..x. .... ..x. | .... ..x. .... ..x."   # 4小節
stab    = "x--x --x- ---x --x- | x--x --x- ---x --x- | x--x --x- ---x --x- | x--x --x- ---x ----"  # 4小節
chop_a  = "x--- x--- X--- x-o-"          # 1小節。音は5つ(x x X x o)

# --- 音(何を鳴らすか)---
kick = grid_voice :sample, :bd_haus, amp: 1.5
bass = grid_voice :synth, :subpulse, attack: :instant, release: :mid, amp: 1.0
pad  = grid_voice :synth, :supersaw, cutoff: 100, env: :stab, amp: 0.6          # 急に立ち上がって短く切る(Future Bass のシンセ)

# --- 進行(1小節に1コード)---
verse_p = grid_prog [:f3, :minor7], [:db3, :major7], [:ab2, :major7], [:eb3, :major7]

# --- 元の wav(デモは内蔵の loop_amen を4拍として使う。自分の声は work/vocals/ の wav と拍数を渡す)---
vox = grid_clip :loop_amen, 4

# 進行は4小節ぶん。ベースとコードは4小節(64マス)を1回で書き、1小節ごとに進行が進む
live_loop :kick do
  grid_play kick, four
end

live_loop :bass do
  grid_play bass, offbeat, on: verse_p
end

live_loop :chords do
  grid_play pad, stab, on: verse_p, chord: true
end

live_loop :vocal do
  grid_chop vox, chop_a, from: [0, 1, 0.5, 3, 2]
end
