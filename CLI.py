"""
cli.py  —  Command-line interface for the Empathy Engine
Usage:
    python cli.py "Your text here"
    python cli.py  (interactive mode)
"""

import sys
import os
import uuid
from emotion_analyzer import analyze_emotion
from tts_engine import synthesize_speech

def run(text: str):
    print(f"\n📝 Input: {text}")
    print("🔍 Analyzing emotion...", end=" ", flush=True)
    result = analyze_emotion(text)
    print(f"done.")
    print(f"🎭 Emotion  : {result['emotion'].upper()}  (intensity {result['intensity']*100:.0f}%)")

    out_dir = "audio_output"
    os.makedirs(out_dir, exist_ok=True)
    filename = os.path.join(out_dir, f"{uuid.uuid4().hex}.wav")

    print("🔊 Synthesizing speech...", end=" ", flush=True)
    params = synthesize_speech(text, result, filename)
    print("done.")
    print(f"🎚  Rate: {params['rate']}  |  Pitch: {params['pitch']}  |  Volume: {params['volume']}")
    print(f"💾 Saved: {filename}")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run(" ".join(sys.argv[1:]))
    else:
        print("🎙  Empathy Engine — Interactive Mode (Ctrl+C to quit)\n")
        while True:
            try:
                text = input("Enter text: ").strip()
                if text:
                    run(text)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
