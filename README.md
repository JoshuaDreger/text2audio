# text2audio 🔊

Tiny, pluggable Text-to-Speech (TTS) with CLI + Streamlit UI.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .


## Run with CLI:

python -m text2audio.cli -t "Hello World" -b gtts -l en -o hello1.mp3

echo "Guten Tag!" | python -m text2audio.cli -b pyttsx3 -l de -o hallo.wav


## Run with UI:

streamlit run text2audio/web_app.py






