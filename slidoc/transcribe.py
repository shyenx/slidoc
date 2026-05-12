"""SRT transcription via whisper.cpp (stage ②).

Includes a quality gate that detects Whisper hallucination loops and recommends
an automatic retry with `large-v3` and anti-hallucination flags.
"""
from __future__ import annotations

import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from .utils import banner, detect_whisper_model, fail, ok, require_binary, warn

# Compression / entropy / logprob thresholds for whisper.cpp.
# Lower → more aggressive fallback to higher temperature, suppressing repetition.
LARGE_V3_ANTIHALLUC = ["-et", "2.0", "-lpt", "-0.8", "-mc", "2.0"]

UNIQUE_RATIO_FAIL = 0.80
TOP_REPEAT_WARN = 100


def _extract_text_lines(srt: Path) -> list[str]:
    """Return only the text lines (skip index, timestamp, blanks)."""
    out: list[str] = []
    with open(srt, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s.isdigit():
                continue
            if "-->" in s:
                continue
            out.append(s)
    return out


def quality_report(srt: Path) -> dict:
    """Compute unique-line ratio + top repeated lines from an SRT."""
    lines = _extract_text_lines(srt)
    total = len(lines)
    unique = len(set(lines))
    counter = Counter(lines)
    top = counter.most_common(3)
    return {
        "total": total,
        "unique": unique,
        "ratio": (unique / total) if total else 0.0,
        "top_repeated": top,
    }


def _extract_wav(video: Path) -> Path:
    """Extract 16kHz mono pcm wav for whisper input. Caller deletes."""
    require_binary("ffmpeg")
    fd, path = tempfile.mkstemp(prefix="slidoc_", suffix=".wav")
    Path(path).unlink()  # close handle, ffmpeg will write
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video),
            "-ar", "16000", "-ac", "1",
            "-c:a", "pcm_s16le",
            path,
        ],
        check=True, capture_output=True,
    )
    return Path(path)


def transcribe(
    video: Path,
    out_dir: Path,
    basename: str,
    model: str = "medium",
    language: str = "zh",
) -> tuple[Path, dict]:
    """Run whisper-cli, return (srt_path, quality_report).

    If model == "large-v3", anti-hallucination flags are applied.
    """
    require_binary("whisper-cli")
    label, model_path = detect_whisper_model(model)
    out_dir.mkdir(parents=True, exist_ok=True)
    srt = out_dir / f"{basename}.srt"

    banner(f"transcribe {video.name} → {srt.name} (model={label})")
    wav = _extract_wav(video)
    try:
        cmd = [
            "whisper-cli",
            "-m", str(model_path),
            "-l", language,
            "-osrt",
            "-of", str(out_dir / basename),
        ]
        if label == "large-v3":
            cmd += LARGE_V3_ANTIHALLUC
        cmd.append(str(wav))
        subprocess.run(cmd, check=True)
    finally:
        wav.unlink(missing_ok=True)

    qr = quality_report(srt)
    return srt, qr


def report_quality(qr: dict, name: str, current_model: str) -> bool:
    """Pretty-print quality report. Return True if passes, False if should retry."""
    pct = qr["ratio"] * 100
    print(f"  unique-line ratio: {qr['unique']}/{qr['total']} ({pct:.1f}%)")
    if qr["top_repeated"]:
        top_count, top_line = qr["top_repeated"][0][1], qr["top_repeated"][0][0]
        print(f"  top repeated:      {top_count}× {top_line[:60]!r}")
        if top_count >= TOP_REPEAT_WARN:
            warn(f"top line repeated {top_count} times — possible hallucination loop")

    if qr["ratio"] < UNIQUE_RATIO_FAIL:
        if current_model == "large-v3":
            fail(
                f"{name}: ratio still below {UNIQUE_RATIO_FAIL:.0%} even with large-v3.\n"
                "  Try cleaning the input audio (silence trim, noise gate) or splitting the video."
            )
        else:
            fail(
                f"{name}: ratio {pct:.1f}% < {UNIQUE_RATIO_FAIL:.0%} threshold.\n"
                "  RETRY with large-v3:\n"
                f"    slidoc transcribe <video> --model large-v3"
            )
        return False
    ok(f"{name}: quality OK ({pct:.1f}% unique)")
    return True
