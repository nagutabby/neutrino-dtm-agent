# sonicpi-live-agent

[Sonic Pi](https://sonic-pi.net) でライブコーディングして曲を作る人を支援する **AI エージェント用リポジトリ**です。
ユーザーがコードを書き、エージェントが

1. **現在の音を改善**する小さな案を出し、
2. **次の音(ステム)**をコードで提示し、
3. 最後に**全体レビュー**する

という流れで、「なぜそう聞こえるか」を理論と数値で学べます。決めるのは常にユーザーです。

- エージェント向けルール: [AGENTS.md](AGENTS.md)(`CLAUDE.md` から参照)
- 技法メモ: [docs/live-coding.md](docs/live-coding.md) / [docs/music-theory.md](docs/music-theory.md) / [docs/workflow.md](docs/workflow.md)

## セットアップ
```sh
brew install uv ffmpeg mpv ruby
brew install --cask sonic-pi
uv sync
scripts/setup.sh        # 不足の確認
```

## 使い方
```sh
# Sonic Pi のコードを work/current.rb に保存し、エージェントに伝える
uv run scripts/live_check.py work/current.rb             # 名前・sleep の簡易検査
uv run scripts/live_render.py current.rb --seconds 16    # 実時間で録音(音が鳴ります)
uv run scripts/wav_stats.py work/renders/current_v1.wav
scripts/play.sh work/renders/current_v1.wav              # 試聴
```

## 開発
`uv run ruff check .` / `uv run pytest` / `shellcheck scripts/*.sh`

## ライセンス
| 対象 | ライセンス |
|---|---|
| コード(`scripts/`、`songs/*.rb`、ドキュメントなど) | MIT([LICENSE-MIT](LICENSE-MIT)) |
| 曲の録音(`songs/*.mp3`) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)(条文: [LICENSE-CC-BY-4.0](LICENSE-CC-BY-4.0)) |

- mp3 を使うときのクレジット表記の例: 「Dark Kawaii Future Bass (songs/73_section_v1.mp3) by nagutabby, CC BY 4.0」
- 曲の音は、Sonic Pi の内蔵シンセ・FX と、同梱のサンプル(CC0)で鳴らしています。
- 曲の声(ボコーダー)は、歌声合成 [NEUTRINO](https://studio-neutrino.com)(MERROW モデル)で作った歌声を、DSP のボコーダーで処理したものです。声の部分には **NEUTRINO の利用許諾の条件が別に適用されます**。たとえば、声だけを取り出した素材やサンプルライブラリ・音源としての利用、AI・機械学習の学習データや変換元としての利用は、許諾されていません。
- 声の素材(wav・f0・melspec)はリポジトリに含まれません(`.gitignore` で除外)。曲のコード(`songs/*.rb`)の中の声のパスは、作者の環境のものです。
