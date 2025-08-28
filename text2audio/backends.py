from pathlib import Path
from typing import Optional

def tts_gtts(text: str, lang: str = "en", out: Path = Path("out.mp3")) -> Path:
    from gtts import gTTS
    tts = gTTS(text=text, lang=lang)
    tts.save(str(out))
    return out

def tts_pyttsx3(text: str, lang: Optional[str] = None, out: Path = Path("out.wav")) -> Path:
    # pyttsx3 can only write to audio by recording its playback; simplest is to save to WAV via driver
    # Many engines don't support direct file output; we’ll use a simple fallback: say() + save_to_file()
    import pyttsx3
    engine = pyttsx3.init()
    # Optional: pick a voice by language substring if available
    if lang:
        for v in engine.getProperty("voices"):
            if lang in (v.languages[0].decode() if isinstance(v.languages[0], bytes) else str(v.languages[0])).lower() or lang in v.name.lower():
                engine.setProperty("voice", v.id); break
    engine.save_to_file(text, str(out))
    engine.runAndWait()
    return out
