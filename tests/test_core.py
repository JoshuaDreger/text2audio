from text2audio.core import synthesize
from pathlib import Path

def test_synthesize_gtts(tmp_path):
    out = tmp_path / "t.mp3"
    p = synthesize("hello", backend="gtts", lang="en", out=str(out))
    assert p.exists()

def test_synthesize_pyttsx3(tmp_path):
    out = tmp_path / "t.wav"
    p = synthesize("hallo", backend="pyttsx3", lang="de", out=str(out))
    assert p.exists()
