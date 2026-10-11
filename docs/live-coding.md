# Sonic Pi ライブコーディング技法メモ(提案の根拠にする辞書)

数値の目安は出発点。最後は耳で決める(エージェントは聴けない)。

| 目的 | 技法 | 例・目安 |
|---|---|---|
| 同時に鳴らす | `live_loop :名前 do … end`(各ループに必ず `sleep`) | 1ループ = 1ステム |
| 展開をつける | `ring` / `tick` / `choose` / `one_in(n)` / `if` / `spread(k, n)` | `spread(3, 8)` でユーロ風の跳ねたパターン |
| 変化を数小節ごとに | `tick` の周期をずらす、`(ring …).look` | ループ長の違う2つを重ねる(4拍と6拍)と飽きにくい |
| 音量の抑揚 | `amp:` をパターンで変える / `rrand` で揺らす | 表拍 1.0・裏拍 0.6、揺らし ±0.1 |
| 音色を動かす | `cutoff:` を `line` / `range` で変化、`res:` を足す | `cutoff: rrand(70,110)`(note 値)、`res` 0.1〜0.4 |
| 空間 | `with_fx :reverb, room: 0.6, mix: 0.3` / `:echo` / `pan:` | 低域は中央、高域ほど左右に振る |
| 低域の整理 | ベースは `use_synth :fm` / `:tb303` で C1〜C3、`:hpf` で他ステムの 100Hz 以下を削る | ベースとキックは同じ拍で揃えるとタイト |
| 同期 | `cue` / `sync`、`use_bpm` | 全ステムで `use_bpm` を 1 箇所に |
| 拍の位置 | キック 1・3、スネア 2・4(バックビート)、ハイハット 8分 | 裏拍に置くとノリ(シンコペーション) |
| 人間味 | `sleep` を `0.25 + rrand(-0.01, 0.01)`、`amp` の揺らし | 揺らしすぎるとよれる |
| 音域の住み分け | ベース C1〜C3 / コード C3〜C5 / メロ C4〜C6 | `note` は MIDI 番号(60 = C4) |
| ボーカル風(ボコーダー) | saw を母音のフォルマント(F1/F2/F3)の `bpf` 3つに通す。子音は短い `noise`/`pnoise`。`docs/vocal-helper.rb` の `vsing` | `res` 0.85、`amp` 比 1 : 0.6 : 0.3。`ring_mod` mix 0.2〜0.4 で機械っぽさ、`reverb` mix 0.3 |

確認: `uv run scripts/sonicpi.py synths [名前]` / `fx [名前]` で内蔵シンセ・FX の引数。`uv run scripts/live_check.py <file.rb>` で名前の検査。
