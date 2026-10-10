# sonicpi-live-agent

[Sonic Pi](https://sonic-pi.net) でライブコーディングして曲を作る人を支援する **AI エージェント用リポジトリ**です。
ユーザーがプロジェクトを始めてコードを書き、エージェントが

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
scripts/new_session.sh                                   # projects/<日付-連番>/ を作成
# Sonic Pi のコードを projects/<song>/current.rb に保存し、エージェントに伝える(/new-song)
uv run scripts/live_check.py projects/<song>/current.rb  # 名前・sleep の簡易検査
uv run scripts/live_render.py <song> current.rb --seconds 16   # 実時間で録音(音が鳴ります)
uv run scripts/wav_stats.py projects/<song>/renders/current_v1.wav
scripts/play.sh projects/<song>/renders/current_v1.wav   # 試聴
```

## 開発
`uv run ruff check .` / `uv run pytest` / `shellcheck scripts/*.sh`
