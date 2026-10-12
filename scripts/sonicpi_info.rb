# Sonic Pi 内蔵の音の一覧を JSON で標準出力に出す(config/sonicpi_catalog.json の元)。音は出さない。
#   ruby scripts/sonicpi_info.rb > config/sonicpi_catalog.json    (`sonicpi.py dump-info` から呼ぶ)
# 中身: synths / fx(名前 → 引数の一覧。synthinfo.rb)、samples(グループ → 名前の一覧)、chords・scales(名前の一覧)
require "json"
root = ENV["SONIC_PI_APP"] || "/Applications/Sonic Pi.app"
ruby_dir = File.join(root, "Contents/Resources/app/server/ruby")
$LOAD_PATH.unshift File.join(ruby_dir, "lib")
$LOAD_PATH.unshift ruby_dir
require "sonicpi/synths/synthinfo"
require "sonicpi/chord"
require "sonicpi/scale"

si = SonicPi::Synths::SynthInfo
dump = lambda do |names, prefix = ""|
  names.sort_by(&:to_s).to_h do |n|
    [n.to_s, si.get_info(:"#{prefix}#{n}").arg_defaults.keys.map(&:to_s)]
  end
end
samples = Dir.children(File.join(root, "Contents/Resources/etc/samples"))
             .select { |f| f =~ /\.(flac|wav|aiff?|ogg)\z/i }
             .map { |f| File.basename(f, ".*") }.sort
puts JSON.pretty_generate(
  "version" => File.read(File.join(root, "Contents/Resources/VERSION")).strip,
  "synths" => dump.call(si.all_synths),
  "fx" => dump.call(si.all_fx, "fx_"),
  "samples" => samples.group_by { |n| n.split("_").first }.sort.to_h,
  "chords" => SonicPi::Chord::CHORD_NAMES.map(&:to_s).sort,
  "scales" => SonicPi::Scale::SCALE.keys.map(&:to_s).sort
) rescue (warn "取得に失敗: #{$!}"; exit 1)
