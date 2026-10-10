# neutrino-dtm-agent

[NEUTRINO](https://studio-neutrino.com)(AI 歌声合成)で DTM を行う**初心者の学習を支援する AI エージェント用リポジトリ**です。
AI が曲を作り切るのではなく、**スペック駆動**で「決める(ユーザー)→作る(AI)→聴く→気になる点を spec に反映→作り直す」を繰り返し、
トラックを1本ずつ重ねながら「なぜそう聞こえるか」を学びます。

- エージェント向けルール: [AGENTS.md](AGENTS.md)(`CLAUDE.md` から参照)
- 進め方: [docs/workflow.md](docs/workflow.md) / [docs/spec-driven.md](docs/spec-driven.md) / [docs/learning-path.md](docs/learning-path.md)
- CLI MIDI ソフト候補: [docs/midi-cli-tools.md](docs/midi-cli-tools.md)
- **ライセンス上の注意**: [docs/licensing.md](docs/licensing.md)(NEUTRINO 本体・モデルは含みません。出力や中間データの AI/ML 学習利用は禁止されています)

## セットアップ
```sh
brew install uv ffmpeg fluid-synth      # MuseScore 4 は別途(brew install --cask musescore)
cp .env.example .env                    # NEUTRINO_DIR / MUSESCORE_BIN / SOUNDFONT を設定
uv sync
scripts/setup.sh                        # 不足の確認
```

## 使い方(例)
```sh
scripts/new_song.sh mysong                # projects/mysong/ と spec 雛形を作成
uv run scripts/spec_status.py mysong      # 次に決められる要素
uv run scripts/spec_check.py mysong       # spec と生成物の整合性
```
以降はエージェントに「新しい曲を作りたい」と伝えるか、`/new-song [曲名]` を実行すると、`coach-start` から対話的に進みます。

## 開発
`uv run ruff check .` / `uv run pytest` / `shellcheck scripts/*.sh`

## 免責
NEUTRINO は STUDIO NEUTRINO の製品です。本リポジトリは非公式の補助ツールです。

## 聴く
`scripts/play.sh <path>`(`projects/` 配下の wav / mp3 / MIDI。`--list <曲名>` で一覧)。mpv が必要: `brew install mpv`。

## 参考曲から雰囲気をつかむ
`/reference <曲名> <YouTube URL>` で参考曲を分析し、テンポ・キー・コード機能などから曲のイメージを言葉にします。詳細と注意は `docs/reference-analysis.md`。
