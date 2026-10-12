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
