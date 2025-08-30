#!/usr/bin/env python3
import sys
from pathlib import Path
import argparse

# make sure ../text2audio is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from text2audio.core import synthesize  # adjust import if synthesize is in another file


def main():
    parser = argparse.ArgumentParser(description="Run TTS synthesis with selectable backend.")
    parser.add_argument("--text", required=True, help="Text to synthesize.")
    parser.add_argument("--backend", choices=["gtts", "pyttsx3", "piper"], default="gtts")
    parser.add_argument("--lang", default="en", help="Language code (default: en).")
    parser.add_argument("--out", default="out.mp3", help="Output file path.")

    # Piper-only args
    parser.add_argument("--piper_model", help="Piper model short key or path.")
    parser.add_argument("--length_scale", type=float, default=None)
    parser.add_argument("--noise_scale", type=float, default=None)
    parser.add_argument("--noise_w", type=float, default=None)

    args = parser.parse_args()

    result_path = synthesize(
        text=args.text,
        backend=args.backend,
        lang=args.lang,
        out=args.out,
        piper_model=args.piper_model,
        length_scale=args.length_scale,
        noise_scale=args.noise_scale,
        noise_w=args.noise_w,
    )

    print(f"✅ Synthesis complete. File saved to: {result_path}")


if __name__ == "__main__":
    main()
