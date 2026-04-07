# 🖼 Pitch Visualizer

> From narrative text to a cinematic, multi-panel visual storyboard — instantly.

## What It Does

The Pitch Visualizer takes any story or pitch narrative and:
1. **Segments** it into logical scenes using NLP (spaCy / NLTK)
2. **Engineers** rich, visually descriptive prompts for each scene via LLM (Claude) or rule-based expansion
3. **Generates** a unique AI image per scene
4. **Presents** a polished, interactive storyboard with panel-by-panel animated reveal

---

## Setup

### 1. Clone & create environment
```bash
git clone https://github.com/your-username/pitch-visualizer.git
cd pitch-visualizer
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Configure API keys (optional but recommended)

Create a `.env` file or export environment variables:

```bash
# For best image quality (DALL-E 3):
export OPENAI_API_KEY=sk-...

# OR Stability AI:
export STABILITY_API_KEY=sk-...

# For LLM-powered prompt engineering:
export ANTHROPIC_API_KEY=sk-ant-...

# If none are set, the app falls back to Pollinations.ai (free, no key needed)
```

### 4. Run
```bash
python app.py
# Open http://localhost:5001
```

---

## Architecture & Design Choices

### Text Segmentation
Uses **spaCy**'s linguistic sentence boundary detection (falls back to NLTK, then regex split). Short fragments are merged with the previous segment to avoid overly sparse panels.

### Prompt Engineering — the core of the challenge
This is where raw sentences are transformed into visually rich image prompts.

**LLM path (primary):** Claude Haiku is given a system prompt instructing it to act as an image prompt engineer. It receives the original sentence + desired style and returns a cinematically detailed prompt. This produces the most coherent, creative results.

**Rule-based path (fallback):** Keyword → mood mapping extracts descriptive adjectives from the sentence ("drowning" → "overwhelming chaos, cluttered"). Camera angle varies by scene index for visual variety. Style is woven throughout.

Example transformation:
- **Input**: *"Sarah's company was drowning in paperwork."*
- **Engineered prompt**: *"Cinematic photorealistic, wide establishing shot, overwhelmed office worker surrounded by towering stacks of paper, harsh fluorescent lighting, desaturated tones, documentary photography style, shallow depth of field, 8K resolution"*

### Image Generation (3-tier)
1. **DALL-E 3** — best quality, wide range of styles
2. **Stability AI SDXL** — local file storage, high control
3. **Pollinations.ai** — completely free fallback, no API key required

### Visual Consistency
Style keywords are appended to every prompt to maintain visual coherence across panels. Users can select from 5 styles: Cinematic, Digital Art, Watercolor, Corporate, or Noir.

### Bonus Features Implemented
- ✅ **User-selectable styles**: 5 visual styles
- ✅ **LLM-powered prompt refinement**: Claude Haiku integration
- ✅ **Dynamic UI**: Panels appear one by one with animation
- ✅ **Visual consistency**: Style injected into every prompt
- ✅ **Prompt transparency**: Each panel shows its engineered prompt on demand

---

## Project Structure
```
pitch_visualizer/
├── app.py               # Flask server + HTML/JS UI
├── segmenter.py         # NLP-based text segmentation
├── prompt_engineer.py   # LLM + rule-based prompt generation
├── image_generator.py   # DALL-E / Stability / Pollinations backends
├── requirements.txt
└── static/generated/    # Locally saved images (Stability path)
```
