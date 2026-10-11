# 調声メモ(NEUTRINO をボコーダー向きに作り直す)

調声 = NEUTRINO が推定した中間ファイルを編集し、続きの段階だけ作り直すこと。
NEUTRINO は `timing`(音素の時刻)→ `f0`(音高、10ms 刻み float32)→ `melspec`(100bin の対数メル、10ms 刻み float32)→ `wav` の順に推定する。`--skip-timing/--skip-f0/--skip-melspec/--skip-wav` で編集済みの段階を飛ばせる。
**wav は作るたびに位相が変わる**ので、調声の最後に1回だけ作る(`neutrino_tune.py` はそうしている)。

## なぜボコーダー向けに調声するか
- ボコーダーは「声の形(包絡)」を鋸波キャリアに載せる。キャリアの音程は NEUTRINO の `f0` が決めるので、ビブラートやゆらぎがあると音程が不安定な機械声になる。
- 4kHz 以上が少ない(素の声は 0.4%)と、s・k・t などの子音が出ず歌詞が潰れる。
- 子音が長いと拍がもたつく。母音の頭を拍に置き、子音は短く手前に寄せる。

## `neutrino_tune.py` のパラメータ
| 指定 | 編集する段階 | 値の目安 | 効果 | 副作用 |
|---|---|---|---|---|
| `--pitch-lock` | f0 | 0.9(vocoder) / 1.0(robot) | 音高を譜面の音に寄せる強さ。1 でほぼ完全固定 | 大きいと人間味が消え、ケロケロ感が出る |
| `--glide-ms` | f0 | 40 / 15 | 音符の頭で元の滑らかな入りを残す長さ | 短いと音程が階段状になる |
| `--smooth` | f0 | 3 / 1 | f0 の移動平均(フレーム数) | 大きいと音符の頭が鈍る |
| `--consonant-scale` | timing | 0.7 / 0.6 | 子音の長さの倍率(母音の頭は動かない) | 小さいと子音が聞こえない |
| `--hf-boost` | melspec | 0.5 / 0.6 | 約 5kHz 以上を持ち上げる(対数値) | 大きいとシャリつく・ノイジー |
| `--cons-boost` | melspec | 0.6 / 0.8 | 子音区間の約 2kHz 以上を持ち上げる | 同上 |
| `--model` | (推定時) | MERROW 他 | 声質。作成時と同じモデルを渡す | |

`--preset vocoder` は自然さを少し残す設定、`--preset robot` はほぼ完全な固定(ロボット声)。まず vocoder で作り、足りなければ1つだけ動かす。

## 結果の読み方(エージェントは聴けない)
`neutrino_tune.py` が出す2つの数値で判断する。
- **譜面の音高からのずれ(セント)**: 素の声 約 70 → vocoder で 約 15。0 に近いほど機械的。100 セント = 半音。
- **4kHz 以上の比**: 0.4% → 数%。10% を超えるとシャリつく可能性が高い(聴いて確かめる)。
- ボコーダー後は `wav_stats.py` で帯域比とピークを見る(目安: ピーク -2dBFS 前後、4kHz 以上 3〜8%)。
聴いて確かめる箇所: 子音の立ち上がり(ka・ta の頭)/ 長い母音の音程の安定 / 高域のシャリつき。

## 手順(1フレーズ)
```
uv run scripts/neutrino_sing.py work/vocals/NN_x.json
uv run scripts/neutrino_tune.py work/vocals/NN_x_v1 --preset vocoder
uv run scripts/vocode.py work/vocals/NN_x_tuned_v1.wav work/vocals/NN_x_tuned_v1.f0 --bpm 130
```
利用許諾: 出力(wav・f0・melspec)を AI・機械学習による音声変換・合成の入力や学習データにしない。DSP のボコーダー(`vocode.py`)は対象外。
