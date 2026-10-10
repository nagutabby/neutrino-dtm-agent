# シンセ合成(Sonic Pi)

**音は曲ごとの専用で、Sonic Pi の内蔵シンセでゼロから作る**(SoundFont・外部音源・Sonic Pi 同梱のサンプルは使わない。例外はユーザーが用意した wav)。MIDI は「いつ・どの高さで・どの強さで」、パッチは「どんな音色で」。

## 曲専用の音色(既存の音源を再利用しない)
- 置き場は曲の中だけ: `projects/<song>/synth/patches.yaml`(登録簿)。`new_song.sh` が**空の雛形**を置く。
- 作るのは**ユーザーが最初に指示した音だけ**(`projects/<song>/user_inputs.yaml` の `tracks[].sound`)。AI は音色を提案しない・既定を補わない。
- 他の曲の音色は読み込まれない・流用しない。`patches.py check` は曲の登録簿にない ID・Sonic Pi にないシンセ/FX/引数名をエラーにする。
- 内蔵シンセ・FX の一覧と引数: `uv run scripts/sonicpi.py synths [名前]` / `fx [名前]`(`config/sonicpi_synths.json`。Sonic Pi 更新後は `sonicpi.py dump-info` で作り直す)。

## 流れ
`tracks/NN_<track>_vN.mid` → `scripts/synth_render.py`(spec の `patch` / `patch_params` を曲の登録簿で解決)→ Sonic Pi の Ruby コード(ボイス列を `sleep` で並べ、`with_fx` で包む)→ ヘッドレスの Sonic Pi で実行しながら録音(`scripts/sonicpi_record.rb`)→ ffmpeg で 16bit/48kHz wav にして `stems/NN_<track>_vN.wav`
- **実時間レンダリング**: Sonic Pi にはゼロから wav を書く非リアルタイム書き出しがない。曲の長さ分(+起動・保存で十数秒)かかり、**録音中はスピーカーから音が鳴る**。同時に別のレンダリングを走らせない。
- 乱数は `use_random_seed 0` で固定(ノイズ系は同じ MIDI・spec ならほぼ同じ音)。録音の頭と音の頭は `set_sched_ahead_time! 0` で揃えている。
- 導入: `brew install --cask sonic-pi` と `ruby`(標準外の場所なら `.env` の `SONIC_PI_APP` / `SONIC_PI_RUBY`)。環境確認は `scripts/setup.sh`。
- テンポは Sonic Pi の既定 60 BPM(1 拍 = 1 秒)で、MIDI の秒数をそのまま `sleep` している。曲のテンポは MIDI 側の時間に入っている。

## パッチの書き方(`patches.yaml`)
```yaml
patches:
  my_bass:
    name: 名前
    kind: melodic            # melodic = ノートごとに音程 / drums = ノート番号でピースを切り替え
    synth: tb303             # Sonic Pi の内蔵シンセ名
    mono: true               # 任意。続く音は音程だけ滑る(滑る秒は params.note_slide、既定 0.08)
    params: {amp: 0.5, pan: 0, cutoff: 80, release: 0.2}   # そのシンセの引数(数値のみ)
    fx: [{name: reverb, params: {room: 0.7, mix: 0.3}}]    # 任意。外側から順にパッチ全体へ
  kit:
    kind: drums
    pieces:
      kick: {notes: [36], synth: sc808_bassdrum, params: {amp: 0.8, decay: 0.5}, sweep: {note: 30, time: 0.12}}
```
- 音量はベロシティに比例して `amp` に掛かる。`amp` / `pan` 以外の引数は `params` に書いた分だけ渡す(書かなければシンセの既定)。
- ノート長: 保持部(`sustain`)は MIDI のノート長 − `attack` − `decay` から決まり、`release` はそのあとに鳴る(SC 時代の gate と同じ感覚)。`oneshot: true` ならノート長に関わらず `params` の ADSR で固定長に鳴り切る。ドラムとサンプルは常にワンショット。
- `sweep`(drums のピース): 鳴らした直後に指定ノート番号まで `time` 秒で音程を滑らせる(キックのピッチ下降。`sc808_bassdrum` などで効く)。
- spec は `params.patch: my_bass`、微調整は `params.patch_params: {release: 0.1}`(ドラムはピース別 `{kick: {decay: 0.6}}`)。`patch_params` で書けるのは登録簿の `params` に既にある引数だけ。
- 確認は `uv run scripts/patches.py list <song>` / `show <song> <id>` / `check <song>`。

## ユーザーが用意したサンプルを使う(音声サンプリング)
ユーザーが自分で用意した **PCM の WAV** だけを、`projects/<song>/samples/` に置いて鳴らせる(AI はサンプルを探さない・提案しない。Sonic Pi 同梱の `:bd_haus` などは使わない)。
1. `patches.yaml` のパッチに `synth` の代わりに `sample: samples/<file>.wav` を書く。`params` は `sample` の引数(`amp pan attack release cutoff lpf hpf rate start finish …`)。
2. 音程を付けるなら `root_note: <MIDI ノート番号>`(元の音の高さ。ノートに合わせて `rate = 2^((note − root)/12)`)、付けない(ワンショット)なら省略(`params.rate` のまま)。ドラムキットはピースごとに `sample` を書く。
3. サンプルは最後まで鳴る長さが自動で計上される。`patches.py check` が、`samples/` 外のパス・存在しないファイル・WAV でないもの・`synth` との併記をエラーにする。

## サウンドチェック(制作の前)
`uv run scripts/patch_audition.py <song>` が、ユーザーが指示した全トラックを固定フレーズで合成して `projects/<song>/audition/` に置く(トラック数 × 十数秒かかる)。全部聴いて音色を確認してから、構成・和声・MIDI の制作に入る(`--force` で作り直し)。

## 主な引数の効き方(技術解説に使う。シンセごとに持つ引数が違うので `sonicpi.py synths <名前>` で確認)
| 引数 | 意味 | 目安 |
|---|---|---|
| `cutoff` | ローパスの周波数。**Hz ではなく MIDI ノート番号**(0〜130)。下げるほど暗く丸い | 50〜70 暗い / 80〜100 標準 / 110+ 明るい |
| `res` | カットオフ付近の強調(0〜1) | 0.2 標準 / 0.6+ でクセが強い |
| `attack` / `decay` / `sustain` / `release` | 立ち上がり / 減衰 / 保持 / 余韻(秒) | attack 0.005 打楽器的 / 0.6+ パッド的 |
| `detune` | 重ねた波形のズレ(厚み。`dsaw` `supersaw` `prophet` など) | 0.1〜0.2 控えめ / 0.5+ 広い |
| `depth` / `divisor` | FM の変調の深さ / 周波数比(`fm`) | 整数比=楽音、非整数=金属的 |
| `note_slide` | 音程のスライド時間(秒。mono のグライド) | 0.03 速い / 0.15 ゆったり |
| `lpf` / `hpf`(ドラム・サンプル) | ローパス / ハイパス(MIDI ノート番号) | ハイハットは hpf 100+ |
| FX `reverb` `mix` `room` | 残響の量 / 部屋の大きさ | mix 0.2〜0.4 / room 0.6〜0.9 |
| FX `distortion` `distort` / `krush` | 歪み / ビットクラッシュ風の荒れ | 0.3 軽い / 0.7+ 荒い |

## パッチを足す(その曲の中で)
1. `uv run scripts/sonicpi.py synths` で候補を見て、ユーザーの `sound` に合うシンセを選ぶ(選んだ理由と主な引数を一言で伝える)
2. `projects/<song>/synth/patches.yaml` に登録する
3. `uv run scripts/patches.py check <song>`(シンセ名・引数名・FX・サンプルの置き場を検査)→ `patch_audition.py` で試奏
