# 3/4 拍子のデモ(grid_meter 3)。1小節 = 12マス。付点8分(3マス)でコードを刻む。BPM100 / Fマイナー。
# 先頭に docs/live-grid.rb の define 部分を貼って使う。拍子と解像度は 1曲で1つ(use_bpm の次に書く)。
# 6/8 は grid_res 2 + grid_meter 3(8分音符6つ)、4/4 の3連符は grid_res 3 + grid_meter 4(12マス)。
use_bpm 100
grid_meter 3

kick  = "x... .... ...."                                                 # 1拍目
hat   = ".... x... x..."                                                 # 2・3拍目
stab  = "x--x --x- ---- | x--x --x- ---- | x--x --x- ---- | x--x --x- ---x"  # 付点8分 x 付点8分 x 8分。4小節

kick_v = grid_voice :sample, :bd_haus, amp: 1.4
hat_v  = grid_voice :sample, :drum_cymbal_closed, amp: 0.6
pad_v  = grid_voice :synth, :supersaw, cutoff: 100, release: 0.3, amp: 0.6

waltz_p = grid_prog [:f3, :minor7], [:db3, :major7], [:ab2, :major7], [:eb3, :major7]

live_loop :kick do
  grid_play kick_v, kick
end

live_loop :hat do
  grid_play hat_v, hat
end

live_loop :chords do
  grid_play pad_v, stab, on: waltz_p, chord: true
end
