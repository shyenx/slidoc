"""Stage ③: align extracted frames with SRT subtitles.

Produces `raw_segments.json` per video. Idempotent: skips work if the JSON is
newer than both `frame_log.txt` and the SRT.

Frames already named `k_NNNN.jpg` are assumed to be pre-deduped (the output of
a previous run) and pHash dedup is skipped — this prevents re-running from
collapsing the carefully time-aligned frames to a wrong subset.
"""
from __future__ import annotations

import glob
import json
import os
import re
from pathlib import Path

from PIL import Image

from .utils import fmt_ts, is_newer, ok, parse_index_prefix, warn

PHASH_THRESHOLD = 8
PHASH_SIZE = 8


def phash(path: Path, size: int = PHASH_SIZE) -> int:
    """64-bit difference hash."""
    img = Image.open(path).convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(img.getdata())
    bits = 0
    for r in range(size):
        for c in range(size):
            i = r * (size + 1) + c
            bits = (bits << 1) | (1 if px[i] > px[i + 1] else 0)
    return bits


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def parse_frame_log(path: Path) -> list[float]:
    """Pull pts_time floats out of ffmpeg showinfo stderr."""
    times: list[float] = []
    with open(path, errors="ignore") as f:
        for line in f:
            if "showinfo" in line and "pts_time:" in line:
                m = re.search(r"pts_time:([0-9.]+)", line)
                if m:
                    times.append(float(m.group(1)))
    return times


def parse_srt(path: Path) -> list[tuple[float, float, str]]:
    """SRT → [(start_sec, end_sec, text)]."""
    out: list[tuple[float, float, str]] = []
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for blk in re.split(r"\n\n+", text.strip()):
        lines = blk.strip().split("\n")
        if len(lines) < 3:
            continue
        m = re.match(
            r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)",
            lines[1],
        )
        if not m:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, m.groups())
        start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
        end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
        txt = " ".join(lines[2:]).strip()
        if txt:
            out.append((start, end, txt))
    return out


def _dedup_frames(
    pairs: list[tuple[float, Path]], threshold: int
) -> tuple[list[tuple[float, Path]], int]:
    """Hash-based dedup of consecutive frames. Returns (kept, removed_count)."""
    keep: list[tuple[float, Path]] = []
    last_h: int | None = None
    for t, fp in pairs:
        h = phash(fp)
        if last_h is None or hamming(h, last_h) >= threshold:
            keep.append((t, fp))
            last_h = h
    return keep, len(pairs) - len(keep)


def process_video(
    vdir: Path,
    srt_path: Path | None,
    force: bool = False,
    skip_dedup: bool = False,
) -> dict | None:
    """Align one video's frames with its SRT. Returns summary dict or None on skip."""
    log_path = vdir / "frame_log.txt"
    fdir = vdir / "frames"
    json_path = vdir / "raw_segments.json"

    if not log_path.exists():
        warn(f"{vdir.name}: no frame_log.txt — skipping")
        return None
    if not any(fdir.glob("*.jpg")):
        warn(f"{vdir.name}: no frames — skipping")
        return None

    # Idempotency
    deps: list[Path] = [log_path]
    if srt_path and srt_path.exists():
        deps.append(srt_path)
    if not force and is_newer(json_path, *deps):
        ok(f"{vdir.name}: raw_segments.json is fresh (cached)")
        with open(json_path, encoding="utf-8") as f:
            return {"vdir": vdir, "segments": len(json.load(f)), "cached": True}

    times = parse_frame_log(log_path)
    frames = sorted(fdir.glob("*.jpg"))

    if len(times) != len(frames):
        warn(f"{vdir.name}: {len(times)} timestamps vs {len(frames)} frames; using min")
    n = min(len(times), len(frames))
    pairs = [(times[i], frames[i]) for i in range(n)]

    # Already-deduped frames are named k_NNNN.jpg; skip pHash to avoid mis-collapse.
    already_renamed = bool(pairs) and pairs[0][1].name.startswith("k_")

    if skip_dedup or already_renamed:
        kept = pairs
        removed = 0
    else:
        kept, removed = _dedup_frames(pairs, PHASH_THRESHOLD)
        # Delete frames that weren't kept
        keep_set = {fp for _, fp in kept}
        for _, fp in pairs:
            if fp not in keep_set:
                fp.unlink(missing_ok=True)
        # Renumber to k_NNNN.jpg
        renumbered: list[tuple[float, Path]] = []
        for i, (t, old) in enumerate(kept, 1):
            new = fdir / f"k_{i:04d}.jpg"
            if old != new and old.exists():
                old.rename(new)
            renumbered.append((t, new))
        kept = renumbered

    # SRT alignment
    if not srt_path or not srt_path.exists():
        warn(f"{vdir.name}: SRT not found; emitting empty raw fields")
        srt: list[tuple[float, float, str]] = []
    else:
        srt = parse_srt(srt_path)

    segments = []
    for i, (t_i, fpath) in enumerate(kept):
        t_next = kept[i + 1][0] if i + 1 < len(kept) else float("inf")
        chunk = [s[2] for s in srt if t_i <= s[0] < t_next]
        segments.append(
            {
                "idx": i + 1,
                "ts_sec": t_i,
                "ts": fmt_ts(t_i),
                "frame": os.path.relpath(fpath, vdir),
                "raw": " ".join(chunk).strip(),
            }
        )

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    ok(
        f"{vdir.name}: {len(pairs)}→{len(kept)} frames "
        f"(dedup {removed}), {len(segments)} segments, srt={'Y' if srt else 'N'}"
    )
    return {"vdir": vdir, "segments": len(segments), "cached": False, "removed": removed}


def align_batch(
    root: Path,
    srt_subdir: str = "字幕",
    video_subdir: str = "视频整理",
    force: bool = False,
) -> list[dict]:
    """Align every video subdirectory in `root/video_subdir`.

    SRT files in `root/srt_subdir` are matched by their leading 'N-' index.
    """
    srt_dir = root / srt_subdir
    vroot = root / video_subdir

    srt_map: dict[int, Path] = {}
    for sf in sorted(srt_dir.glob("*.srt")):
        idx = parse_index_prefix(sf.stem)
        if idx is not None:
            srt_map[idx] = sf

    results: list[dict] = []
    for vdir in sorted(p for p in vroot.iterdir() if p.is_dir()):
        idx = parse_index_prefix(vdir.name)
        srt = srt_map.get(idx) if idx is not None else None
        r = process_video(vdir, srt, force=force)
        if r is not None:
            results.append(r)
    return results
