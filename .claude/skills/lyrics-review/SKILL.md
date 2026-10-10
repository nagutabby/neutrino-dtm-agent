---
name: lyrics-review
description: 歌詞を追加した直後、ボーカル合成の前に、Haiku 5.5 のサブエージェントで音節・歌いやすさ・内容をレビューし、指摘をユーザーに示す。
---

歌詞あり(`vocal` が歌あり)の曲だけ。歌詞を `07-lyrics` に決め、`lyrics_inject.py` で MusicXML に割り当てた**直後、`synth.sh` の前**に実行する。

1. **レビュー依頼**: `docs/lyrics-review-prompt.md` の役割プロンプト(`docs/vocal-tuning.md` を読ませる指示を含む)を埋め、`Agent` ツールを `model: "haiku"`(`claude-haiku-5-5`)で起動する。読み取りのみ。
2. **判定**: 先頭が `気になる点なし` なら終了。`要修正` なら、音節数(`lyrics_inject.py` / `musicxml_validate.py`)や旋律と照らして妥当性を確かめる。矛盾する指摘は採用しない。パラメータ(StyleShift など)の提案は `docs/vocal-tuning.md` の範囲に限る。
3. **提示と修正**: 採用した指摘と改善案(最大 2 つ)をユーザーに見せる。**歌詞を決めるのはユーザー**で、勝手に改変しない。了承された変更だけ `spec-revise` の流れで `07-lyrics` を version+1 し、下流(`08-vocal`)を `spec-regenerate` で作り直す。`step` は了承を得てから、`auto` は止まらず進める: AI が下書きした歌詞は指摘を採否判断して直し、ユーザーが書いた歌詞は変えずに指摘と案を最終報告にまとめる。
4. **再レビュー**: 変更したときだけ手順 1 に戻る(最大 2 周)。
5. **記録**: 指摘と決定を `notes.md` に追記。歌って確かめる箇所を添える。
