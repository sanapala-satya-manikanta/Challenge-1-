"""
emotion_analyzer.py
--------------------
Detects granular emotions from text with intensity scoring.

Primary method: Hugging Face transformers (j-hartmann/emotion-english-distilroberta-base)
Fallback: VADER + keyword rules for offline/lightweight use.
"""

from typing import Dict

# ---------- Hugging Face path ----------
def _hf_analyze(text: str) -> Dict:
    from transformers import pipeline
    classifier = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=None
    )
    results = classifier(text)[0]  # list of {label, score}
    # Map HF labels → our canonical emotions
    LABEL_MAP = {
        "joy":     "happy",
        "anger":   "angry",
        "sadness": "sad",
        "fear":    "fearful",
        "surprise":"surprised",
        "disgust": "frustrated",
        "neutral": "neutral",
    }
    top = max(results, key=lambda x: x["score"])
    emotion = LABEL_MAP.get(top["label"].lower(), "neutral")
    intensity = float(top["score"])

    # Refine: detect "excited" vs plain "happy" by intensity + exclamation marks
    if emotion == "happy" and (intensity > 0.80 or text.count("!") >= 2):
        emotion = "excited"
    # Detect inquisitive
    if text.strip().endswith("?") and emotion in ("neutral", "surprised"):
        emotion = "inquisitive"
    # Detect concerned
    if emotion in ("fearful", "sad") and any(w in text.lower() for w in ["worry", "concerned", "hope", "please"]):
        emotion = "concerned"

    return {"emotion": emotion, "intensity": round(intensity, 3)}


# ---------- VADER fallback path ----------
def _vader_analyze(text: str) -> Dict:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]

    # Keyword-based granular detection
    text_lower = text.lower()
    exclamations = text.count("!")
    questions = text.count("?")

    # Determine base emotion
    if compound >= 0.6:
        emotion = "excited" if exclamations >= 2 or compound > 0.8 else "happy"
        intensity = min(0.5 + compound * 0.5, 1.0)
    elif compound >= 0.1:
        if questions > 0:
            emotion = "inquisitive"
        else:
            emotion = "happy"
        intensity = 0.4 + compound * 0.3
    elif compound <= -0.6:
        angry_words = ["hate", "furious", "rage", "angry", "terrible", "awful"]
        frustrated_words = ["frustrated", "ugh", "annoying", "waste", "useless"]
        if any(w in text_lower for w in angry_words):
            emotion = "angry"
        elif any(w in text_lower for w in frustrated_words):
            emotion = "frustrated"
        else:
            emotion = "sad"
        intensity = min(0.5 + abs(compound) * 0.5, 1.0)
    elif compound <= -0.1:
        concern_words = ["worry", "concerned", "afraid", "scared", "nervous"]
        if any(w in text_lower for w in concern_words):
            emotion = "concerned"
        elif any(w in text_lower for w in ["fear", "terrified", "panic"]):
            emotion = "fearful"
        else:
            emotion = "sad"
        intensity = 0.3 + abs(compound) * 0.4
    else:
        if questions > 0:
            emotion = "inquisitive"
        elif any(w in text_lower for w in ["wow", "whoa", "really", "no way", "oh my"]):
            emotion = "surprised"
        else:
            emotion = "neutral"
        intensity = 0.3 + abs(compound) * 0.2

    return {"emotion": emotion, "intensity": round(intensity, 3)}


# ---------- Public interface ----------
def analyze_emotion(text: str) -> Dict:
    """
    Returns dict: { "emotion": str, "intensity": float (0-1) }

    Tries HuggingFace first; falls back to VADER if unavailable.
    """
    try:
        return _hf_analyze(text)
    except Exception:
        pass
    try:
        return _vader_analyze(text)
    except Exception:
        pass
    # Last resort
    return {"emotion": "neutral", "intensity": 0.5}
