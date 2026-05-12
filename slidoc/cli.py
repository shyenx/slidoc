"""Command-line interface for slidoc."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .align import align_batch
from .check import check_batch
from .frames import extract_keyframes
from .inspect import inspect_batch
from .prompt import emit_prompts_for_batch
from .transcribe import report_quality, transcribe
from .utils import banner, fail


def _add_inspect(sub):
    p = sub.add_parser("inspect", help="Sample frames from each mp4 to classify video format")
    p.add_argument("batch_dir", type=Path)
    p.add_argument(
        "--sample-dir", type=Path, default=Path("/tmp/slidoc-samples"),
        help="where to write sample JPGs (default: /tmp/slidoc-samples)",
    )
    p.set_defaults(func=lambda a: inspect_batch(a.batch_dir, a.sample_dir))


def _add_frames(sub):
    p = sub.add_parser("frames", help="Extract keyframes from one video")
    p.add_argument("video", type=Path)
    p.add_argument(
        "--out", type=Path, required=True,
        help="output directory (will contain frames/ and frame_log.txt)",
    )
    p.add_argument("--mode", choices=["scene", "fps"], default="scene")
    p.add_argument(
        "--threshold", type=float, default=0.30,
        help="scene-detect threshold (mode=scene; default 0.30)",
    )
    p.add_argument(
        "--interval", type=int, default=90,
        help="seconds between frames (mode=fps; default 90)",
    )
    p.add_argument("--width", type=int, default=1280)

    def _run(a):
        extract_keyframes(
            video=a.video,
            out_dir=a.out,
            mode=a.mode,
            scene_threshold=a.threshold,
            fps_interval=a.interval,
            width=a.width,
        )

    p.set_defaults(func=_run)


def _add_transcribe(sub):
    p = sub.add_parser("transcribe", help="Generate SRT for one video + quality gate")
    p.add_argument("video", type=Path)
    p.add_argument(
        "--out", type=Path, required=True,
        help="output directory for SRT (will contain <basename>.srt)",
    )
    p.add_argument(
        "--basename",
        help="output basename without extension (default: video filename stem)",
    )
    p.add_argument(
        "--model", default="medium",
        choices=["base", "small", "medium", "large-v3"],
    )
    p.add_argument("--language", default="zh")

    def _run(a):
        base = a.basename or a.video.stem
        srt, qr = transcribe(a.video, a.out, base, model=a.model, language=a.language)
        ok = report_quality(qr, base, a.model)
        if not ok:
            sys.exit(4)

    p.set_defaults(func=_run)


def _add_align(sub):
    p = sub.add_parser("align", help="Align frames with SRT (idempotent)")
    p.add_argument("root", type=Path, help="batch root containing subtitles/ and videos/")
    p.add_argument("--srt-dir", default="subtitles")
    p.add_argument("--video-dir", default="videos")
    p.add_argument("--force", action="store_true", help="rebuild even if cache fresh")

    def _run(a):
        align_batch(a.root, srt_subdir=a.srt_dir, video_subdir=a.video_dir, force=a.force)

    p.set_defaults(func=_run)


def _add_check(sub):
    p = sub.add_parser("check", help="Verify all artifacts present in a batch")
    p.add_argument("root", type=Path)
    p.add_argument("--srt-dir", default="subtitles")
    p.add_argument("--video-dir", default="videos")

    def _run(a):
        c = check_batch(a.root, srt_subdir=a.srt_dir, video_subdir=a.video_dir)
        if c["issues"]:
            sys.exit(1)

    p.set_defaults(func=_run)


def _add_prompt(sub):
    p = sub.add_parser(
        "prompt",
        help="Print cleanup prompts for stage 4 (one per video with raw_segments.json)",
    )
    p.add_argument("root", type=Path)
    p.add_argument("--video-dir", default="videos")

    def _run(a):
        emit_prompts_for_batch(a.root, video_subdir=a.video_dir)

    p.set_defaults(func=_run)


def _add_run(sub):
    p = sub.add_parser(
        "run",
        help="Orchestrate inspect -> frames -> transcribe -> align for a whole batch",
    )
    p.add_argument("batch_dir", type=Path)
    p.add_argument("--out", type=Path, help="output root (default: batch_dir/video-doc)")
    p.add_argument(
        "--frames-mode", choices=["scene", "fps"], default="scene",
        help="default extraction mode (per-video can be overridden by editing scripts)",
    )
    p.add_argument("--model", default="medium")
    p.add_argument("--language", default="zh")

    def _run(a):
        out = a.out or (a.batch_dir / "video-doc")
        out.mkdir(parents=True, exist_ok=True)
        (out / "subtitles").mkdir(exist_ok=True)
        (out / "videos").mkdir(exist_ok=True)

        banner("Stage 0: inspect")
        inspect_batch(a.batch_dir)

        videos = sorted(a.batch_dir.glob("*.mp4"))
        if not videos:
            fail(f"No *.mp4 in {a.batch_dir}")
            sys.exit(2)

        banner("Stage 1: keyframes")
        for v in videos:
            vdir = out / "videos" / v.stem
            try:
                extract_keyframes(v, vdir, mode=a.frames_mode)
            except Exception as e:
                fail(f"{v.name}: {e}")

        banner("Stage 2: transcribe")
        for v in videos:
            srt, qr = transcribe(v, out / "subtitles", v.stem, model=a.model, language=a.language)
            report_quality(qr, v.stem, a.model)

        banner("Stage 3: align")
        align_batch(out)

        banner("Stage 4: emit prompts")
        print(
            "Run `slidoc prompt {out}` to print one cleanup prompt per video,\n"
            "then dispatch each to your LLM of choice (e.g. Claude Code subagent).".format(out=out)
        )
        print()
        check_batch(out)

    p.set_defaults(func=_run)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="slidoc",
        description="Turn lecture videos into Markdown documents pairing slides with cleaned narration.",
    )
    parser.add_argument("--version", action="version", version=f"slidoc {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    _add_inspect(sub)
    _add_frames(sub)
    _add_transcribe(sub)
    _add_align(sub)
    _add_check(sub)
    _add_prompt(sub)
    _add_run(sub)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
