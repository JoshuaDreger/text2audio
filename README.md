# text2audio 🔊

**Flexible, pluggable Text‑to‑Speech (TTS)** with:

* **🐳 Docker (API + UI in one container)**
* **🌐 Streamlit Web UI**
* **🔗 HTTP API (FastAPI)**
* **💻 CLI**

Convert plain text (and documents via the UI) to audio with `.mp3` / `.wav` outputs. API and UI write to the **same output folder**.

---

## 🐳 Start here: Run with Docker (API + UI)

The easiest way to use **text2audio** is via Docker. One container runs **both** the HTTP API (Uvicorn on `:8000`) and the Streamlit **UI** (`:8501`). Audio files are saved inside the container at **`/data`** and appear on your host in `./output/` via a bind‑mount.

```bash
docker compose up --build
# or build once, then:
docker compose up -d
```

* API → [http://localhost:8000](http://localhost:8000)
* UI  → [http://localhost:8501](http://localhost:8501)
* Outputs on host → `./output/`


## 🔗 HTTP API (FastAPI)

### Endpoints

#### 1. See if API is up
* `curl -s -X GET http://localhost:8000/health`

#### 2. List all possible Piper models
* `curl -s -X GET http://localhost:8000/api/models`

#### 3. Convert Text to audio
* `curl -s -X POST http://localhost:8000/api/models   -H "Content-Type: application/json"   -d '{"text":"Guten Tag!","backend":"piper","piper_model":"Thorsten (DE)","filename":"thorsten.wav"}'`

### `POST /api/synthesize` — request body

```json
{
  "text": "Guten Tag!",              // required
  "backend": "pyttsx3",              // one of: gtts | pyttsx3 | piper
  "piper_model": "de_DE-thorsten-high", // required when backend = piper (short key or ONNX path)
  "filename": "speech.wav",          // optional; defaults by backend (.wav for piper/pyttsx3, .mp3 for gtts)
  "chunking": false,                  // if true, long text is split into chunks
  "chunk_size": 1200                  // chars per chunk (when chunking)
}
```

### Responses

* **Single file**

```json
{"status":"ok","output":"/data/speech.wav"}
```

* **Chunked ZIP**

```json
{
  "status": "ok",
  "outputs": ["/tmp/.../speech_1.wav", "..."],
  "zip": "/data/speech.zip",
  "message": "Saved N chunks and ZIP."
}
```

> Files are written to the container at `/data/...` and available on the host at `./output/...`.

### Examples

```bash
# Piper (offline)
curl -X POST http://localhost:8000/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Guten Tag!","backend":"piper","piper_model":"Thorsten (DE)","filename":"thorsten.wav"}'

# gTTS (online)
curl -X POST http://localhost:8000/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello World","backend":"gtts","filename":"hello.mp3"}'
```

---

## 🌐 Web UI (Streamlit)

Launches at [http://localhost:8501](http://localhost:8501) when running via Docker Compose. Features:

* Paste/edit text and synthesize via gTTS / pyttsx3 / Piper
* **Optional**: Convert **PDF/DOCX/TXT** into text first (with optional OCR for scanned PDFs)
* Preview audio and **download** the result
* All outputs saved under **`OUTPUT_DIR`** (default `/data`)

> You can change `OUTPUT_DIR` by setting the environment variable in Docker Compose.

### Local (without Docker)

```bash
streamlit run text2audio/web_app.py
```
(Outputs will go to `/data` unless you export `OUTPUT_DIR` differently.)

---

## 💻 CLI

```bash
# gTTS (mp3, online)
python -m text2audio.cli -t "Hello World" -b gtts -l en -o hello.mp3

# pyttsx3 (wav, offline) with piped input
echo "Guten Tag!" | python -m text2audio.cli -b pyttsx3 -l de -o hallo.wav
```

> The CLI and API both ultimately call the same `synthesize(...)` function.

---

## 📄 License

Licensed under the [MIT License](LICENSE).
