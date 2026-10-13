# 録音からメロディを作る(`record_mic.py` → `melody_from_audio.py`)

ハミング・口笛・単音の楽器を録音し、曲のキーに合わせた `[拍の位置, 音名, 長さ]` のメロディ(`live_loop` つき)にする。
対象は **ユーザー自身の録音**(他人の曲の旋律を起こさない)。単音のみで、和音・伴奏つきの録音は誤検出する。

## 手順
```
uv run scripts/record_mic.py                       # Enter で開始 → Enter で停止 → work/recordings/rec_vN.mp3
uv run scripts/melody_from_audio.py work/recordings/rec_v1.mp3 --key "F minor" --bpm 100
uv run scripts/live_check.py work/proposals/rec_v1_melody.rb
```
- 初回はターミナルにマイクの許可が要る(システム設定 → プライバシーとセキュリティ → マイク)。入力デバイスは `record_mic.py --list-devices`。
- `--bpm` を省くと `work/current.rb` の `use_bpm` を読む。キーは `current.rb` から読めないので必ず指定する(音階は `--list-scales`)。
- 最初の音が `--start-beat`(既定 0)の位置になる。出力は `current.rb` に重ねて鳴らせる(`use_bpm` は `current.rb` 側)。
- 録音中に Sonic Pi を鳴らすなら **イヤホン**で(音がマイクに入ると誤検出する)。

## キックで拍を示して録る(おすすめ)
```
uv run scripts/record_mic.py --bpm 100            # スピーカーからキックが鳴る(4拍数える)
uv run scripts/melody_from_audio.py work/recordings/rec_v6.mp3 --key "F minor"   # BPM・キックは rec_v6.json から
```
- Enter で録音開始と同時にキックが拍ごとに鳴る。**最初の4拍(`--count-in` 小節)は数えるだけ**で、次の拍から歌う。
- キックは **スピーカーから**鳴らして録音に入れる(イヤホンだと入らない。その場合は警告が出て、最初の音を拍 0 にする従来の動き)。
- 変換側は、録音に入ったキックの立ち上がりから拍の位置を求め(確かさが 3 未満なら不採用)、カウントのあとを拍 0 にする。
  歌い出しが少し早い・遅いときも、拍に合わせて丸められる。130Hz 以下を削る(`--kick-hp`)ので、キックの低音が音程に混ざりにくい。
- `--no-kick` で、キックの処理を使わない。声が低くて 130Hz 以下に音がある場合は、`--kick-hp 100` などに下げる。
- 限界: スピーカーの音量が大きいと、キックの倍音が声と重なる。音量は小さめに、マイクは口に近く。

## 何をしているか
YIN で11.6msごとの基本周波数 → 全体の音程ずれ(セント)を補正 → 半音単位で音符に区切る → 音符ごとの中央値を
キーの音階の最も近い音へ寄せる(真ん中のときは低い方)→ 1/4拍(16分)に量子化 → 音域(既定 C4〜C6)に収まるオクターブへ。
ログ(標準エラー)の「もともとキー内だったフレーム」が低いほど、寄せた量が多い。

## 調整
| 症状 | 直し方 |
|---|---|
| 音が細かく割れる / 短い音が多い | `--min-note 0.15` |
| 速い音が消える | `--min-note 0.06` |
| オクターブが違う | `--octave 1` / `-1`、または `--low` `--high` |
| 3連符 | `--grid 3` |
| ずれた位置から始まる | `--start-beat` |
| 音程ずれの補正が邪魔 | `--no-tune-fix` |

## 動作確認(お題)
お題は `docs/melody-exercise.rb`(F マイナー / BPM 100。伴奏はクリックとベースだけ)。

1. Sonic Pi で `docs/melody-exercise.rb` を鳴らす(`# お手本` の部分はコメントのまま)。
2. 別のターミナルで `uv run scripts/record_mic.py`(キックなら `--bpm 100`)→ Enter → クリックを4回数えて、**お題「F F Ab C / Bb Ab G F」を「ら〜」と1音1拍で歌う** → Enter。
3. `uv run scripts/melody_from_audio.py work/recordings/rec_v1.mp3 --key "F minor" --bpm 100`
4. 期待する出力: 音符 8 個前後、ループ 8 拍(2 小節)、`:f4 :f4 :ab4 :c5 :bb4 :ab4 :g4 :f4`(オクターブ違いは可)。
5. 聴いて確かめる: 出力 `.rb` を `current.rb` の後ろに足して鳴らし、お手本(`answer`)と聴き比べる。音符数・音の高さ・長さが合っているか。
6. 発展: 同じお題を **わざとキーを外して**(Ab を A 寄りに)歌い、`F minor` に寄ることを確認する。`--key "F major"` に変えると A のまま残るかを比べる。
   録音なしの確認は `uv run pytest tests/test_melody_from_audio.py`(合成音で検出と量子化を検査)。

## 限界
- 歌が揺れたり息継ぎで音が割れたりする。聴いて、直す(コードの数字を手で直す)前提。
- 隣り合う音階音の真ん中に当たる音は、どちらに寄るか不安定(低い方)。
- 長さは1/4拍刻みで丸めるので、細かい揺れは消える。
