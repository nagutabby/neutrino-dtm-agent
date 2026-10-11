import neutrino_tune as nt
import numpy as np

SPEC = {"bpm": 120, "notes": [["あ", "A4", 4.0]]}  # A4 = 440Hz、頭に 4 拍(2 秒)の無音


def test_tighten_consonants_keeps_vowel_onset():
    rows = [[0, 100, "pau"], [100, 300, "k"], [300, 600, "a"]]
    out = nt.tighten_consonants(rows, 0.5)
    assert out[1] == [200, 300, "k"] and out[0][1] == 200 and out[2] == [300, 600, "a"]


def test_lock_pitch_pulls_to_note():
    f0 = np.zeros(400)
    f0[200:380] = 466.0  # 譜面(A4=440Hz)より約 100 セント高い
    out = nt.lock_pitch(f0, SPEC, lock=1.0, glide_ms=0, smooth=1)
    assert np.allclose(out[210:370], 440.0, atol=0.01)
    assert nt.cents_error(out, SPEC) < 1 < nt.cents_error(f0, SPEC)
    assert (out[:200] == 0).all()  # 無声フレームは触らない


def test_boost_melspec_only_above_floor():
    mel = np.full((10, 100), -7.0, dtype=np.float32)
    mel[3:6, :] = -3.0
    out = nt.boost_melspec(mel, [], hf=0.5, cons=0)
    assert np.allclose(out[4, nt.HF_BIN:], -2.5) and np.allclose(out[4, :nt.HF_BIN], -3.0)
    assert (out[0] == -7.0).all()
