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
