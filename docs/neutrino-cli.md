# NEUTRINO CLI メモ(同梱 Run.sh より)

macOS arm64。`NEUTRINO_DIR`(既定 `~/NEUTRINO`)は**読み取り専用**として扱う。

```
DYLD_LIBRARY_PATH=$NEUTRINO_DIR/bin
bin/musicXMLtoLabel <in.musicxml> <full.lab> <mono.lab>
bin/neutrino <full.lab> <timing.lab> <out.f0> <out.melspec> <out.wav> <model_dir>/ \
    -n <threads> -k <styleShift> -f <transpose> -s <samplingRate> -b <bitDepth> -t
```
- 既定(Run.sh): `-n 4 -k 0 -f 0 -s 48000 -b 16`、モデル `MERROW`
- 利用可能モデル: MERROW / NAKUMO / REINA / RUNO / SOMA(`model/<name>/`)
- フレーズ単位: `-i <phraselist.txt> -p <番号>`(Run_single_phrase.sh)
- 入力は **MusicXML のみ**。MIDI は MuseScore で変換する。

## 本リポジトリの対応
- `scripts/synth.sh <song> <basename> [model]` が上記2段を実行(Run.sh と同じ既定、出力は `projects/<song>/output/`)
- 環境変数 `STYLE_SHIFT` `TRANSPOSE` `NUM_THREADS` `SAMPLING_RATE` `BIT_DEPTH` で上書き
- Run.sh は `xattr`/`chmod` を行うが、本リポジトリのスクリプトは本体を変更しない。初回に実行権限エラーが出たらユーザーに報告し、対処(`chmod`/quarantine 解除)をユーザーに実行してもらう
