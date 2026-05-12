"""Sample frames from a video to classify its format.

PPT screencasts, Zoom recordings, and talking-head videos need different
extraction strategies. This module produces sample JPGs that the user (or LLM
agent) can eyeball to decide.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .utils import banner, fmt_duration, ok, require_binary, video_duration

DEFAULT_SAMPLE_TIMES = [60, 300, 1800]  # 1m, 5m, 30m


def sample_frames(
    video: Path,
    out_dir: Path,
    times_sec: list[int] | None = None,
    width: int = 640,
) -> list[Path]:
    """Extract one frame at each timestamp. Returns list of created jpg paths.

    Times that exceed video duration are skipped silently.
    """
    require_binary("ffmpeg")
    out_dir.mkdir(parents=True, exist_ok=True)
    duration = video_duration(video)
    times = times_sec or DEFAULT_SAMPLE_TIMES

    written: list[Path] = []
    for t in times:
        if t >= duration:
            continue
        out = out_dir / f"sample_{video.stem[:20]}_{t:05d}.jpg"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(t),
                "-i",
                str(video),
                "-frames:v",
                "1",
                "-vf",
                f"scale={width}:-1",
                str(out),
            ],
            check=True,
            capture_output=True,
        )
        written.append(out)
    return written


def inspect_batch(batch_dir: Path, sample_dir: Path | None = None) -> dict:
    """Sample 3 frames from each mp4 in batch_dir. Print a report.

    Returns a dict {video_path: [sample_paths]}.
    """
    sample_dir = sample_dir or Path("/tmp/slidoc-samples")
    sample_dir.mkdir(parents=True, exist_ok=True)
    videos = sorted(batch_dir.glob("*.mp4"))
    if not videos:
        raise FileNotFoundError(f"No *.mp4 found in {batch_dir}")

    results = {}
    for v in videos:
        dur = video_duration(v)
        banner(f"{v.name}  ({fmt_duration(dur)})")
        samples = sample_frames(v, sample_dir)
        for s in samples:
            ok(f"  {s}")
        results[v] = samples
    print()
    print("Next step: open each sample and classify the video as:")
    print("  (A) PPT screencast              → slidoc frames <v> --mode scene")
    print("  (B) Zoom / busy multi-tile UI   → slidoc frames <v> --mode fps --interval 90")
    print("  (C) Pure talking-head, no slides → skip frames; use SRT only")
    return results
