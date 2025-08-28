# save as quick_piper_check.py (run with your venv's python)
from pathlib import Path
from piper import PiperVoice

model = Path("models/en_US-amy-medium.onnx").resolve()
print("Model:", model)
voice = PiperVoice.load(model)  # will raise if model is invalid
out = Path("models/_piper_test.wav")
with out.open("wb") as f:
    for chunk in voice.synthesize_stream_raw("This is a Piper test."):
        f.write(chunk)
print("Wrote:", out, out.stat().st_size, "bytes")
