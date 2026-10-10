# NEUTRINO 調声メモ(ボーカルあり曲の参照用)

Web 調査(2026-10-10)に基づく。公式マニュアルは `$NEUTRINO_DIR` 同梱の readme_NEUTRINO.pdf。歌詞入力前・歌詞レビュー・ボーカル合成の前後に参照する。数値は目安で、最終判断は聴いて行う(ユーザー)。

## 仕様上の制約
- 入力は MusicXML のみ。1音符1音節。1音符に2音は出せない。スラー・スタッカート・アクセントは効かない
- 歌詞はひらがな・カタカナのみ(英字不可)。全音符に歌詞が必要(空白はエラー)
- テンポは MusicXML に明記(未設定は BPM120)。生成のたび波形が変わるため、複数テイクから選べる
- 高速歌唱は BPM150〜160 の 16分音符程度まで確認例あり。出力の前後に 1 小節の休符が付くのは仕様

## 歌詞の書き方(読みの調整)
- 発音に近い表記にする(助詞「は」→「わ」、「へ」→「え」)
- 長音「ー」は直前の母音の繰り返し
- 二重母音(あい・えい)を1音符にまとめると滑らか、分割すると各音がはっきり出る
- 促音「っ」は直前母音に続く連続フレーズ。休符は別フレーズになる
- 母音脱落「'」で子音のみ発声(高速や英語風。例: ス'カ)。無声音の表現にも使える
- タイミングが合わない箇所は促音で伸ばす等、表記で調整する

## 楽譜の作り方
- カラオケ譜面・メロディ譜面のようにシンプルに。細かい休符は避け、フレーズ単位で音をつなげる
- 息継ぎは休符で入れる。BPM 変更は小節頭
- 高音でかすれる/不安定なら、音程を下げるかキー(`TRANSPOSE`)を見直す

## パラメータ(`scripts/synth.sh` の環境変数。docs/neutrino-cli.md)
- StyleShift(`STYLE_SHIFT`、-k): おおよそ -5〜+5 の整数。+N は N 半音上のキーの歌い方、-N は落ち着いた歌い方。得意な音域に寄せる、表情を変える用途。楽譜全体を N 上げて打ち込み、N 下げて出す処理に相当
- PitchShift(NSF 側): 周波数比。キー移調ではなく細かい音高調整
- FormantShift: 1.0 が標準。上げると子供っぽく、下げると大人っぽい声。目安 0.85〜1.15
- モデル(MERROW / NAKUMO / REINA / RUNO / SOMA)で声質が違う。曲に合うものを聴き比べる

## 調声ツール(ずー声などの GUI。Windows 中心)の工程
基盤から仕上げの順に行い、各調整後に再実行して確認する。
1. SCORE: 音符の位置・長さ
2. 歌詞とタイミング(TIMING): 子音と母音の分離など。「タイミング保持」にして再実行
3. PITCH: 音程補正・ビブラートの描画
4. DYNAMICS: 音量

本リポジトリは CLI のみ。ツールで直す場合は手順だけ示し、ユーザーに実行してもらう。タイミング label(`label/`)の手動編集は上級者向け。

## 本リポジトリでの運用
- 歌詞も旋律もユーザーが先に書く。AI の改善案は最大 2 つ、ユーザーの歌詞は改変しない
- 直す順: 歌詞表記 → 音符の長さ・休符・音域 → StyleShift/モデル/FormantShift → 調声ツールの手順案内
- 解析は MIDI/MusicXML のみ(出力音声・label を他の AI に渡さない。docs/licensing.md)

## 出典
- [NEUTRINOで上手に歌わせるコツ(Classmethod)](https://dev.classmethod.jp/articles/tutorial-about-neutrino-neural-singing-synthesizer/)
- [NEUTRINO FAQ(公式)](https://studio-neutrino.com/faq/)
- [歌AI「NEUTRINO」と調声ツールのシンプルな使い方](https://ossan-gamer.net/post-82050/)
- [NEUTRINOのStyleShiftとPitchShiftを使う](https://scrapbox.io/music-tech-box/NEUTRINO%E3%81%AEStyleShift%E3%81%A8PitchShift%E3%82%92%E4%BD%BF%E3%81%86)
- [Sleepfreaks NEUTRINO 解説](https://sleepfreaks-dtm.com/en/softsynth/neutrino)
- [StyleShift 公式告知](https://x.com/SHACHI_NEUTRINO/status/1281583942294859778)
