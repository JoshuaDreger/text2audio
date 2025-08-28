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
    piper_model: Optional[Union[str, Path]] = None,  # accepts short key (e.g., "de_DE-thorsten-high") or path
    length_scale: Optional[float] = None,
    noise_scale: Optional[float] = None,
    noise_w: Optional[float] = None,
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
            length_scale=length_scale or 1.0,
            noise_scale=noise_scale or 0.667,
            noise_w=noise_w or 0.8,
        )

    else:
        raise ValueError(f"Unknown backend: {backend}")
