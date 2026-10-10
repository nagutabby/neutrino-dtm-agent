# シンセ合成(SuperCollider)

**曲に使う音は必ず SuperCollider で作る**(サンプル・SoundFont・外部音源は使わない。足りない音色は SynthDef を足す。歌声のみ NEUTRINO)。伴奏の音は波形から作る(減算合成・FM・物理モデル・ノイズ)。MIDI は「いつ・どの高さで・どの強さで」、パッチは「どんな音色で」。

## 流れ
`tracks/NN_<track>_vN.mid` → `scripts/synth_render.py`(spec の `patch` / `patch_params` を解決)→ `.scd`(ボイス列)→ `sclang` の `Score.recordNRT`(非リアルタイム)→ `stems/NN_<track>_vN.wav`
- 同じ MIDI・spec なら毎回同じ音(ノイズ系は乱数のため完全一致はしない)
- 導入: `brew install --cask supercollider`(標準外の場所なら `.env` の `SCLANG`)

## サウンドチェック(制作の前)
`uv run scripts/patch_audition.py <song>` が、トラック計画の全トラックを固定フレーズで合成して `projects/<song>/audition/` に置く。全部聴いて音色を確認してから、構成・和声・MIDI の制作に入る(`--force` で作り直し)。

## 音色の決め方
- `uv run scripts/patches.py list` / `show <id>` で選ぶ。spec は `params.patch: sub808`、微調整は `params.patch_params: {glide: 0.1}`
- ドラムは `patch_params: {kick: {tune: 45, decay: 0.6}}` のようにピース別。ノート番号は GM ドラム(36 キック / 38 スネア / 39 クラップ / 42 閉ハット / 46 開ハット / 49 クラッシュ / 56 カウベル)
- ベロシティは音量(amp)に比例して掛かる。`mono` のパッチは音が続くと同じ音のまま音程だけ滑る(808 のグライド)

## 主な引数の効き方(技術解説に使う)
| 引数 | 意味 | 目安 |
|---|---|---|
| `cutoff`(Hz) | ローパスの周波数。下げるほど暗く丸い | 400〜800 暗い / 1500〜3000 標準 / 5000+ 明るい |
| `res` | カットオフ付近の強調(0〜1) | 0.2 標準 / 0.6+ でクセが強い |
| `atk` / `decay` / `sus` / `rel` | 立ち上がり / 減衰 / 保持量 / 余韻(ADSR) | atk 0.005 打楽器的 / 0.6+ パッド的 |
| `detune` | ノコギリ波のズレ(厚み) | 0.005 控えめ / 0.02 広い |
| `drive` | 歪み(tanh) | 1 ほぼ素 / 3 太い / 6+ 荒い |
| `glide`(秒) | 音程のスライド時間 | 0.03 速い / 0.15 ゆったり |
| `index` / `ratio`(FM) | 変調の深さ / 周波数比。整数比=楽音、非整数=金属的 | epiano: 1.0 / 1〜2 |
| `tune`(ドラム) | キックの最低音など基本の高さ(Hz) | キック 40〜60 |

## パッチを足す
1. `synth/synthdefs.scd` に SynthDef を足す(引数に既定値。旋律は `freq amp pan gate`、ドラムは gate なしで固定長)
2. `config/patches.yaml` に同名の引数を `params` として登録
3. `uv run pytest`(引数名の一致を `tests/test_synth.py` が検査)
