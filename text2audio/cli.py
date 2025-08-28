import sys
import argparse
from pathlib import Path
from .core import synthesize

def main():
    ap = argparse.ArgumentParser(description="Text → Audio")
    ap.add_argument("-t", "--text", help="Text to speak. If omitted, read from stdin.", default=None)
    ap.add_argument("-f", "--file", help="Read text from file.", default=None)
    ap.add_argument("-b", "--backend", choices=["gtts", "pyttsx3"], default="gtts")
    ap.add_argument("-l", "--lang", default="en", help="Language code (e.g., en, de, fr).")
    ap.add_argument("-o", "--out", default="out.mp3", help="Output path (.mp3 for gTTS, .wav for pyttsx3).")
    args = ap.parse_args()

    if args.text is None and args.file is None:
        text = sys.stdin.read()
    elif args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        text = args.text

    if not text.strip():
        print("No text provided.", file=sys.stderr)
        sys.exit(1)

    out_path = synthesize(text, backend=args.backend, lang=args.lang, out=args.out)
    print(out_path)

if __name__ == "__main__":
    main()
