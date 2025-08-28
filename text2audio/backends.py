from pathlib import Path
from typing import Optional

def _prep_out(out: Path) -> Path:
    out = out.expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    return out

def tts_gtts(text: str, lang: str = "en", out: Path = Path("out.mp3")) -> Path:
    from gtts import gTTS
    out = _prep_out(out)
    tts = gTTS(text=text, lang=lang)
    tts.save(str(out))
    if not out.exists():
        raise RuntimeError(f"gTTS reported success but file not found: {out}")
    return out

def tts_pyttsx3(text: str, lang: Optional[str] = None, out: Path = Path("out.wav")) -> Path:
    import pyttsx3, time
    out = _prep_out(out)
    engine = pyttsx3.init()
    if lang:
        for v in engine.getProperty("voices"):
            # robust language check
            langs = []
            try:
                langs = [x.decode().lower() if isinstance(x, (bytes, bytearray)) else str(x).lower() for x in getattr(v, "languages", [])]
            except Exception:
                pass
            name = getattr(v, "name", "").lower()
            if lang.lower() in name or any(lang.lower() in l for l in langs):
                engine.setProperty("voice", v.id); break
    engine.save_to_file(text, str(out))
    engine.runAndWait()

    # Some Linux drivers are slow to flush. Poll briefly.
    for _ in range(50):  # up to ~2.5s
        if out.exists() and out.stat().st_size > 0:
            break
        time.sleep(0.05)
    if not out.exists() or out.stat().st_size == 0:
        raise RuntimeError(f"pyttsx3 did not produce audio at: {out}")
    return out
