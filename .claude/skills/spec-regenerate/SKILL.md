---
name: spec-regenerate
description: spec 変更後、stale になった要素を一覧提示し、確認を得て該当と下流のみ再生成する。
---

1. `uv run scripts/spec_check.py <song>` の `[stale]` と `depends_on` から再生成対象を一覧にして **ユーザーに確認**。
2. 対象を ready の spec から作り直し、`register_track.py` で v(N+1) として登録(旧版は残す)。音色(patch)を変えた場合は `patches.py check <song>` を先に通す。
3. `layer-track` の提示・技術解説・進行確認(`run_mode` に従う)を再度実施。
