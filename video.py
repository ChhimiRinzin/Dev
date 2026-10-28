"""Bounded, offline extraction of representative frames from screen recordings.

No media content is interpreted as commands. ffmpeg/ffprobe are invoked without shell.
"""
from __future__ import annotations
from dataclasses import dataclass
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from PIL import Image

MAX_BYTES = 30_000_000
MAX_DURATION = 120.0
MAX_FRAMES = 8

@dataclass(frozen=True)
class VideoFrame:
    seconds: float
    png: bytes

@dataclass(frozen=True)
class VideoResult:
    duration: float
    frames: tuple[VideoFrame, ...]

def sample_video(data: bytes, *, frame_count: int = 6) -> VideoResult:
    if not data or len(data) > MAX_BYTES:
        raise ValueError('Video must be nonempty and at most 30 MB.')
    if not 1 <= frame_count <= MAX_FRAMES:
        raise ValueError('Choose between 1 and 8 frames.')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise RuntimeError('ffmpeg and ffprobe must be installed (see README).')
    with tempfile.TemporaryDirectory(prefix='devsentinel_video_') as tmp:
        source = Path(tmp) / 'upload.mp4'
        source.write_bytes(data)
        info = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'format=duration:stream=width,height',
             '-of', 'json', str(source)], capture_output=True, timeout=15, check=False)
        if info.returncode != 0:
            raise ValueError('Unable to read video. Check file encoding or format.')
        try:
            meta = json.loads(info.stdout)
            duration = float(meta['format']['duration'])
            streams = meta['streams']
            width, height = int(streams[0]['width']), int(streams[0]['height'])
        except (KeyError, ValueError, TypeError, IndexError, OverflowError) as exc:
            raise ValueError('Video metadata is missing or invalid.') from exc
        if not 0 < duration <= MAX_DURATION:
            raise ValueError('Video must be at most 120 seconds long.')
        if width < 1 or height < 1 or width * height > 16_000_000:
            raise ValueError('Video resolution is unsupported or too large.')
        # Spread frames across the recording, skipping exact endpoints.
        times = [round(duration * (i + 1) / (frame_count + 1), 3) for i in range(frame_count)]
        frames = []
        for i, timestamp in enumerate(times):
            target = Path(tmp) / f'frame_{i}.png'
            cmd = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error',
                   '-ss', str(timestamp), '-i', str(source), '-frames:v', '1',
                   '-vf', 'scale=960:540:force_original_aspect_ratio=decrease',
                   '-y', str(target)]
            result = subprocess.run(cmd, capture_output=True, timeout=18, check=False)
            if result.returncode != 0 or not target.exists():
                continue
            with Image.open(target) as image:
                image.verify()
            png = target.read_bytes()
            if len(png) <= 4_000_000:
                frames.append(VideoFrame(timestamp, png))
        if not frames:
            raise ValueError('No frames could be decoded from this video.')
        return VideoResult(duration, tuple(frames))

def inspect_video(data: bytes, *, frame_count: int = 6):
    """Returns video metadata, timestamped redacted OCR, and analyzable text."""
    from devsentinel.ocr import extract_screenshot
    from devsentinel.analyzer import redact
    sampled = sample_video(data, frame_count=frame_count)
    evidence = []
    for frame in sampled.frames:
        try:
            text = redact(extract_screenshot(frame.png))
        except (RuntimeError, ValueError, OSError, TimeoutError) as exc:
            text = f'[OCR unavailable: {type(exc).__name__}]'
        evidence.append((frame, text[:3000]))
    merged = '\n'.join(f'[Video {frame.seconds:.1f}s]\n{text}' for frame, text in evidence)
    return sampled, evidence, merged
