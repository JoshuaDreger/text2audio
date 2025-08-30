# file_to_text.py
from __future__ import annotations
import io
import tempfile
from pathlib import Path
from typing import Callable, Optional

# ---- Optional imports (lazily checked) ----
try:
    from pdfminer.high_level import extract_text as _pdf_extract_text
except Exception:
    _pdf_extract_text = None  # type: ignore

try:
    import docx2txt as _docx2txt
except Exception:
    _docx2txt = None  # type: ignore


def has_ocr_stack() -> bool:
    """Return True if pytesseract + pdf2image + PIL are importable."""
    try:
        import pytesseract  # noqa: F401
        from pdf2image import convert_from_bytes  # noqa: F401
        from PIL import Image  # noqa: F401
        return True
    except Exception:
        return False


def _ocr_pdf_bytes(
    file_bytes: bytes,
    *,
    ocr_lang: str = "eng+deu",
    on_info: Optional[Callable[[str], None]] = None,
) -> str:
    """OCR a PDF (bytes) page-by-page using pytesseract + pdf2image."""
    import pytesseract
    from pdf2image import convert_from_bytes

    pages = convert_from_bytes(file_bytes, dpi=300)
    out_parts = []
    total = len(pages)
    for i, img in enumerate(pages, start=1):
        if on_info:
            on_info(f"OCR page {i}/{total}…")
        out_parts.append(pytesseract.image_to_string(img, lang=ocr_lang))
    return "\n".join(out_parts)


def extract_text_from_bytes(
    filename: str,
    data: bytes,
    *,
    use_ocr: bool = False,
    ocr_lang: str = "eng+deu",
    on_info: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Best-effort text extraction from (filename, bytes).

    - .txt  → decode (utf-8 → latin-1 fallback)
    - .docx → docx2txt
    - .pdf  → pdfminer.six (if available), else OCR if enabled,
              or OCR if text extraction returns empty and use_ocr=True.
    """
    fname = filename.lower()

    # TXT
    if fname.endswith(".txt"):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1", errors="ignore")

    # DOCX
    if fname.endswith(".docx"):
        if _docx2txt is None:
            raise RuntimeError("docx2txt not installed. Install with: pip install docx2txt")
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(data)
            tmp.flush()
            try:
                return _docx2txt.process(tmp.name) or ""
            finally:
                Path(tmp.name).unlink(missing_ok=True)

    # PDF
    if fname.endswith(".pdf"):
        # 1) Try text extraction first when possible (fast, accurate for text PDFs)
        if _pdf_extract_text is not None and not use_ocr:
            try:
                txt = _pdf_extract_text(io.BytesIO(data)) or ""
                if txt.strip():
                    return txt
                # If empty and OCR requested, fall through to OCR below
            except Exception as e:
                # If OCR is allowed, we’ll try that next.
                if not use_ocr:
                    raise RuntimeError(f"PDF text extraction failed (pdfminer): {e}") from e

        # 2) OCR path
        if use_ocr:
            if not has_ocr_stack():
                raise RuntimeError(
                    "OCR stack missing. Install: pdf2image pillow pytesseract, and system poppler + tesseract."
                )
            return _ocr_pdf_bytes(data, ocr_lang=ocr_lang, on_info=on_info)

        # If we got here: either pdfminer is missing or yielded nothing and OCR wasn’t requested
        if _pdf_extract_text is None:
            raise RuntimeError("Install pdfminer.six or enable OCR to extract from PDFs.")
        return ""  # pdfminer returned nothing and OCR not enabled

    # Unsupported
    raise RuntimeError("Unsupported file type. Supported: .pdf, .docx, .txt")


def extract_text_from_path(
    path: Path | str,
    *,
    use_ocr: bool = False,
    ocr_lang: str = "eng+deu",
    on_info: Optional[Callable[[str], None]] = None,
) -> str:
    """Convenience for non-Streamlit contexts: extract text from a file path."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    data = p.read_bytes()
    return extract_text_from_bytes(p.name, data, use_ocr=use_ocr, ocr_lang=ocr_lang, on_info=on_info)
