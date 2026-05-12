"""Tests for slidoc.align (parsers + alignment logic).

These avoid spinning up ffmpeg/whisper and just exercise the pure-Python pieces.
"""
import json
import tempfile
from pathlib import Path

import pytest

from slidoc.align import parse_frame_log, parse_srt, process_video


SAMPLE_SHOWINFO_LOG = """\
... [Parsed_showinfo_1 @ 0x7f] n:0 pts_time:0.000000
... [Parsed_showinfo_1 @ 0x7f] n:1 pts_time:12.500000
... [Parsed_showinfo_1 @ 0x7f] n:2 pts_time:30.250000
... [Parsed_showinfo_1 @ 0x7f] n:3 pts_time:60.750000
"""


SAMPLE_SRT = """\
1
00:00:00,000 --> 00:00:05,000
opening line

2
00:00:10,000 --> 00:00:14,000
content during slide one

3
00:00:35,000 --> 00:00:40,000
content during slide two

4
00:01:00,000 --> 00:01:05,000
content during slide three
"""


def test_parse_frame_log(tmp_path):
    log = tmp_path / "log.txt"
    log.write_text(SAMPLE_SHOWINFO_LOG)
    times = parse_frame_log(log)
    assert times == [0.0, 12.5, 30.25, 60.75]


def test_parse_srt(tmp_path):
    srt = tmp_path / "x.srt"
    srt.write_text(SAMPLE_SRT)
    out = parse_srt(srt)
    assert len(out) == 4
    assert out[0][0] == 0.0 and out[0][2] == "opening line"
    assert out[1][0] == 10.0
    assert out[2][0] == 35.0
    assert out[3][0] == 60.0


def _make_jpg(p: Path, seed: int = 0):
    """Write a 32x32 JPEG with distinct content per seed so pHash differs."""
    from PIL import Image
    # Use a gradient pattern keyed to seed → distinct dHash values.
    img = Image.new("RGB", (32, 32))
    px = img.load()
    for y in range(32):
        for x in range(32):
            px[x, y] = ((x * 8 + seed * 30) % 256, (y * 8) % 256, ((x + y) * 4 + seed * 50) % 256)
    img.save(p, "JPEG")


def test_process_video_idempotent(tmp_path):
    """Running process_video twice should not re-do work."""
    vdir = tmp_path / "1-test"
    fdir = vdir / "frames"
    fdir.mkdir(parents=True)
    (vdir / "frame_log.txt").write_text(SAMPLE_SHOWINFO_LOG)
    for i in range(1, 5):
        _make_jpg(fdir / f"f_{i:04d}.jpg", seed=i)
    srt = tmp_path / "1-test.srt"
    srt.write_text(SAMPLE_SRT)

    # First run
    r1 = process_video(vdir, srt)
    assert r1 is not None
    assert (vdir / "raw_segments.json").exists()
    segs = json.loads((vdir / "raw_segments.json").read_text())
    n_segs_first = len(segs)
    assert n_segs_first > 0

    # Frames should now be k_NNNN.jpg
    assert all(f.name.startswith("k_") for f in fdir.glob("*.jpg"))

    # Second run — should be cached
    r2 = process_video(vdir, srt)
    assert r2 is not None
    assert r2.get("cached") is True

    # Same segment count
    segs2 = json.loads((vdir / "raw_segments.json").read_text())
    assert len(segs2) == n_segs_first


def test_process_video_aligns_text_to_time_windows(tmp_path):
    """The SRT line at 10s should land in the segment for the frame at 0s
    (since the next frame is at 12.5s)."""
    vdir = tmp_path / "1-test"
    fdir = vdir / "frames"
    fdir.mkdir(parents=True)
    (vdir / "frame_log.txt").write_text(SAMPLE_SHOWINFO_LOG)
    for i in range(1, 5):
        _make_jpg(fdir / f"f_{i:04d}.jpg", seed=i)
    srt = tmp_path / "1-test.srt"
    srt.write_text(SAMPLE_SRT)

    process_video(vdir, srt)
    segs = json.loads((vdir / "raw_segments.json").read_text())

    # Frames at: 0, 12.5, 30.25, 60.75
    # SRT lines at: 0 ("opening"), 10 ("slide one"), 35 ("slide two"), 60 ("slide three")
    # Windows:  [0, 12.5)  [12.5, 30.25)  [30.25, 60.75)  [60.75, ∞)
    # segs[0]: opening (0) + slide one (10)
    # segs[1]: empty
    # segs[2]: slide two (35) + slide three (60)
    # segs[3]: empty
    assert "opening line" in segs[0]["raw"]
    assert "content during slide one" in segs[0]["raw"]
    assert segs[1]["raw"] == ""
    assert "content during slide two" in segs[2]["raw"]
    assert "content during slide three" in segs[2]["raw"]
    assert segs[3]["raw"] == ""
