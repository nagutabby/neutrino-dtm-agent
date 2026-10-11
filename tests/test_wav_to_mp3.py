import shutil
import wave

import pytest
import wav_to_mp3


def make_wav(path):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(b"\x00\x00" * 2 * 4800)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg がない")
def test_convert(tmp_path):
    src, dst = tmp_path / "a.wav", tmp_path / "a.mp3"
    make_wav(src)
    wav_to_mp3.convert(src, dst)
    assert dst.stat().st_size > 0


def test_resolve_missing():
    with pytest.raises(SystemExit):
        wav_to_mp3.resolve("no_such_file.wav")
