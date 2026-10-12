import check_grid as cg

BAR = "x... x... x... x..."


def test_good_demo_has_no_problems():
    text = f'use_bpm 150\nfour = "{BAR}"\nlive_loop :kick do\n  grid_play kick, four\nend\n'
    assert cg.check(text) == ([], [])


def test_grid_must_be_multiple_of_16_cells():
    e, _ = cg.check('use_bpm 150\nx = "x... x... x..."\nlive_loop :a do\n  grid_play k, x\nend\n')
    assert any("12 マス" in m for m in e)


def test_separators_and_comments_are_ignored():
    text = f'use_bpm 150\nx = "{BAR} | {BAR}" # "x..." はコメント\nlive_loop :a do\n  grid_play k, x\nend\n'
    assert cg.check(text) == ([], [])


def test_non_grid_strings_are_not_checked():
    assert cg.check('puts "..."\nputs "x"\nputs "xo"\n') == ([], [])


def test_hit_beats_counts_ties():
    assert cg.hit_beats("x--- x... X.o-") == [1.0, 0.25, 0.25, 0.5]


def test_chop_from_count_must_match_hits():
    text = 'use_bpm 150\nv = grid_clip "a.wav", 16\nlive_loop :v do\n  grid_chop v, "x--- x--- X--- x-o-", from: [0, 1, 2]\nend\n'
    e, _ = cg.check(text)
    assert any("3 個、音は 5 個" in m for m in e)


def test_chop_from_must_stay_inside_clip():
    text = 'use_bpm 150\nv = grid_clip "a.wav", 4\nlive_loop :v do\n  grid_chop v, "x--- x---", from: [0, 3.5]\nend\n'
    e, _ = cg.check(text)
    assert any("はみ出す" in m for m in e)


def test_chop_with_variable_pattern_is_resolved():
    text = 'use_bpm 150\nv = grid_clip "a.wav", 16\np = "x--- x--- x--- x---"\nlive_loop :v do\n  grid_chop v, p, from: [0, 4, 8]\nend\n'
    e, _ = cg.check(text)
    assert any("3 個、音は 4 個" in m for m in e)


def test_define_needs_grid_prefix_and_loops_must_not_double_sleep():
    text = 'use_bpm 150\ndefine :on_air do\nend\nlive_loop :a do\n  grid_play k, x\n  sleep 1\nend\n'
    _, w = cg.check(text)
    assert any("on_air" in m for m in w) and any("sleep は要りません" in m for m in w)


def test_use_bpm_missing_or_duplicated():
    _, w = cg.check('live_loop :a do\n  sleep 1\nend\n')
    assert any("use_bpm がありません" in m for m in w)
    _, w = cg.check('use_bpm 120\nuse_bpm 150\n')
    assert any("2 箇所" in m for m in w)


def test_operators_are_warned():
    text = f'use_bpm 150\na = "{BAR}"\nb = a.mask("{BAR}")\nc = "{BAR}" + "{BAR}"\n'
    _, w = cg.check(text)
    assert len([m for m in w if "演算" in m or "連結" in m]) == 2


def loop(body: str) -> str:
    return f"use_bpm 120\n{body}\nlive_loop :a do\n  grid_play k, x\nend\n"


def test_dotted_eighth_fits_default_grid():
    assert cg.hit_beats("x-- x-- x-- x-- x-- x-. .... ....") == [0.75] * 5 + [0.5]


def test_meter_3_makes_a_bar_12_cells():
    ok = loop('grid_meter 3\nx = "x... x... x..."')
    assert cg.check(ok) == ([], [])
    e, _ = cg.check(loop('grid_meter 3\nx = "x... x... x... x..."'))
    assert any("16 マス(1小節 = 12マス" in m for m in e)


def test_meter_5_and_res_3_triplets():
    assert cg.check(loop('grid_meter 5\nx = "x... x... x... x... x..."')) == ([], [])
    assert cg.check(loop('grid_res 3\nx = "x.. x.. x.. x.."')) == ([], [])  # 4/4 の8分3連 = 12マス
    e, _ = cg.check(loop('grid_res 3\nx = "x... x... x... x..."'))
    assert any("1小節 = 12マス" in m for m in e)


def test_six_eight_is_res_2_meter_3():
    assert cg.check(loop('grid_res 2\ngrid_meter 3\nx = "x.x.x. x.x.x."')) == ([], [])


def test_hit_beats_follow_resolution():
    assert cg.hit_beats("x-. x..", res=3) == [2 / 3, 1 / 3]
    assert cg.hit_beats("x.. x-.", res=2) == [0.5, 1.0]


def test_chop_range_uses_resolution():
    text = 'grid_res 2\ngrid_meter 3\nv = grid_clip "a.wav", 3\nlive_loop :v do\n  grid_chop v, "x-x.x-", from: [0, 2, 2.5]\nend\nuse_bpm 100\n'
    e, _ = cg.check(text)
    assert any("3 番目" in m and "はみ出す" in m for m in e)


def test_invalid_or_conflicting_settings():
    e, _ = cg.check("use_bpm 100\ngrid_res 0\n")
    assert any("正の整数" in m for m in e)
    _, w = cg.check("use_bpm 100\ngrid_meter 3\ngrid_meter 4\n")
    assert any("grid_meter が複数" in m for m in w)
