import pytest
import reference_analyze as ra


def test_roman_numerals_relative_to_major_tonic():
    assert ra.roman(7, "", 0) == "V"  # C メジャーの G
    assert ra.roman(9, "m", 0) == "vi"  # Am
    assert ra.roman(10, "", 0) == "♭VII"


def test_key_estimation_prefers_tonic():
    np = pytest.importorskip("numpy")
    chroma = np.zeros(12)
    chroma[[0, 4, 7]] = 1.0
    chroma[[2, 5, 9, 11]] = 0.3
    tonic, mode, _ = ra.estimate_key(chroma)
    assert (tonic, mode) == (0, "長調")


def test_ref_id_rejects_path_escape(tmp_path):
    import common

    with pytest.raises(SystemExit):
        common.safe_ref_dir(tmp_path, "../x")
