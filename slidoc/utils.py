"""Shared utilities."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def fmt_ts(sec: float) -> str:
    """Seconds → HH:MM:SS."""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def is_newer(target: str | Path, *deps: str | Path) -> bool:
    """Return True if `target` exists and is newer than every existing dep."""
    target = Path(target)
    if not target.exists():
        return False
    t_mtime = target.stat().st_mtime
    for d in deps:
        d = Path(d)
        if d.exists() and d.stat().st_mtime > t_mtime:
            return False
    return True


def require_binary(name: str) -> str:
    """Return the absolute path of `name` or raise with a friendly message."""
    try:
        result = subprocess.run(["which", name], check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise RuntimeError(
            f"Required binary '{name}' not found on $PATH.\n"
            f"  Install it first (e.g. `brew install {name}` or apt/yum equivalent).\n"
            f"  For whisper-cli see https://github.com/ggerganov/whisper.cpp"
        ) from None


def parse_index_prefix(name: str) -> int | None:
    """Extract the leading integer index from 'N-title' / 'N. title' / 'N_title'."""
    m = re.match(r"(\d+)[.\-_ ]", name)
    return int(m.group(1)) if m else None


def detect_whisper_model(preferred: str | None = None) -> tuple[str, Path]:
    """Pick a whisper model file. Returns (label, path)."""
    cache = Path.home() / ".cache" / "whisper"
    candidates = {
        "large-v3": cache / "ggml-large-v3.bin",
        "medium": cache / "ggml-medium.bin",
        "small": cache / "ggml-small.bin",
        "base": cache / "ggml-base.bin",
    }
    if preferred and preferred in candidates:
        if candidates[preferred].exists():
            return preferred, candidates[preferred]
        raise FileNotFoundError(
            f"Model file not found: {candidates[preferred]}\n"
            f"  Download it from https://huggingface.co/ggerganov/whisper.cpp/tree/main"
        )
    for label, p in candidates.items():
        if p.exists():
            return label, p
    raise FileNotFoundError(
        f"No whisper model found in {cache}.\n"
        f"  Download e.g. ggml-medium.bin from "
        f"https://huggingface.co/ggerganov/whisper.cpp/tree/main"
    )


def video_duration(video: str | Path) -> float:
    """Return duration in seconds via ffprobe."""
    require_binary("ffprobe")
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def fmt_duration(sec: float) -> str:
    """Seconds → '1h33m' / '23m' / '45s'."""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    if h:
        return f"{h}h{m:02d}m"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def banner(msg: str) -> None:
    print(f"\033[1;36m▶ {msg}\033[0m", flush=True)


def warn(msg: str) -> None:
    print(f"\033[33m⚠ {msg}\033[0m", flush=True)


def ok(msg: str) -> None:
    print(f"\033[32m✓ {msg}\033[0m", flush=True)


def fail(msg: str) -> None:
    print(f"\033[31m✗ {msg}\033[0m", flush=True)
