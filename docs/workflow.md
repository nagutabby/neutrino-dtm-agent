# ワークフロー

1. ユーザーが Sonic Pi で曲を始め、コードを `projects/<song>/current.rb` に保存して伝える(`/new-song`)。
2. 繰り返す: **今の音を改善**(`live-improve`)または**次のステムを提示**(`live-next-stem`)。提案は小さく1つずつ、`proposals/` にコードで置き、必要なら `live_render.py` で録音して試聴。採否はユーザーが決める。
3. できたら**最終の全体レビュー**(`live-review`)。
