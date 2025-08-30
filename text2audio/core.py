from pathlib import Path
from typing import Literal, Optional, Union
from text2audio.backends import tts_gtts, tts_pyttsx3, tts_piper

Backend = Literal["gtts", "pyttsx3", "piper"]

def synthesize(
    text: str,
    backend: Backend = "gtts",
    lang: str = "en",
    out: str = "out.mp3",
    *,
    # Piper:
    piper_model: Optional[Union[str, Path]] = None,
) -> Path:
    out_path = Path(out).expanduser().resolve()

    if backend == "gtts":
        if out_path.suffix.lower() != ".mp3":
            out_path = out_path.with_suffix(".mp3")
        return tts_gtts(text, lang=lang, out=out_path)

    elif backend == "pyttsx3":
        if out_path.suffix.lower() != ".wav":
            out_path = out_path.with_suffix(".wav")
        return tts_pyttsx3(text, lang=lang, out=out_path)

    elif backend == "piper":
        if out_path.suffix.lower() != ".wav":
            out_path = out_path.with_suffix(".wav")
        if not piper_model:
            raise ValueError("For backend='piper', provide piper_model (short key or path).")
        return tts_piper(
            text,
            model=piper_model,
            out=out_path,
        )

    else:
        raise ValueError(f"Unknown backend: {backend}")
