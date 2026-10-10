# Sonic Pi のコードをヘッドレスで実行し、鳴った音を wav に録音する(リアルタイム録音)。
#   ruby sonicpi_record.rb OUT.wav SECONDS CODE.rb
# 同梱の headless-record.rb は Sonic Pi 5.0.0 ではエンジンが TCP になっていて動かないため、
# Sonic Pi 自身の recording_start / recording_save を使う。音は実際に再生されながら録音される。
require "fileutils"

root = ENV["SONIC_PI_APP"] || "/Applications/Sonic Pi.app"
require File.join(root, "Contents/Resources/app/server/ruby/bin/headless_boot")

out, dur, file = ARGV[0], ARGV[1].to_f, ARGV[2]
abort "使い方: sonicpi_record.rb OUT.wav SECONDS CODE.rb" unless out && dur > 0 && file && File.file?(file)
out = File.expand_path(out)
FileUtils.mkdir_p(File.dirname(out))
FileUtils.rm_f(out)

boot = SonicPi::HeadlessBoot.new.boot!
code = [
  "set_sched_ahead_time! 0", # 録音の頭と音の頭を揃える(既定の 0.5 秒先行だと音が遅れる)
  "recording_start",
  File.read(file),
  "sleep #{dur}",
  "recording_stop",
  "sleep 0.5",
  "recording_save #{out.inspect}",
  "sleep 2.0"
].join("\n")
boot.run(code)
sleep dur + 8
boot.stop_all
sleep 1
boot.say "ERRORS: #{boot.errors.join(' | ')}" unless boot.errors.empty?
ok = File.exist?(out) && File.size(out) > 1000
boot.say(ok ? "WROTE #{out}" : "FAILED — no output written")
$stdout.flush

# 起動した daemon とエンジン(自分の子孫プロセス)だけを止める。他の Sonic Pi は触らない
def descendants(pid)
  kids = `pgrep -P #{pid}`.split.map(&:to_i)
  kids + kids.flat_map { |k| descendants(k) }
end
descendants(Process.pid).each { |k| Process.kill("TERM", k) rescue nil }
exit!(ok && boot.errors.empty? ? 0 : (ok ? 2 : 1))
