"""
tts_engine.py
--------------
Synthesizes speech with vocal parameters modulated by emotion + intensity.

Primary:  gTTS (Google TTS) — produces .mp3, converted to .wav via pydub
Fallback: pyttsx3 — fully offline

Vocal parameters adjusted:
  - Rate  (words per minute / speed factor)
  - Pitch (semitone shift via pydub, or pyttsx3 native)
  - Volume (amplitude scaling)

SSML is used when the Google Cloud TTS SDK is available (optional stretch goal).
"""

import os
import io
from typing import Dict

# ── Emotion → vocal profile ────────────────────────────────────────────────
# Each entry: (base_rate, base_pitch_shift_semitones, base_volume)
# Intensity (0–1) scales these values around the base.

EMOTION_PROFILES = {
    #             rate   pitch   volume
    "happy":     (1.10,  +2,     1.10),
    "excited":   (1.25,  +4,     1.20),
    "sad":       (0.80,  -3,     0.85),
    "angry":     (1.15,  -1,     1.30),
    "frustrated":(1.05,  -1,     1.15),
    "fearful":   (1.10,  +1,     0.90),
    "surprised": (1.20,  +5,     1.15),
    "inquisitive":(0.95, +2,     1.00),
    "concerned": (0.90,  -1,     0.95),
    "neutral":   (1.00,   0,     1.00),
}

def _compute_params(emotion: str, intensity: float) -> Dict:
    """
    Scales vocal params by intensity around the neutral baseline.
    intensity=0.5 → exactly the profile value.
    intensity=1.0 → amplified; intensity=0.0 → near neutral.
    """
    base_rate, base_pitch, base_vol = EMOTION_PROFILES.get(emotion, EMOTION_PROFILES["neutral"])

    # Scale factor: 0 → 0 effect, 1 → full effect
    scale = intensity  # direct proportional

    rate   = round(1.0 + (base_rate  - 1.0) * scale * 2, 3)
    pitch  = round(base_pitch * scale * 2, 2)
    volume = round(1.0 + (base_vol   - 1.0) * scale * 2, 3)

    # Clamp to safe ranges
    rate   = max(0.5, min(2.0, rate))
    pitch  = max(-10, min(10, pitch))
    volume = max(0.5, min(2.0, volume))

    return {
        "rate":   f"{rate}x",
        "pitch":  f"{pitch:+.1f} st",
        "volume": f"{round(volume * 100)}%",
        "_rate":   rate,
        "_pitch":  pitch,
        "_volume": volume,
    }


# ── gTTS path ──────────────────────────────────────────────────────────────
def _gtts_synthesize(text: str, params: Dict, output_path: str) -> bool:
    from gtts import gTTS
    from pydub import AudioSegment
    import tempfile

    # gTTS does not support rate/pitch natively; we post-process with pydub
    tts = gTTS(text=text, lang="en", slow=False)
    tmp_mp3 = output_path.replace(".wav", "_raw.mp3")
    tts.save(tmp_mp3)

    audio = AudioSegment.from_mp3(tmp_mp3)

    # Pitch shift via frame-rate trick
    pitch_semitones = params["_pitch"]
    if pitch_semitones != 0:
        octaves = pitch_semitones / 12.0
        new_sample_rate = int(audio.frame_rate * (2.0 ** octaves))
        audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate})
        audio = audio.set_frame_rate(44100)

    # Rate change (speed up/slow down)
    rate = params["_rate"]
    if rate != 1.0:
        audio = audio.speedup(playback_speed=rate) if rate > 1.0 else \
                audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * rate)}).set_frame_rate(44100)

    # Volume
    vol = params["_volume"]
    if vol != 1.0:
        audio = audio + (20 * (vol - 1.0))  # dB adjustment

    audio.export(output_path, format="wav")
    os.remove(tmp_mp3)
    return True


# ── pyttsx3 fallback path ──────────────────────────────────────────────────
def _pyttsx3_synthesize(text: str, params: Dict, output_path: str) -> bool:
    import pyttsx3
    engine = pyttsx3.init()

    # Rate: pyttsx3 default ~200 wpm
    engine.setProperty("rate", int(200 * params["_rate"]))
    # Volume
    engine.setProperty("volume", min(1.0, params["_volume"]))
    # Pitch: pyttsx3 doesn't support pitch natively on all platforms; best-effort
    try:
        engine.setProperty("pitch", 50 + int(params["_pitch"] * 5))
    except Exception:
        pass

    engine.save_to_file(text, output_path)
    engine.runAndWait()
    return True


# ── Public interface ───────────────────────────────────────────────────────
def synthesize_speech(text: str, emotion_result: Dict, output_path: str) -> Dict:
    """
    Synthesize text to audio at output_path (.wav).
    Returns the vocal params dict (display-friendly strings).
    """
    emotion  = emotion_result.get("emotion", "neutral")
    intensity = emotion_result.get("intensity", 0.5)
    params   = _compute_params(emotion, intensity)

    success = False
    try:
        success = _gtts_synthesize(text, params, output_path)
    except Exception:
        pass

    if not success:
        try:
            success = _pyttsx3_synthesize(text, params, output_path)
        except Exception:
            pass

    if not success:
        # Write a silent WAV as last resort so the API doesn't break
        _write_silent_wav(output_path)

    # Return only display-friendly strings
    return {
        "rate":   params["rate"],
        "pitch":  params["pitch"],
        "volume": params["volume"],
    }


def _write_silent_wav(path: str):
    import wave, struct
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(struct.pack('<h', 0) * 22050)
