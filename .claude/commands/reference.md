---
description: ユーザーが挙げた YouTube の参考曲(最低3つ)をダウンロード・音源分離・分析し、その共通点を few-shot の例として曲のイメージを固める
argument-hint: "<曲名> <YouTubeのURL> <URL> <URL>..."
---

参考曲の分析を行い、ユーザーが作りたい曲のイメージを言葉にする手伝いをする。引数: $ARGUMENTS(`<song> <url>...`。URL は**最低3つ**。足りなければ `AskUserQuestion` で聞く)

方針: **MIDI の検索・取得・書き起こしはしない**。ユーザーが挙げた参考曲(最低3つ)を YouTube から取得して**音源分離 → 音声の分析**を行い、複数曲の結果を **few-shot の例**として並べ、共通点から曲の型をつかむ。

1. 最初に `docs/reference-analysis.md` の注意(私的な分析のみ・複製しない・公開しない)を1〜2行で伝える。対象は YouTube の単体動画(10 分以内)。
2. `projects/<song>/` が無ければ `/new-song` を先に案内する。
3. **参考曲の分析**: URL が3つ未満なら不足分を聞く(3つ揃うまで進めない。Web 検索で類似曲を探して補わない)。1曲ずつ `scripts/reference_run.sh <song> <url> --dry-run` で確認 → 実行(YouTube 取得 → 音源分離 → 分析)。各 `projects/<song>/reference/<id>/analysis.md` を読む。再生リスト・チャンネル一括取得はしない。
4. **few-shot の例をまとめる**: `uv run scripts/reference_summary.py <song>` で `reference/summary.md`(曲ごとの数値表+共通点)を作る。
5. 次の3点で報告する(参考曲を並べ、共通点・違いを整理する):
   - **わかったこと**: テンポ・キー(長調/短調)・コード機能の並び・盛り上がりの形・パート比・明るさ・刻みの細かさを、`docs/music-theory.md` の理論で平易に(初出用語は最大2つ、数値付き)。
   - **聴きどころ**: ユーザーが聴き直して確かめる箇所(何秒付近)。`scripts/play.sh projects/<song>/reference/<id>/stems/piano.wav --start 秒` のような再生コマンドを添える(`scripts/play.sh --list <song>`)。推定の限界(テンポの倍/半分違い、コード推定の取り違え、分離の混ざり)を正直に伝える。
   - **次の選択肢**: 「この型で行く / 一部だけ取り入れる(例: テンポとコード機能だけ)/ 参考曲を差し替えて再分析する」(最大3)。
6. ユーザーが選んだ方向を `spec/00-concept.md` の下書き差分案として示す(ユーザーが了承するまで spec を変更しない)。旋律・歌詞・リズムの丸写しは提案しない。
7. 結果と学んだ点を `notes.md` に追記する(参考曲の曲名と YouTube URL も)。
