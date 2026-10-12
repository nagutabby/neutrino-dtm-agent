import learning_log as ll

SAMPLE = """# 学習ログ
<!-- INDEX:START -->
<!-- INDEX:END -->

### L001 ハーフタイムのドラム
- タグ: #ハーフタイム #half-time #バックビート
- 意味: スネアを3拍目だけに置くと、体感のテンポが半分になる

### L002 サイドチェイン風の沈み
- タグ: #サイドチェイン #sidechain #バックビート
- 意味: キックの瞬間に他の音を沈める
"""


def test_parse_collects_ids_titles_and_tags():
    e = ll.parse(SAMPLE)
    assert [x["id"] for x in e] == ["L001", "L002"]
    assert e[0]["tags"] == ["#ハーフタイム", "#half-time", "#バックビート"]


def test_index_lists_entries_and_tags():
    idx = ll.build_index(ll.parse(SAMPLE))
    assert "| L001 | ハーフタイムのドラム |" in idx
    assert "| #バックビート | L001, L002 |" in idx


def test_apply_index_is_idempotent_and_keeps_entries():
    once = ll.apply_index(SAMPLE)
    assert ll.apply_index(once) == once
    assert "### L002 サイドチェイン風の沈み" in once and "| #sidechain | L002 |" in once


def test_search_requires_all_words_case_insensitive():
    e = ll.parse(SAMPLE)
    assert [x["id"] for x in ll.search(e, ["#SideChain"])] == ["L002"]
    assert [x["id"] for x in ll.search(e, ["バックビート"])] == ["L001", "L002"]
    assert ll.search(e, ["バックビート", "キック"]) == [e[1]]
    assert ll.search(e, ["存在しない語"]) == []
