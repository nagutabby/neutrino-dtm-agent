# CLI で使える MIDI ソフト候補

| 候補 | 種別 | 安定性/所感 | 本リポジトリでの使い方 |
|---|---|---|---|
| **mido**(Python) | ライブラリ | 長年の定番、API 安定、イベントレベル | 検査・生成・解析(**採用**) |
| **MuseScore 4 CLI** | 楽譜 | 安定。MIDI↔MusicXML 変換 | MIDI→MusicXML(**採用**。要インストール) |
| pretty_midi / symusic | ライブラリ | ノートレベルで解析しやすい。symusic は C++ 実装で高速 | 大量解析が必要になれば検討 |
| midicsv / csvmidi | CLI | 小さく枯れている。Homebrew で入手可 | 差分確認・手編集(任意) |
| **FluidSynth** | CLI | 非常に安定。Homebrew `fluid-synth` | 試聴用レンダリング(**採用**) |
| midish | CLI シーケンサ | 枯れているが macOS/Homebrew での入手性は未確認 | 対話的編集(任意・未検証) |

導入: `brew install fluid-synth ffmpeg mpv midicsv shellcheck`、`brew install --cask musescore`(後者は未導入。インストールはユーザー確認の上で)。
