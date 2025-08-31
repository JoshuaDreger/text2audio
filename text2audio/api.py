# api.py
from __future__ import annotations
from pathlib import Path
from typing import Optional, List
import tempfile
import zipfile
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from text2audio.core import synthesize
from text2audio.model_repo import ensure_model, MODELS

app = FastAPI(title="text2audio API", version="1.0")

# Allow overriding via env; default matches your compose bind-mount
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/data"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class SynthesizeRequest(BaseModel):
    text: str = Field(..., description="Plain text to synthesize")
    backend: str = Field("pyttsx3", pattern="^(gtts|pyttsx3|piper)$")
    piper_model: Optional[str] = Field(
        None, description="Required if backend='piper' (short key or ONNX path)"
    )
    filename: Optional[str] = Field(
        None, description="Target filename; defaults to .wav for piper/pyttsx3, .mp3 for gtts"
    )
    chunking: bool = Field(
        False, description="If true and text is long, split into chunks and return ZIP"
    )
    chunk_size: int = Field(
        1200, ge=200, le=8000, description="Characters per chunk when chunking is enabled"
    )

def _chunk_iter(s: str, n: int = 1200):
    s = s.strip()
    for i in range(0, len(s), n):
        yield s[i : i + n]

@app.get("/api/models")
def list_models():
    """List Piper short keys available via model_repo.py."""
    return {"models": sorted(MODELS.keys())}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/synthesize")
def synthesize_json(payload: SynthesizeRequest):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(422, "Field 'text' must be a non-empty string.")

    # Piper voice pre-check (downloads model if needed)
    if payload.backend == "piper":
        if not payload.piper_model:
            raise HTTPException(422, "backend='piper' requires 'piper_model'.")
        if payload.piper_model in MODELS:
            ensure_model(payload.piper_model)  # download if missing

    # Determine default filename if not supplied
    if not payload.filename:
        payload.filename = "speech.wav" if payload.backend in ("piper", "pyttsx3") else "speech.mp3"

    # Ensure output path
    out_path = (OUTPUT_DIR / payload.filename).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Chunked flow → multiple files + a ZIP in /data
        if payload.chunking and len(text) > payload.chunk_size:
            tmpdir = Path(tempfile.mkdtemp(prefix="tts_chunks_"))
            paths: List[Path] = []
            stem = out_path.stem
            suffix = out_path.suffix

            for idx, part in enumerate(_chunk_iter(text, payload.chunk_size), start=1):
                part_out = tmpdir / f"{stem}_{idx}{suffix}"
                final_part = synthesize(
                    part,
                    backend=payload.backend,
                    out=str(part_out),
                    piper_model=payload.piper_model if payload.backend == "piper" else None,
                )
                paths.append(final_part)

            zip_path = out_path.with_suffix(".zip")
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for p in paths:
                    zf.write(p, arcname=p.name)

            return JSONResponse(
                {
                    "status": "ok",
                    "outputs": [str(p) for p in paths],
                    "zip": str(zip_path),
                    "message": f"Saved {len(paths)} chunks and ZIP.",
                }
            )

        # Single-file flow
        final = synthesize(
            text,
            backend=payload.backend,
            out=str(out_path),
            piper_model=payload.piper_model if payload.backend == "piper" else None,
        )
        return {"status": "ok", "output": str(final)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Synthesis failed: {e}")
