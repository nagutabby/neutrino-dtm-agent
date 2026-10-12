import check_structure as cs

HEAD = "| セクション | 小節 | 雰囲気・役割 | コード進行 | 鳴らす楽器 | つなぎ | 確認 |\n|---|---|---|---|---|---|---|\n"


def rows(*lines):
    return cs.parse(HEAD + "\n".join(lines))


GOOD = (
    "| イントロ | 1-8 | 静か | Fm7→Fm7→Dbmaj7→Dbmaj7 | ピアノ | riser | ✔ 2026-10-12 |",
    "| ビルド | 9-16 | 緊張 | Bbm7→Dbmaj7→Ebmaj7→C7 | ピアノ,ドラム | 無音 | ✔ 2026-10-12 |",
    "| ドロップ | 17-32 | 開放 | Fm7→Dbmaj7→Abmaj7→Ebmaj7 | 全部 | なし | ✔ 2026-10-12 |",
)


def test_parse_skips_header_and_separator():
    r = rows(*GOOD)
    assert len(r) == 3 and r[1]["セクション"] == "ビルド" and r[0]["確認"].startswith("✔")


def test_good_structure_has_no_problems():
    assert cs.check(rows(*GOOD), final=True, min_sections=3) == ([], [])


def test_unconfirmed_is_warning_in_progress_but_error_in_final():
    r = rows(GOOD[0].replace("✔ 2026-10-12", ""), *GOOD[1:])
    e, w = cs.check(r, final=False, min_sections=3)
    assert not e and any("確認" in x for x in w)
    e, _ = cs.check(r, final=True, min_sections=3)
    assert any("確認" in x for x in e)


def test_too_few_sections_and_missing_fields_are_errors():
    e, _ = cs.check(rows(GOOD[0]), final=False, min_sections=3)
    assert any("1 個" in x for x in e)
    e, _ = cs.check(rows(GOOD[0].replace("Fm7→Fm7→Dbmaj7→Dbmaj7", ""), *GOOD[1:]), final=False, min_sections=3)
    assert any("コード進行" in x for x in e)


def test_same_progression_everywhere_is_an_error():
    same = [g.replace(g.split("|")[4], " Fm7→Dbmaj7→Abmaj7→Ebmaj7 ") for g in GOOD]
    e, _ = cs.check(rows(*same), final=False, min_sections=3)
    assert any("同じコード進行" in x for x in e)


def test_overlap_is_error_and_gap_is_warning():
    e, _ = cs.check(rows(GOOD[0], GOOD[1].replace("9-16", "8-16"), GOOD[2]), final=False, min_sections=3)
    assert any("重なって" in x for x in e)
    e, w = cs.check(rows(GOOD[0], GOOD[1].replace("9-16", "10-16"), GOOD[2]), final=False, min_sections=3)
    assert not e and any("9-9" in x for x in w)


def test_adjacent_sections_with_same_progression_and_instruments_warn():
    dup = GOOD[1].replace("Bbm7→Dbmaj7→Ebmaj7→C7", "Fm7→Fm7→Dbmaj7→Dbmaj7").replace("ピアノ,ドラム", "ピアノ")
    _, w = cs.check(rows(GOOD[0], dup, GOOD[2]), final=False, min_sections=3)
    assert any("進行も楽器も同じ" in x for x in w)


def test_bars_of():
    assert cs.bars_of("1-8") == (1, 8) and cs.bars_of("5") == (5, 5) and cs.bars_of("8-1") is None
