# DevSentinel MVP

A first **working**, free developer troubleshooting app. Supports pasted logs, uploaded `.txt/.log` files, PNG/JPEG screenshot OCR, classification with deterministic rules, local reference snippets, and downloadable redacted report. **It does not use an LLM yet.**

## Requirements
Python **3.12** recommended, especially if you previously had PyArrow installation errors using Python 3.14. Linux/macOS; Windows works if Tesseract is installed separately.

## GitHub Codespaces / Ubuntu

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --only-binary=:all: -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app.py --server.address 0.0.0.0
```

If Python 3.12 isn't installed, use an available supported version (3.11–3.15) with a working wheel for the pinned dependencies. In Codespaces, use the **Ports** tab to open port 8501.

## macOS

```bash
brew install tesseract
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --only-binary=:all: -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app.py
```

## Offline test (no app dependencies needed)

```bash
python -m unittest discover -s tests -v
```

## Example
Paste `ERROR: Failed building wheel for pyarrow` and click Investigate. The application finds a dependency build error and suggests checking Python compatibility and binary wheels.

## Honest limitations
- Rules catch only known patterns; this isn't genuine root-cause verification.
- The knowledge search is keyword-based, **not** embedding RAG yet.
- OCR requires the separate native Tesseract binary and is not a multimodal foundation model.
- Automatically redacting all kinds of private tokens is impossible; don't upload real secrets.
- No audio, video, live GitHub integration, automated patch application or execution yet.
- Never expose this MVP directly on a public internet port with sensitive data: it has no login or authorization.

## Upgrade architecture
FastAPI backend → authenticated orchestrator → [Log Agent, Vision OCR Agent, Audio Whisper Agent, Video Frame Agent, Repo RAG Agent] → evidence scoring → user-reviewed suggested fix → sandbox test results. Add explicit authorization checks for every tool.

## NEW: Screen recording analysis (Version 1.1)
Upload an `.mp4`, `.mov`, or `.webm` screen recording (at most **30 MB and 2 minutes**). DevSentinel samples 2–8 frames evenly across the clip, displays a timestamped timeline, uses local Tesseract OCR on each frame, and combines the recognized error text with logs and screenshots in the existing investigation report. It does **not** listen to the recording's audio, track cursor interactions, or run a video foundation model yet. OCR on moving/blurred UI may miss errors; capture a clear frame if possible.

Install ffmpeg as well as Tesseract:

Ubuntu/Codespaces:
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg tesseract-ocr
```

macOS:
```bash
brew install ffmpeg tesseract
```

The app uses only standard Python, Pillow, ffmpeg, and Tesseract for the video feature (no new pip dependencies). Video files and extracted frames are stored in a temporary directory and removed after processing. Do not expose this app publicly; its demo UI does not include authentication. Recording contents may contain secrets; review material before upload. The report attempts to redact common secret patterns but cannot guarantee complete removal.
