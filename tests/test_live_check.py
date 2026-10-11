import live_check

INFO = {"synths": {"tb303": ["cutoff", "res"]}, "fx": {"reverb": ["room", "mix"]}}


def test_ok():
    code = "live_loop :a do\n  use_synth :tb303\n  play :c2\n  sleep 1\nend\n"
    assert live_check.check(code, INFO) == []


def test_unknown_names_and_args():
    code = "synth :nope\nwith_fx :reverb, bogus: 1 do\nend\n"
    probs = live_check.check(code, INFO)
    assert any(":nope" in p for p in probs)
    assert any("bogus" in p for p in probs)


def test_live_loop_without_sleep():
    probs = live_check.check("live_loop :a do\n  play 60\nend\n", INFO)
    assert any("sleep" in p for p in probs)


def test_live_loop_with_if_and_sleep_after_block():
    code = "live_loop :a do\n  x = if true\n    1\n  else\n    2\n  end\n  if x == 1\n    play 60\n  end\n  sleep 1\nend\n"
    assert live_check.check(code, INFO) == []
