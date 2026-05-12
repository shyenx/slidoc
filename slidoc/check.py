"""Batch verification (stage ⑤): confirm every video has all artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from .transcribe import quality_report
from .utils import fail, ok, parse_index_prefix, warn


def check_batch(
    root: Path,
    srt_subdir: str = "subtitles",
    video_subdir: str = "videos",
) -> dict:
    """Print per-video status. Returns summary counts."""
    srt_dir = root / srt_subdir
    vroot = root / video_subdir

    counts = {"videos": 0, "srt": 0, "frames": 0, "aligned": 0, "doc": 0, "issues": 0}

    if not srt_dir.exists() or not vroot.exists():
        fail(f"Missing expected subdirs in {root}: {srt_subdir}/, {video_subdir}/")
        counts["issues"] += 1
        return counts

    srt_map = {}
    for sf in sorted(srt_dir.glob("*.srt")):
        idx = parse_index_prefix(sf.stem)
        if idx is not None:
            srt_map[idx] = sf

    for vdir in sorted(p for p in vroot.iterdir() if p.is_dir()):
        counts["videos"] += 1
        idx = parse_index_prefix(vdir.name)
        line = f"[{idx}] {vdir.name}"
        issues = []

        frames_dir = vdir / "frames"
        frames_n = len(list(frames_dir.glob("*.jpg"))) if frames_dir.exists() else 0
        if frames_n == 0:
            issues.append("no frames")
        else:
            counts["frames"] += 1
        line += f"  frames={frames_n}"

        srt = srt_map.get(idx) if idx is not None else None
        if srt and srt.exists():
            counts["srt"] += 1
            qr = quality_report(srt)
            pct = qr["ratio"] * 100
            line += f"  srt={pct:.0f}%"
            if pct < 80:
                issues.append(f"srt quality {pct:.0f}%")
        else:
            line += "  srt=missing"
            issues.append("no srt")

        aligned = vdir / "raw_segments.json"
        if aligned.exists():
            counts["aligned"] += 1
            with open(aligned, encoding="utf-8") as f:
                segs = json.load(f)
            line += f"  segs={len(segs)}"
        else:
            issues.append("not aligned")

        doc = vdir / "video-doc.md"
        if doc.exists():
            counts["doc"] += 1
            line += f"  doc={doc.stat().st_size // 1024}KB"
        else:
            issues.append("no video-doc.md")

        if issues:
            counts["issues"] += 1
            warn(line + "  -- " + ", ".join(issues))
        else:
            ok(line)

    print()
    n = counts["videos"]
    print(
        f"Summary: {counts['srt']}/{n} SRT, {counts['frames']}/{n} frames, "
        f"{counts['aligned']}/{n} aligned, {counts['doc']}/{n} video-doc.md "
        f"({counts['issues']} issues)"
    )
    return counts
