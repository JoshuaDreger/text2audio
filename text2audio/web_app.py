import streamlit as st
from pathlib import Path
from text2audio.core import synthesize

st.set_page_config(page_title="text2audio", page_icon="🔊")
st.title("Text → Audio")

backend = st.selectbox("Backend", ["gTTS (mp3, online)", "pyttsx3 (wav, offline)"])
lang = st.text_input("Language code", value="en", help="Try: en, de, es, fr, it...")
text = st.text_area("Your text", height=200, placeholder="Type something…")
filename = st.text_input("Output filename", value="speech.mp3" if backend.startswith("gTTS") else "speech.wav")

if st.button("Synthesize") and text.strip():
    chosen = "gtts" if backend.startswith("gTTS") else "pyttsx3"
    out_path = synthesize(text, backend=chosen, lang=lang, out=filename)
    data = Path(out_path).read_bytes()
    st.success(f"Saved → {out_path}")
    st.download_button("Download audio", data=data, file_name=Path(out_path).name)
