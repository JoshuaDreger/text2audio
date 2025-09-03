from pathlib import Path
from typing import Optional, Union
import shutil, subprocess, inspect

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

# text2audio/backends.py
def tts_pyttsx3(text: str, lang: Optional[str] = None, out: Path = Path("out.wav")) -> Path:
    from pyttsx3_engine import synthesize_to_wav
    import shutil, subprocess, tempfile

    out = _prep_out(out)
    try:
        return Path(synthesize_to_wav(text, str(out), voice_lang=lang))
    except Exception as e_py:
        # Fallback to espeak CLI
        es = shutil.which("espeak") or shutil.which("espeak-ng")
        if not es:
            raise RuntimeError(f"pyttsx3 failed ({e_py}) and no espeak/espeak-ng CLI in PATH")
        cmd = [es, "-w", str(out)]
        if lang:
            # espeak lang codes look like 'en', 'de', 'en-us' etc.
            cmd += ["-v", lang]
        # Use stdin to avoid quote/escape headaches
        cp = subprocess.run(cmd, input=text.encode("utf-8"), check=False)
        if cp.returncode != 0 or (not out.exists() or out.stat().st_size == 0):
            raise RuntimeError(f"espeak CLI failed with code {cp.returncode}") from e_py
        return out


def tts_piper(
    text: str,
    model: Union[str, Path],               # short key or .onnx path
    out: Path = Path("out.wav")
) -> Path:
    """
    Robust Piper backend:
      • supports model short-keys (auto-download) or direct .onnx path
      • adapts to old/new Python APIs
      • falls back to 'piper' CLI if Python API fails
    """
    out = _prep_out(out)

    # Resolve model path (and auto-download if using short key)
    if isinstance(model, str) and "/" not in model and "\\" not in model:
        from text2audio.model_repo import ensure_model  # your helper module
        onnx_path, _ = ensure_model(model)
        model_path = onnx_path
    else:
        model_path = Path(model).expanduser().resolve()

    # Guard common file issues early
    sig = model_path.read_bytes()[:256]
    if sig.startswith(b"\x1f\x8b"):
        raise RuntimeError(f"{model_path.name} is gzipped (.onnx.gz). Decompress first.")
    if sig.startswith(b"version https://git-lfs"):
        raise RuntimeError(f"{model_path.name} is a Git LFS pointer. Download the real model.")
    if b"<html" in sig.lower() or b"<!doctype html" in sig.lower():
        raise RuntimeError(f"{model_path.name} looks like an HTML page, not a model.")
    sidecar = model_path.with_suffix(model_path.suffix + ".json")
    if not sidecar.exists():
        raise FileNotFoundError(f"Missing sidecar next to model: {sidecar.name}")

    # ---------- Try Python API first ----------
    try:
        import wave
        from piper import PiperVoice
        
        voice = PiperVoice.load(model_path)

        with wave.open(str(out), "wb") as wf:
            voice.synthesize_wav(text, wf)

        if not out.exists() or out.stat().st_size == 0:
            raise RuntimeError("Piper produced no audio via Python API.")
        return out

    except Exception as py_err:
        # ---------- Fallback to CLI ----------
        cli = shutil.which("piper")
        if not cli:
            raise RuntimeError(f"Piper Python API failed ({py_err}). Also no 'piper' CLI found in PATH. "
                               f"Install CLI with: pip install piper-tts") from py_err

        cmd = [
            cli, "--model", str(model_path),
            "--output_file", str(out),
            "--text", text,
        ]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Piper CLI failed: {e}") from py_err

        if not out.exists() or out.stat().st_size == 0:
            raise RuntimeError("Piper produced no audio via CLI.")
        return out