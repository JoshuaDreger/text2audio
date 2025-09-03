# pyttsx3_engine.py
import threading, atexit, time, os
import pyttsx3

_ENGINE = None
_LOCK = threading.Lock()

def _shutdown():
    global _ENGINE
    try:
        if _ENGINE is not None:
            _ENGINE.stop()
    finally:
        _ENGINE = None

def get_engine():
    global _ENGINE
    if _ENGINE is None:
        e = pyttsx3.init(driverName="espeak")
        _ENGINE = e
        atexit.register(_shutdown)
    return _ENGINE

def synthesize_to_wav(text: str, out_path: str, voice_lang: str | None = None, *,
                      timeout_per_1k_chars: float = 6.0):
    """
    Reuses a single engine. Runs a manual event loop with a timeout so it can’t hang forever.
    """
    e = get_engine()
    done = threading.Event()

    def _on_end(name, completed):
        done.set()

    with _LOCK:
        # (Re)connect listener every time (Streamlit reloads can drop refs)
        try:
            e.disconnect('finished-utterance')  # ignore error if not connected
        except Exception:
            pass
        e.connect('finished-utterance', _on_end)

        if voice_lang:
            try:
                for v in e.getProperty("voices"):
                    langs = []
                    try:
                        langs = [x.decode().lower() if isinstance(x, (bytes, bytearray)) else str(x).lower()
                                 for x in getattr(v, "languages", [])]
                    except Exception:
                        pass
                    name = getattr(v, "name", "").lower()
                    if voice_lang.lower() in name or any(voice_lang.lower() in l for l in langs):
                        e.setProperty("voice", v.id)
                        break
            except Exception:
                pass

        # Queue and run a manual loop
        e.save_to_file(text, out_path)
        e.startLoop(False)  # non-blocking loop

        try:
            # Iterate until finished or timeout
            timeout = max(4.0, (len(text) / 1000.0) * timeout_per_1k_chars)
            t0 = time.time()
            while True:
                e.iterate()
                if done.is_set():
                    break
                if time.time() - t0 > timeout:
                    raise TimeoutError(f"pyttsx3 synthesis timed out after {timeout:.1f}s")
                time.sleep(0.01)
        finally:
            # Ensure we end the loop and clear the queue either way
            try:
                e.endLoop()
            except Exception:
                pass
            e.stop()

    # Finalize: wait a moment for file flush
    for _ in range(50):
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return out_path
        time.sleep(0.05)
    raise RuntimeError(f"pyttsx3 did not produce audio at: {out_path}")
