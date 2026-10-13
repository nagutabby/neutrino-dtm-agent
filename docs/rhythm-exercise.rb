# リズム録音→変換の動作確認用「お題」(BPM 100 / 4/4 / 1小節ループ)。一度の録音で取るのは1本(1ステム)だけ。
# 使い方: 下の stem を選んで鳴らし、そのリズムを手拍子・机・口(「ドン」など)で叩いて録音する(手順は docs/melody-from-audio.md)。
#   record_mic.py --bpm 100 --count-only で録る → 数えのキック4拍のあと、次の拍から叩く。1小節を2〜4回くり返す。
#   rhythm_from_audio.py <mp3> --stem <選んだ stem> で変換する。ステムごとに別の録音にする。
#
# お題(16マス = 1小節。1マス = 16分音符。拍ごとに空白で区切って読む。x = ふつう):
#   :kick   x... .... x... ....   1拍目と3拍目(まずはこれ)
#   :snare  .... x... .... x...   2拍目と4拍目
#   :hat    ..x. ..x. ..x. ..x.   各拍のうら(8分音符のうら拍)
#   :synco  x... ..x. x... ..x.   1拍目・2拍目のうら・3拍目・4拍目のうら(跳ねるリズム)
# 期待する変換結果は、選んだお題と同じ形(強さ X / x / o は叩き方で変わる)。
use_bpm 100

stem = :kick  # ← :kick / :snare / :hat / :synco から選ぶ

patterns = {
  kick: "x... .... x... ....",
  snare: ".... x... .... x...",
  hat: "..x. ..x. ..x. ..x.",
  synco: "x... ..x. x... ..x."
}
samples = { kick: :bd_haus, snare: :sn_dub, hat: :drum_cymbal_closed, synco: :bd_haus }
target = patterns[stem].delete(" ").chars

live_loop :target do
  16.times do |i|
    sample samples[stem], amp: 1.5 if target[i] == "x"
    sleep 0.25
  end
end
