# app.py (or your current Streamlit script)
import sys
import tempfile
from pathlib import Path
import streamlit as st

from text2audio.core import synthesize
from text2audio.model_repo import MODELS, ensure_model

# NEW: import the extraction helpers
from file_to_text import extract_text_from_bytes, has_ocr_stack

st.set_page_config(page_title="text2audio", page_icon="🔊")
st.title("Text → Audio")
st.caption(f"Working dir: `{Path.cwd()}` · Python: `{sys.executable}`")

# ---------- File → Text UI (collapsed until needed) ----------
prefill_text = ""
uploaded = None
use_ocr = False
ocr_lang = "eng+deu"

with st.expander("1) Optional: Convert a file to text (click to open)"):
    uploaded = st.file_uploader(
        "Supported: .pdf, .docx, .txt",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=False,
        help="Drag & drop or browse. Text will be extracted and placed into the text box below."
    )

    use_ocr = st.checkbox(
        "Use OCR for scanned PDFs (slower, needs Tesseract + Poppler)",
        value=False,
        help="Enable if your PDF is scanned images. Requires pytesseract + pdf2image + poppler."
    )

    if use_ocr:
        ocr_lang = st.text_input(
            "OCR language(s)",
            value="eng+deu",
            help="Tesseract language codes (e.g., eng, deu, eng+deu)."
        )

    if uploaded is not None:
        file_bytes = uploaded.read()
        uploaded.seek(0)

        # Small callback to stream progress/info messages into the UI (used by OCR)
        def _on_info(msg: str) -> None:
            st.write(msg)

        try:
            prefill_text = extract_text_from_bytes(
                uploaded.name,
                file_bytes,
                use_ocr=use_ocr,
                ocr_lang=ocr_lang if use_ocr else None,
                on_info=_on_info,
            )
            if prefill_text.strip():
                st.success(f"Extracted ~{len(prefill_text)} characters from **{uploaded.name}**")
            else:
                if uploaded.name.lower().endswith(".pdf") and not use_ocr:
                    st.warning("No text found. If this is a scanned PDF, enable OCR and try again.")
                else:
                    st.warning(f"No text extracted from **{uploaded.name}**.")
        except Exception as e:
            st.error(str(e))
            if "OCR" in str(e) and not has_ocr_stack():
                st.info("Hint: `pip install pdf2image pillow pytesseract` and install system poppler + tesseract.")

# ---------- Text input ----------
st.subheader("2) Edit or paste your text")
text = st.text_area("Your text", height=220, placeholder="Type something…", value=prefill_text)

# ---------- TTS controls ----------
st.subheader("3) Choose a voice backend and synthesize")

backend_label = st.selectbox(
    "Backend",
    ["gTTS (mp3, online)", "pyttsx3 (wav, offline)", "Piper (wav, offline)"]
)

piper_model_key = None
if backend_label.startswith("Piper"):
    st.info("Voices download automatically from Hugging Face on first use.")
    keys = sorted(MODELS.keys())
    piper_model_key = st.selectbox("Piper voice", keys, index=keys.index("de_DE-thorsten-high") if "de_DE-thorsten-high" in keys else 0)

filename = st.text_input(
    "Output filename",
    value="speech.wav" if backend_label.startswith(("Piper", "pyttsx3")) else "speech.mp3"
)

chunking = st.checkbox("Split text into ~1200-character chunks (recommended for very long texts)", value=False)

def _chunks(s, n=1200):
    s = s.strip()
    for i in range(0, len(s), n):
        yield s[i:i+n]

if st.button("Synthesize") and text.strip():
    try:
        chosen = "gtts" if backend_label.startswith("gTTS") else ("pyttsx3" if backend_label.startswith("pyttsx3") else "piper")

        if chosen == "piper":
            prog = st.progress(0.0, text="Checking voice model…")
            def _cb(label, frac):
                prog.progress(frac, text=label)
            ensure_model(piper_model_key, progress_cb=_cb)
            prog.empty()

        if chunking and len(text) > 1500:
            import zipfile
            tmpdir = Path(tempfile.mkdtemp(prefix="tts_chunks_"))
            out_zip = Path(filename).with_suffix(".zip")
            paths = []
            for idx, part in enumerate(_chunks(text), start=1):
                part_name = Path(filename).with_stem(Path(filename).stem + f"_{idx}")
                out_path = synthesize(
                    part,
                    backend=chosen,
                    out=str(tmpdir / part_name.name),
                    piper_model=piper_model_key if chosen == "piper" else None,
                )
                paths.append(out_path)

            with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for p in paths:
                    zf.write(p, arcname=p.name)

            st.success(f"Saved {len(paths)} audio chunks → {out_zip}")
            st.download_button("Download ZIP", data=out_zip.read_bytes(), file_name=out_zip.name)
        else:
            out_path = synthesize(
                text,
                backend=chosen,
                out=filename,
                piper_model=piper_model_key if chosen == "piper" else None,
            )
            if not out_path.exists():
                st.error(f"Audio file not found: {out_path}")
            else:
                st.success(f"Saved → {out_path}")
                st.audio(str(out_path))
                st.download_button("Download audio", data=out_path.read_bytes(), file_name=out_path.name)

    except Exception as e:
        st.error(f"Failed to synthesize: {e}")
