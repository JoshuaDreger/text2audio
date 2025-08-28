import sys
import streamlit as st
from pathlib import Path
from text2audio.core import synthesize
from text2audio.model_repo import MODELS, ensure_model

st.set_page_config(page_title="text2audio", page_icon="🔊")
st.title("Text → Audio")
st.caption(f"Working dir: `{Path.cwd()}` · Python: `{sys.executable}`")

backend_label = st.selectbox(
    "Backend",
    ["gTTS (mp3, online)", "pyttsx3 (wav, offline)", "Piper (wav, offline)"]
)

text = st.text_area("Your text", height=200, placeholder="Type something…")

piper_model_key = None
length_scale = noise_scale = noise_w = None

if backend_label.startswith("Piper"):
    st.info("Voices download automatically from Hugging Face on first use.")
    keys = sorted(MODELS.keys())
    piper_model_key = st.selectbox("Piper voice", keys, index=keys.index("de_DE-thorsten-high") if "de_DE-thorsten-high" in keys else 0)

    c1, c2, c3 = st.columns(3)
    with c1:
        length_scale = st.number_input("length_scale", min_value=0.4, max_value=2.0, value=1.0, step=0.05)
    with c2:
        noise_scale  = st.number_input("noise_scale",  min_value=0.0, max_value=1.0, value=0.667, step=0.01)
    with c3:
        noise_w      = st.number_input("noise_w",      min_value=0.0, max_value=1.0, value=0.8,   step=0.01)

filename = st.text_input("Output filename", value="speech.wav" if backend_label.startswith("Piper") or backend_label.startswith("pyttsx3") else "speech.mp3")

if st.button("Synthesize") and text.strip():
    try:
        chosen = "gtts" if backend_label.startswith("gTTS") else ("pyttsx3" if backend_label.startswith("pyttsx3") else "piper")

        # For Piper: auto-download with visual progress
        if chosen == "piper":
            prog = st.progress(0.0, text="Checking model…")
            def _cb(label, frac):
                prog.progress(frac, text=label)
            # ensure both files are present (this will download if missing)
            ensure_model(piper_model_key, progress_cb=_cb)
            prog.empty()

        out_path = synthesize(
            text,
            backend=chosen,
            out=filename,
            piper_model=piper_model_key if chosen == "piper" else None,
            length_scale=length_scale if chosen == "piper" else None,
            noise_scale=noise_scale if chosen == "piper" else None,
            noise_w=noise_w if chosen == "piper" else None,
        )

        if not out_path.exists():
            st.error(f"Audio file not found: {out_path}")
        else:
            st.success(f"Saved → {out_path}")
            st.audio(str(out_path))
            data = out_path.read_bytes()
            st.download_button("Download audio", data=data, file_name=out_path.name)

    except Exception as e:
        st.error(f"Failed to synthesize: {e}")