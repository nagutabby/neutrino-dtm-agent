# シンセ合成(SuperCollider)

**音は曲ごとの専用で、SuperCollider でゼロから作る**(SoundFont・外部音源は使わない。例外はユーザーが用意した wav)。MIDI は「いつ・どの高さで・どの強さで」、パッチは「どんな音色で」。

## 曲専用の音色(既存の音源を再利用しない)
- 置き場は曲の中だけ: `projects/<song>/synth/synthdefs.scd`(SynthDef)と `projects/<song>/synth/patches.yaml`(登録簿)。`new_song.sh` が**空の雛形**を置く。
- 作るのは**ユーザーが最初に指示した音だけ**(`projects/<song>/user_inputs.yaml` の `tracks[].sound`)。AI は音色を提案しない・既定を補わない。
- 他の曲の音色や、リポジトリ直下の `config/patches.yaml`・`synth/synthdefs.scd`(過去の音色集)は**読み込まれない**。コピーして流用もしない(書き方の構文の参考に見るのは可)。`patches.py check` は曲の登録簿にない ID をエラーにする。

## 流れ
`tracks/NN_<track>_vN.mid` → `scripts/synth_render.py`(spec の `patch` / `patch_params` を曲の登録簿で解決)→ `.scd`(ボイス列)→ `sclang` の `Score.recordNRT`(非リアルタイム)→ `stems/NN_<track>_vN.wav`
- 同じ MIDI・spec なら毎回同じ音(ノイズ系は乱数のため完全一致はしない)
- 導入: `brew install --cask supercollider`(標準外の場所なら `.env` の `SCLANG`)

## ユーザーが用意したサンプルを使う(音声サンプリング)
ユーザーが自分で用意した **PCM の WAV** だけを、`projects/<song>/samples/` に置いて鳴らせる(AI はサンプルを探さない・提案しない)。
1. `synthdefs.scd` に、引数 `buf` と `rate` を持つ再生用 SynthDef を書く(例: `PlayBuf.ar(1, buf, rate, doneAction: 2)` を `Pan2` で出力)。`buf` はレンダラが割り当てるので `patches.yaml` の `params` に書かない。
2. `patches.yaml` のパッチに `sample: samples/<file>.wav` を書く。音程を付けるなら `root_note: <MIDI ノート番号>`(元の音の高さ。ノートに合わせて `rate = 2^((note − root)/12)`)、付けない(ワンショット)なら省略(`rate=1`)。ドラムキットはピースごとに `sample` を書く。
3. サンプルは最後まで鳴る長さが自動で計上される。`patches.py check` が、`samples/` 外のパス・存在しないファイル・WAV でないもの・`buf`/`rate` の無い SynthDef をエラーにする。

## サウンドチェック(制作の前)
`uv run scripts/patch_audition.py <song>` が、ユーザーが指示した全トラックを固定フレーズで合成して `projects/<song>/audition/` に置く。全部聴いて音色を確認してから、構成・和声・MIDI の制作に入る(`--force` で作り直し)。

## 音色の決め方
- ユーザーの `sound` を元に、その曲の `patches.yaml` に登録する。確認は `uv run scripts/patches.py list <song>` / `show <song> <id>`。spec は `params.patch: my_bass`、微調整は `params.patch_params: {glide: 0.1}`
- ドラムは `patch_params: {kick: {tune: 45, decay: 0.6}}` のようにピース別。ノート番号の割り当てはその曲のキットの `pieces[].notes`(GM ドラム: 36 キック / 38 スネア / 42 閉ハット … に揃えると MIDI を作りやすい)
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

## パッチを足す(その曲の中で)
1. `projects/<song>/synth/synthdefs.scd` の配列に SynthDef を足す(引数に既定値。旋律は `freq amp pan gate`、ドラムは gate なしで固定長)
2. `projects/<song>/synth/patches.yaml` に同名の引数を `params` として登録
3. `uv run scripts/patches.py check <song>`(引数名の一致・サンプルの置き場を検査)
