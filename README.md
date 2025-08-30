# text2audio 🔊

**Tiny, pluggable Text-to-Speech (TTS)** with both a **Command-Line Interface (CLI)** and a **Streamlit Web UI**.

---

## 🚀 Quickstart

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # (use `.venv\Scripts\activate` on Windows)

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

---

## 💻 Run with CLI

```bash
# Example 1: Using gTTS
python -m text2audio.cli -t "Hello World" -b gtts -l en -o hello1.mp3

# Example 2: Using pyttsx3 with piped input
echo "Guten Tag!" | python -m text2audio.cli -b pyttsx3 -l de -o hallo.wav
```

---

## 🌐 Run with Web UI

```bash
streamlit run text2audio/web_app.py
```

---

## 📦 Features

* 🔌 Pluggable TTS backends (e.g., gTTS, pyttsx3 — extend with your own)
* 🖥️ Simple CLI for quick audio generation
* 🎛️ Interactive Streamlit UI
* 🎶 Output to `.mp3` or `.wav`

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
