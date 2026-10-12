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


SOUNDS = {**INFO, "samples": {"bd": ["bd_haus"], "bass": ["bass_hit_c"]}, "chords": ["minor7", "major7", "7", "m7"], "scales": ["minor", "major"]}


def test_sample_names_are_checked_when_sounds_json_is_loaded():
    code = "live_loop :a do\n  sample :bd_haus\n  sample :bass_hit_c\n  sample :bd_hause\n  sleep 1\nend\n"
    probs = live_check.check(code, SOUNDS)
    assert len(probs) == 1 and "bd_hause" in probs[0] and "bd_haus" in probs[0]
    assert live_check.check(code, INFO) == []  # sounds JSON が無いときは検査しない


def test_grid_voice_sample_and_paths_and_comments():
    assert live_check.check('k = grid_voice :sample, :bd_haus, amp: 1\nsample "/tmp/a.wav"\n# sample :nope\n', SOUNDS) == []
    assert any("nope" in p for p in live_check.check("k = grid_voice :sample, :nope\n", SOUNDS))


def test_chord_and_scale_names():
    ok = "chord(:f3, :minor7)\nchord :c3, '7'\nx = grid_prog [:f3, :minor7], [:db3, :major7]\nscale(:c3, :minor)\nchord(r, t)\n"
    assert live_check.check(ok, SOUNDS) == []
    probs = live_check.check("chord(:f3, :minorr7)\nx = [[:f3, :nope]]\nscale :c3, :minr\n", SOUNDS)
    assert len(probs) == 3 and "minor7" in probs[0]
