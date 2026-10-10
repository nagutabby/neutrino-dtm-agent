---
description: YouTube の参考曲を音源分離して分析し、ジャンルと雰囲気から類似曲の MIDI を Web 検索で集めて解析し、作りたい曲のイメージを固める
argument-hint: "<曲名> <YouTubeのURL>"
---

参考曲の分析を行い、ユーザーが作りたい曲のイメージを言葉にする手伝いをする。引数: $ARGUMENTS(`<song> <url>`。足りなければ `AskUserQuestion` で聞く)

参考曲の音声を MIDI に書き起こすことはしない。音声は**音源分離と音声の分析**までにとどめ、MIDI は**Web 検索で見つけた類似曲**から得る。

1. 最初に `docs/reference-analysis.md` の注意(私的な分析のみ・複製しない・公開しない)を1〜2行で伝える。対象は YouTube の単体動画(10 分以内)。
2. `projects/<song>/` が無ければ `/new-song` を先に案内する。
3. **音声の分析**: `scripts/reference_run.sh <song> <url> --dry-run` で確認 → 実行(音声取得 → 音源分離 → 分析)。`projects/<song>/reference/<id>/analysis.md` を読む。
4. **類似曲 MIDI の検索**(ジャンルが決まっていること。未定なら先にユーザーに聞く。推測しない):
   - 検索語は「ジャンル + 3 の分析から推定した雰囲気(テンポ帯・長調/短調・明るさ・盛り上がり)」。例: `lo-fi hip hop 80bpm minor mellow piano midi download`。WebSearch で 2〜3 種の語を試す。
   - 候補は **`.mid` / `.midi` への直リンクがある**もの、かつ利用条件が確認できるもの(フリー・CC・パブリックドメイン・サイトが個人利用の DL を認めているもの)を優先する。会員制・有料・規約で禁止のサイトは使わない。ページを巡回せず、1ファイルずつ直リンクだけを扱う。
   - 最大3曲に絞り、「曲名 / URL / どこが雰囲気に近いか / 利用条件」を一覧でユーザーに見せる(`step`: 了承を取ってから取得。`auto`: そのまま取得して後でまとめて報告)。確信のない曲を「似ている」と断定しない。
   - `scripts/reference_midi_fetch.py <song> <直リンクURL> --title "曲名" --note "利用条件・似ている点"`(先に `--dry-run`)で `projects/<song>/reference/midi/` に保存 → `uv run --group reference scripts/reference_midi_analyze.py <song>` で解析(`reference/midi/analysis.md`)。
   - 見つからない/取得できないときは、その旨を伝え、音声の分析だけで進める(無理に探し続けない)。
5. 次の3点で報告する(音声の分析と MIDI の分析を並べ、共通点・違いを整理する):
   - **わかったこと**: テンポ・キー(長調/短調)・コード機能の並び・盛り上がりの形・パート構成・音域・密度を、`docs/music-theory.md` の理論で平易に(初出用語は最大2つ、数値付き)。
   - **聴きどころ**: ユーザーが参考曲を聴き直して確かめる箇所(何秒付近)。`scripts/play.sh projects/<song>/reference/<id>/stems/piano.wav --start 秒` のような再生コマンドを添える(`scripts/play.sh --list <song>`。収集した MIDI は音色を持たないため `play.sh` では再生できず、数値の分析で扱う)。推定の限界(テンポの倍/半分違い、コード推定の取り違え、MIDI は採譜者の解釈を含む、検索で見つけた曲は参考曲そのものではない)を正直に伝える。
   - **次の選択肢**: 「この雰囲気で行く / 一部だけ取り入れる(例: テンポとコード機能だけ)/ 別の参考曲・別の検索語で探す」(最大3)。
6. ユーザーが選んだ方向を `spec/00-concept.md` の下書き差分案として示す(ユーザーが了承するまで spec を変更しない)。旋律・歌詞・リズムの丸写しは提案しない。
7. 結果と学んだ点を `notes.md` に追記する(取得した MIDI の出典 URL と利用条件も)。
