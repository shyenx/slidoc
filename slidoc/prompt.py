"""Emit cleanup prompts for stage 4 LLM subagents."""

from __future__ import annotations

import json
from pathlib import Path

PROMPT_TEMPLATE = """\
You will produce a clean lecture transcript for video {N} -- "{TITLE}" by {SPEAKER}.

Inputs:
- Aligned data: `{VDIR}/raw_segments.json` ({N_SEGMENTS} segments).
  Each item has {{idx, ts (HH:MM:SS), frame (relative path), raw (concatenated SRT lines for that frame's time window)}}.
- PPT frames: `{VDIR}/frames/k_NNNN.jpg` (or f_NNNN.jpg).

Output (Write tool, single file, overwrite if exists):
`{VDIR}/video-doc.md`

Cleaning rules for each segment's `raw`:
1. Remove fillers: filler words like 嗯/啊/呃/那个/就是说/对吧 (English: um, uh, like).
2. Remove interaction & chitchat: "can you hear me", "stand by", "where was I".
3. Remove technical disruption: "the network is bad", "let me redo".
4. Remove whisper hallucinations: identical sentence repeated 3+ times -> keep one or drop.
5. PRESERVE everything substantive: concepts, frameworks, steps, numbers, names, examples, quotes, Q&A, slide references.
6. Smooth into 1-3 short paragraphs of natural prose. Do NOT paraphrase aggressively.
7. If a segment is essentially empty after cleaning, output: `> (no substantive content)`.
8. Read each frame image ONE AT A TIME (sequential, NOT parallel) to keep memory low.

Document format:
```markdown
# {TITLE}

> Speaker: {SPEAKER}  |  Duration: {DURATION}  |  Frames: {N_SEGMENTS}  |  Source: [MP4]({MP4_REL})

## TOC
- [00:00 Section 1: xxx](#section-1)
- ...

---

<a id="section-1"></a>
## Section 1 - 00:00:00
![](frames/k_0001.jpg)

{{cleaned narration}}
```

TOC labels: short 4-8 word topic phrase. Process segments sequentially. Reply only "DONE" when finished.
"""


def build_prompt(
    vdir: Path,
    title: str,
    speaker: str,
    duration: str,
    mp4_rel: str,
) -> str:
    aligned = vdir / "raw_segments.json"
    n_segments = 0
    if aligned.exists():
        with open(aligned, encoding="utf-8") as f:
            n_segments = len(json.load(f))

    idx = vdir.name.split("-", 1)[0] if "-" in vdir.name else "?"
    return PROMPT_TEMPLATE.format(
        N=idx,
        TITLE=title,
        SPEAKER=speaker,
        VDIR=str(vdir),
        N_SEGMENTS=n_segments,
        DURATION=duration,
        MP4_REL=mp4_rel,
    )


def emit_prompts_for_batch(root: Path, video_subdir: str = "videos") -> None:
    """Print one cleanup prompt per video for the user to dispatch."""
    vroot = root / video_subdir
    for vdir in sorted(p for p in vroot.iterdir() if p.is_dir()):
        if not (vdir / "raw_segments.json").exists():
            continue
        parts = vdir.name.split("-", 2)
        speaker = parts[1] if len(parts) > 1 else "?"
        title = parts[2] if len(parts) > 2 else vdir.name
        prompt = build_prompt(
            vdir=vdir,
            title=title,
            speaker=speaker,
            duration="?",
            mp4_rel=f"../../{vdir.name}.mp4",
        )
        print("=" * 80)
        print(f"PROMPT FOR: {vdir.name}")
        print("=" * 80)
        print(prompt)
        print()
