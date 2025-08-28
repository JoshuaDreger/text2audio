from pathlib import Path
from typing import Literal
from text2audio.backends import tts_gtts, tts_pyttsx3


Backend = Literal["gtts", "pyttsx3"]

def synthesize(text: str, backend: Backend = "gtts", lang: str = "en", out: str = "out.mp3") -> Path:
    out_path = Path(out)
    if backend == "gtts":
        # enforce mp3 for gTTS
        if out_path.suffix.lower() != ".mp3":
            out_path = out_path.with_suffix(".mp3")
        return tts_gtts(text, lang=lang, out=out_path)
    elif backend == "pyttsx3":
        # enforce wav for pyttsx3 (most reliable)
        if out_path.suffix.lower() != ".wav":
            out_path = out_path.with_suffix(".wav")
        return tts_pyttsx3(text, lang=lang, out=out_path)
    else:
        raise ValueError(f"Unknown backend: {backend}")
