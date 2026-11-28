"""FFmpeg-based video + soundtrack preview creation."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class PreviewError(RuntimeError):
    """Raised when media cannot be combined into a preview."""


def create_preview(video_bytes: bytes, audio_bytes: bytes, duration_seconds: float = 10.0) -> bytes:
    """Return MP4 bytes containing the source video and replacement soundtrack.

    The original video's audio is excluded. Video is trimmed to duration_seconds;
    audio is trimmed or padded with silence to match. Requires FFmpeg on PATH.
    """
    if not video_bytes or not audio_bytes:
        raise ValueError("Both video_bytes and audio_bytes must be nonempty.")
    if not 0 < duration_seconds <= 120:
        raise ValueError("duration_seconds must be between 0 and 120.")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise PreviewError("FFmpeg is not installed or is not on PATH.")

    with tempfile.TemporaryDirectory(prefix="scenesound_") as directory:
        root = Path(directory)
        video_path = root / "input_video"
        audio_path = root / "input_audio"
        output_path = root / "preview.mp4"
        video_path.write_bytes(video_bytes)
        audio_path.write_bytes(audio_bytes)
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(video_path), "-i", str(audio_path),
            "-map", "0:v:0", "-map", "1:a:0",
            "-t", str(duration_seconds),
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-af", f"apad=whole_dur={duration_seconds}",
            "-movflags", "+faststart", str(output_path),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
        except subprocess.TimeoutExpired as exc:
            raise PreviewError("FFmpeg timed out while rendering the preview.") from exc
        if result.returncode != 0 or not output_path.exists():
            raise PreviewError(f"FFmpeg failed: {result.stderr[-1200:]}")
        return output_path.read_bytes()
