# Sonic Pi 内蔵シンセ・FX の名前と引数を JSON で標準出力に出す(config/sonicpi_synths.json の元)。
#   ruby scripts/sonicpi_info.rb > config/sonicpi_synths.json    (`sonicpi.py dump-info` から呼ぶ)
# Sonic Pi.app の synthinfo.rb を読むだけで、音は出さない。
require "json"
root = ENV["SONIC_PI_APP"] || "/Applications/Sonic Pi.app"
ruby_dir = File.join(root, "Contents/Resources/app/server/ruby")
$LOAD_PATH.unshift File.join(ruby_dir, "lib")
$LOAD_PATH.unshift ruby_dir
require "sonicpi/synths/synthinfo"

si = SonicPi::Synths::SynthInfo
dump = lambda do |names, prefix = ""|
  names.sort_by(&:to_s).to_h do |n|
    [n.to_s, si.get_info(:"#{prefix}#{n}").arg_defaults.keys.map(&:to_s)]
  end
end
puts JSON.pretty_generate(
  "version" => File.read(File.join(root, "Contents/Resources/VERSION")).strip,
  "synths" => dump.call(si.all_synths),
  "fx" => dump.call(si.all_fx, "fx_")
) rescue (warn "取得に失敗: #{$!}"; exit 1)
