# DevSentinel MVP specification

## Goal
Help developers investigate common technical errors from log/text or screenshots, offline. A fast and explainable prototype, *not* yet a multimodal transformer or autonomous agent.

## Inputs and modality roles
- **Text / logs:** primary source of exception details and stack traces.
- **Images:** OCR extracts text from screenshots using local Tesseract.
- **Audio:** future Whisper-based transcription of bug reports.
- **Video:** future frame sampling plus OCR and optional audio transcription.

## MVP pipeline
Input → redaction → optional OCR → deterministic pattern-matching → local keyword knowledge retrieval → readable report. No code execution or file writes except user-initiated report download.

## Success criteria / evaluation plan
- All included rule-based regression tests pass.
- Known example logs classified into expected categories, with no invented confidence probability.
- OCR succeeds for 80% or more of a *future, labeled screenshot dataset*; not yet measured.
- 95% of benchmark requests below two seconds without OCR; not yet measured.
- Never execute or deploy generated code.

## Failure modes
Missing Tesseract binary, illegible text, truncated logs, non-English UI, ambiguous errors, unmatched patterns, secrets embedded in screenshots, and incomplete context. Redaction is best-effort only.

## Roadmap
1. MVP: local logs/screenshot OCR + rules + markdown report.
2. RAG: local repository/document embeddings with source links, permission checks, and evaluation corpus.
3. Audio: Whisper speech transcription.
4. Video: sampled frames with OCR, timestamps and audio track.
5. Agents: planner with tightly permissioned search and test tools, sandbox execution with explicit approval, verified evidence citations.
6. Transformers foundations: a separate, educational CPU-friendly folder for attention, patch tokens, and toy models; no effect on initial product accuracy.

## Security
No remote LLM calls; no file URL fetching; no executing uploaded code; no secrets stored intentionally; OCR strictly size-limited; enforce real authentication and storage controls before deploying for teams.

## Video analysis extension (v1.1)
- Input: MP4/MOV/WEBM screen recording (30 MB, 120 s maximum).
- Technique: ffprobe validation, ffmpeg timestamp sampling (2–8 frames), local Tesseract OCR, deterministic error classification and timestamped report evidence.
- Does not analyze audio, cursor movements, or every frame; error events between sampled frames may be missed.
- Safety: subprocess commands use static argv without a shell, temporary files are deleted, and no source code is executed.
