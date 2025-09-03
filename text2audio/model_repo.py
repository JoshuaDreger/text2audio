from __future__ import annotations
from pathlib import Path
from typing import Dict, Tuple
import shutil, gzip

DEFAULT_MODELS_DIR = Path("models")
HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

MODELS: Dict[str, Tuple[str, str]] = {
    "Thorsten (DE)": (
        "de/de_DE/thorsten/high",  # path
        "de_DE-thorsten-high"      # base filename
    ),
    "Karlsson (DE)": (
        "de/de_DE/karlsson/low",
        "de_DE-karlsson-low"
    ),
    "Amy (US)": (
        "en/en_US/amy/medium",
        "en_US-amy-medium"
    ),
    "Libri (US)": (
        "en/en_US/libritts_r/medium",
        "en_US-libritts_r-medium"
    ),
}

def _hf_url(dirpath: str, base: str, ext: str) -> str:
    # ext in {".onnx", ".onnx.gz", ".onnx.json"}
    return f"{HF_BASE}/{dirpath}/{base}{ext}"

def model_files(short_name: str, models_dir: Path = DEFAULT_MODELS_DIR) -> Tuple[Path, Path]:
    if short_name not in MODELS:
        raise KeyError(f"Unknown model key: {short_name}")
    _, base = MODELS[short_name]
    onnx = models_dir / f"{base}.onnx"
    meta = models_dir / f"{base}.onnx.json"
    return onnx, meta

def ensure_model(short_name: str, models_dir: Path = DEFAULT_MODELS_DIR, *, progress_cb=None) -> Tuple[Path, Path]:
    import requests

    models_dir.mkdir(parents=True, exist_ok=True)
    onnx_path, json_path = model_files(short_name, models_dir)
    dirpath, base = MODELS[short_name]

    def _download(url: str, dest: Path, label: str):
        with requests.get(url, stream=True, timeout=60) as r:
            if r.status_code == 404:
                raise FileNotFoundError(f"404 for {url}")
            r.raise_for_status()
            total = int(r.headers.get("Content-Length") or 0)
            done = 0
            tmp = dest.with_suffix(dest.suffix + ".part")
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if not chunk: continue
                    f.write(chunk); done += len(chunk)
                    if total and progress_cb:
                        progress_cb(label, min(done / total, 1.0))
            tmp.rename(dest)

    if not onnx_path.exists():
        try_exts = [(".onnx", False), (".onnx.gz", True)]
        last_err = None
        for ext, is_gz in try_exts:
            url = _hf_url(dirpath, base, ext)
            try:
                if progress_cb: progress_cb(f"Downloading {base}{ext}", 0.0)
                tmp = onnx_path.with_suffix(onnx_path.suffix + (".dl" if not is_gz else ".gz.dl"))
                _download(url, tmp, f"{base}{ext}")
                if is_gz:
                    if progress_cb: progress_cb(f"Decompressing {base}{ext}", 0.0)
                    with gzip.open(tmp, "rb") as src, open(onnx_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    tmp.unlink(missing_ok=True)
                else:
                    tmp.rename(onnx_path)
                break
            except Exception as e:
                last_err = e
                continue
        else:
            raise RuntimeError(f"Failed to fetch ONNX for {short_name}: {last_err}")

        head = onnx_path.read_bytes()[:256]
        if head.startswith(b"version https://git-lfs") or b"<html" in head.lower():
            raise RuntimeError(f"{onnx_path.name} is not a valid ONNX (LFS pointer or HTML).")
        if onnx_path.stat().st_size < 1024 * 1024:
            raise RuntimeError(f"{onnx_path.name} seems too small ({onnx_path.stat().st_size} bytes).")

    if not json_path.exists():
        url = _hf_url(dirpath, base, ".onnx.json")
        if progress_cb: progress_cb(f"Downloading {json_path.name}", 0.0)
        _download(url, json_path, json_path.name)

    return onnx_path, json_path
