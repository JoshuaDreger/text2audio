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

def tts_piper(
    text: str,
    model: Union[str, Path],               # short key or .onnx path
    out: Path = Path("out.wav"),
    *,
    length_scale: float = 1.0,
    noise_scale: float = 0.667,
    noise_w: float = 0.8,
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
        from piper import PiperVoice
        voice = PiperVoice.load(model_path)

        def _supported_kwargs(fn, **kwargs):
            try:
                params = inspect.signature(fn).parameters
                return {k: v for k, v in kwargs.items() if k in params and v is not None}
            except Exception:
                return {}

        kw = {
            "length_scale": length_scale,
            "noise_scale":  noise_scale,
            "noise_w":      noise_w,
        }

        with out.open("wb") as f:
            if hasattr(voice, "synthesize_stream"):              # newer API
                fn = voice.synthesize_stream
                try:
                    for chunk in fn(text, **_supported_kwargs(fn, **kw)):
                        f.write(chunk)
                except TypeError:
                    # retry without kwargs if this version doesn't accept them
                    for chunk in fn(text):
                        f.write(chunk)
            else:                                                # older API
                fn = voice.synthesize
                try:
                    data = fn(text, **_supported_kwargs(fn, **kw))
                except TypeError:
                    data = fn(text)
                # some versions return (bytes, sample_rate)
                if isinstance(data, tuple):
                    data = data[0]
                f.write(data)

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
        # only add CLI args that exist in most piper builds
        if length_scale is not None: cmd += ["--length_scale", str(length_scale)]
        if noise_scale  is not None: cmd += ["--noise_scale",  str(noise_scale)]
        if noise_w      is not None: cmd += ["--noise_w",      str(noise_w)]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Piper CLI failed: {e}") from py_err

        if not out.exists() or out.stat().st_size == 0:
            raise RuntimeError("Piper produced no audio via CLI.")
        return out