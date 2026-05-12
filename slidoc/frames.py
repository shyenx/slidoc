"""Keyframe extraction (stage ①).

Two modes:
- `scene`: ffmpeg scene-detect filter. Best for clean PPT screencasts where
  slide changes produce large pixel deltas.
- `fps`: fixed-interval sampling. Best for Zoom-style recordings with moving
  chat sidebars / webcam tiles that defeat scene-detect.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .utils import banner, ok, require_binary, warn


def extract_keyframes(
    video: Path,
    out_dir: Path,
    mode: str = "scene",
    scene_threshold: float = 0.30,
    fps_interval: int = 90,
    width: int = 1280,
    quality: int = 3,
) -> tuple[int, Path]:
    """Extract frames + ffmpeg showinfo log.

    Returns (frame_count, frame_log_path).
    """
    require_binary("ffmpeg")
    out_dir.mkdir(parents=True, exist_ok=True)
    fdir = out_dir / "frames"
    fdir.mkdir(exist_ok=True)
    log = out_dir / "frame_log.txt"

    # Clean previous run
    for p in fdir.glob("*.jpg"):
        p.unlink()
    if log.exists():
        log.unlink()

    if mode == "scene":
        vf = f"select='gt(scene,{scene_threshold})',showinfo,scale={width}:-1"
    elif mode == "fps":
        vf = f"fps=1/{fps_interval},showinfo,scale={width}:-1"
    else:
        raise ValueError(f"Unknown mode {mode!r}; expected 'scene' or 'fps'")

    banner(f"extract [{mode}] → {fdir}")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-vf", vf,
        "-q:v", str(quality),
    ]
    if mode == "scene":
        cmd += ["-vsync", "vfr"]
    cmd += [str(fdir / "f_%04d.jpg")]

    with open(log, "wb") as logf:
        subprocess.run(cmd, check=True, stderr=logf, stdout=subprocess.DEVNULL)

    count = len(list(fdir.glob("*.jpg")))
    ok(f"{count} frames")

    # Heuristic hints
    if mode == "scene":
        if count > 200:
            warn(
                f"{count} frames — too many. Raise threshold (try {scene_threshold + 0.10:.2f})."
            )
        elif count < 10:
            warn(
                f"{count} frames — too few. Lower threshold (try {max(0.10, scene_threshold - 0.10):.2f}) "
                "OR switch to --mode fps."
            )

    return count, log
