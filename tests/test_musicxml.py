import subprocess
import sys
from pathlib import Path

import musicxml_validate

ROOT = Path(__file__).resolve().parent.parent

XML = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1"><part-list><score-part id="P1"><part-name>V</part-name></score-part></part-list>
<part id="P1"><measure number="1"><attributes><divisions>1</divisions></attributes>
<direction><sound tempo="120"/></direction>
<note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration></note>
<note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration></note>
<note><rest/><duration>2</duration></note>
</measure></part></score-partwise>"""


def test_inject_and_validate(tmp_path):
    x = tmp_path / "a.musicxml"
    x.write_text(XML, encoding="utf-8")
    lyr = tmp_path / "l.txt"
    lyr.write_text("き ら\n", encoding="utf-8")
    errors, _ = musicxml_validate.validate(str(x))
    assert any("歌詞のない" in e for e in errors)
    out = tmp_path / "b.musicxml"
    subprocess.run([sys.executable, str(ROOT / "scripts/lyrics_inject.py"), str(x), str(lyr), "-o", str(out)], check=True)
    errors, _ = musicxml_validate.validate(str(out))
    assert errors == []


def test_inject_count_mismatch_fails(tmp_path):
    x = tmp_path / "a.musicxml"
    x.write_text(XML, encoding="utf-8")
    lyr = tmp_path / "l.txt"
    lyr.write_text("き\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "scripts/lyrics_inject.py"), str(x), str(lyr), "-o", str(tmp_path / "o.xml")], capture_output=True, text=True)
    assert r.returncode != 0
