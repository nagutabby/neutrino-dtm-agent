# 録音→メロディ変換の動作確認用「お題」(F マイナー / BPM 100 / 2小節ループ)
# 使い方: 鳴らしながら、イヤホンで聴いて、下のお題を「ら〜」とハミングして録音する(手順は docs/melody-from-audio.md)。
# カチカチ(click)の4回を数え、次の1拍目から歌い始める。1音1拍。歌いやすい高さでよい(オクターブは自動で合わせる)。
#   お題(F マイナー): 小節1 = F F Ab C / 小節2 = Bb Ab G F
use_bpm 100

live_loop :click do
  sample :elec_tick, amp: 1.5
  sleep 1
end

live_loop :bass do
  use_synth :fm
  play :f2, release: 1.6, amp: 0.8
  sleep 2
  play :db2, release: 1.6, amp: 0.8
  sleep 2
end

# お手本(答え合わせ用)。録音前は #をつけて止め、変換後に外して聴き比べる
# live_loop :answer do
#   use_synth :saw
#   [[0, :f4, 1], [1, :f4, 1], [2, :ab4, 1], [3, :c5, 1],
#    [4, :bb4, 1], [5, :ab4, 1], [6, :g4, 1], [7, :f4, 1]].each do |pos, n, len|
#     time_warp pos do
#       play n, amp: 0.7, release: len * 0.9, cutoff: 100
#     end
#   end
#   sleep 8
# end
