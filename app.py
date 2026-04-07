from flask import Flask, request, jsonify, send_file, render_template_string
import os
import uuid
import json
from emotion_analyzer import analyze_emotion
from tts_engine import synthesize_speech

app = Flask(__name__)
AUDIO_DIR = "audio_output"
os.makedirs(AUDIO_DIR, exist_ok=True)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Empathy Engine</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --card: #1a1a26;
    --border: #2a2a3d;
    --accent: #7c6af7;
    --accent2: #f76a8c;
    --accent3: #6af7c8;
    --text: #e8e8f0;
    --muted: #7070a0;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 20px;
  }
  .bg-orb {
    position: fixed; border-radius: 50%; filter: blur(120px); pointer-events: none; z-index: 0;
  }
  .orb1 { width: 500px; height: 500px; background: rgba(124,106,247,0.12); top: -100px; left: -100px; }
  .orb2 { width: 400px; height: 400px; background: rgba(247,106,140,0.08); bottom: 0; right: -50px; }
  .container { max-width: 760px; width: 100%; position: relative; z-index: 1; }
  h1 {
    font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2.8rem;
    background: linear-gradient(135deg, #7c6af7, #f76a8c, #6af7c8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    text-align: center; margin-bottom: 8px;
  }
  .subtitle { text-align: center; color: var(--muted); margin-bottom: 40px; font-size: 1rem; }
  .card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 20px; padding: 32px; margin-bottom: 24px;
  }
  label { font-size: 0.85rem; color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase; display: block; margin-bottom: 10px; }
  textarea {
    width: 100%; background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; color: var(--text); font-family: 'DM Sans', sans-serif;
    font-size: 1rem; padding: 16px; resize: vertical; min-height: 120px;
    outline: none; transition: border-color 0.2s;
  }
  textarea:focus { border-color: var(--accent); }
  .btn {
    width: 100%; padding: 16px; border-radius: 12px; border: none; cursor: pointer;
    font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1rem;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: white; margin-top: 16px; transition: opacity 0.2s, transform 0.1s;
    letter-spacing: 0.04em;
  }
  .btn:hover { opacity: 0.9; transform: translateY(-1px); }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
  .result { display: none; }
  .emotion-badge {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 8px 16px; border-radius: 999px; font-size: 0.9rem; font-weight: 500;
    margin-bottom: 20px;
  }
  .emotion-dot { width: 10px; height: 10px; border-radius: 50%; }
  .params-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
  .param-box {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px; text-align: center;
  }
  .param-label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }
  .param-value { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 700; color: var(--accent3); margin-top: 4px; }
  audio { width: 100%; border-radius: 10px; margin-top: 4px; }
  .loading { text-align: center; color: var(--muted); padding: 20px; display: none; }
  .spinner {
    width: 36px; height: 36px; border: 3px solid var(--border);
    border-top-color: var(--accent); border-radius: 50%;
    animation: spin 0.8s linear infinite; margin: 0 auto 12px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .intensity-bar-bg { background: var(--surface); border-radius: 999px; height: 8px; margin-top: 12px; }
  .intensity-bar { height: 8px; border-radius: 999px; background: linear-gradient(90deg, var(--accent), var(--accent2)); transition: width 0.6s ease; }
  .intensity-label { font-size: 0.8rem; color: var(--muted); margin-top: 6px; }
  .error { color: var(--accent2); font-size: 0.9rem; margin-top: 10px; display: none; }
</style>
</head>
<body>
<div class="bg-orb orb1"></div>
<div class="bg-orb orb2"></div>
<div class="container">
  <h1>🎙 Empathy Engine</h1>
  <p class="subtitle">Dynamic emotion-aware speech synthesis</p>

  <div class="card">
    <label>Input Text</label>
    <textarea id="inputText" placeholder="Type something expressive... e.g. 'I just got the promotion! This is the best day of my life!'"></textarea>
    <button class="btn" id="generateBtn" onclick="generate()">Generate Emotional Speech</button>
    <div class="error" id="errorMsg"></div>
  </div>

  <div class="loading" id="loading">
    <div class="spinner"></div>
    <p>Analyzing emotion & synthesizing voice...</p>
  </div>

  <div class="card result" id="result">
    <label>Detected Emotion</label>
    <div id="emotionBadge" class="emotion-badge"></div>

    <label>Intensity</label>
    <div class="intensity-bar-bg">
      <div class="intensity-bar" id="intensityBar" style="width:0%"></div>
    </div>
    <div class="intensity-label" id="intensityLabel"></div>

    <br>
    <label>Voice Parameters</label>
    <div class="params-grid">
      <div class="param-box">
        <div class="param-label">Rate</div>
        <div class="param-value" id="paramRate">—</div>
      </div>
      <div class="param-box">
        <div class="param-label">Pitch</div>
        <div class="param-value" id="paramPitch">—</div>
      </div>
      <div class="param-box">
        <div class="param-label">Volume</div>
        <div class="param-value" id="paramVolume">—</div>
      </div>
    </div>

    <label>Audio Output</label>
    <audio id="audioPlayer" controls></audio>
  </div>
</div>

<script>
const EMOTION_COLORS = {
  happy:      { bg: 'rgba(106,247,160,0.15)', border: '#6af7a0', dot: '#6af7a0', label: '😄 Happy' },
  excited:    { bg: 'rgba(247,200,106,0.15)', border: '#f7c86a', dot: '#f7c86a', label: '🤩 Excited' },
  sad:        { bg: 'rgba(106,160,247,0.15)', border: '#6aa0f7', dot: '#6aa0f7', label: '😔 Sad' },
  angry:      { bg: 'rgba(247,106,106,0.15)', border: '#f76a6a', dot: '#f76a6a', label: '😠 Angry' },
  frustrated: { bg: 'rgba(247,150,106,0.15)', border: '#f7966a', dot: '#f7966a', label: '😤 Frustrated' },
  fearful:    { bg: 'rgba(200,106,247,0.15)', border: '#c86af7', dot: '#c86af7', label: '😨 Fearful' },
  surprised:  { bg: 'rgba(247,247,106,0.15)', border: '#f7f76a', dot: '#f7f76a', label: '😲 Surprised' },
  inquisitive:{ bg: 'rgba(106,220,247,0.15)', border: '#6adcf7', dot: '#6adcf7', label: '🤔 Inquisitive' },
  concerned:  { bg: 'rgba(247,180,106,0.15)', border: '#f7b46a', dot: '#f7b46a', label: '😟 Concerned' },
  neutral:    { bg: 'rgba(150,150,180,0.15)', border: '#9696b4', dot: '#9696b4', label: '😐 Neutral' },
};

async function generate() {
  const text = document.getElementById('inputText').value.trim();
  if (!text) return;
  document.getElementById('generateBtn').disabled = true;
  document.getElementById('loading').style.display = 'block';
  document.getElementById('result').style.display = 'none';
  document.getElementById('errorMsg').style.display = 'none';

  try {
    const res = await fetch('/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Unknown error');

    const ec = EMOTION_COLORS[data.emotion] || EMOTION_COLORS.neutral;
    const badge = document.getElementById('emotionBadge');
    badge.style.background = ec.bg;
    badge.style.border = `1px solid ${ec.border}`;
    badge.innerHTML = `<span class="emotion-dot" style="background:${ec.dot}"></span>${ec.label}`;

    const pct = Math.round(data.intensity * 100);
    document.getElementById('intensityBar').style.width = pct + '%';
    document.getElementById('intensityLabel').textContent = `Intensity: ${pct}%`;

    document.getElementById('paramRate').textContent = data.params.rate;
    document.getElementById('paramPitch').textContent = data.params.pitch;
    document.getElementById('paramVolume').textContent = data.params.volume;

    const audio = document.getElementById('audioPlayer');
    audio.src = data.audio_url + '?t=' + Date.now();
    audio.load();

    document.getElementById('result').style.display = 'block';
  } catch (e) {
    document.getElementById('errorMsg').textContent = 'Error: ' + e.message;
    document.getElementById('errorMsg').style.display = 'block';
  } finally {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('generateBtn').disabled = false;
  }
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/synthesize", methods=["POST"])
def synthesize():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400
    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400

    emotion_result = analyze_emotion(text)
    filename = f"{uuid.uuid4().hex}.wav"
    filepath = os.path.join(AUDIO_DIR, filename)
    params = synthesize_speech(text, emotion_result, filepath)

    return jsonify({
        "emotion": emotion_result["emotion"],
        "intensity": emotion_result["intensity"],
        "params": params,
        "audio_url": f"/audio/{filename}"
    })

@app.route("/audio/<filename>")
def serve_audio(filename):
    filepath = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, mimetype="audio/wav")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
