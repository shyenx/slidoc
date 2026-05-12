---
name: lecture-video-to-doc
description: Use when converting one or more lecture or training videos (Chinese or English speaker with slides on screen) into a structured Markdown document that pairs each slide with the cleaned narration for that slide. Triggers include "把videos成文档"、"视频带PPT配文字"、"讲座视频转图文笔记"、"lecture video to markdown"、"slides+narration doc". Skip when only raw transcription is needed (use video-transcribe) or only frames (use video-keyframe-extract).
---

# Lecture Video → Slides + Narration Markdown

## Overview

This skill drives the `slidoc` open-source pipeline (https://github.com/shyenx/slidoc). It converts lecture videos into per-video Markdown files where every PPT slide thumbnail is paired with the cleaned narration the speaker delivered while that slide was on screen.

The pipeline has four stages. Stages 1–3 are executed by the `slidoc` CLI; stage 4 is the LLM cleanup that this skill helps you dispatch.

```
mp4 ─► ① slidoc frames     → frames/k_NNNN.jpg
    ─► ② slidoc transcribe → subtitles/N-title.srt (+quality gate)
    ─► ③ slidoc align      → raw_segments.json (idempotent)
    ─► ④ LLM subagent      → video-doc.md
```

## When to use

- 1+ video where the speaker explains slides.
- User wants a doc with slide thumbnails + cleaned narration.
- Want filler / interaction / Whisper hallucinations stripped.

**Don't use when:**
- Single short video with no slides → just `video-transcribe`.
- Just need SRT → `video-transcribe`.
- Just need frames → `video-keyframe-extract`.
- Video is pure talking-head → produce SRT-only summary.

## Critical rules (battle-tested)

1. **Sample-verify video format first.** Run `slidoc inspect <batch_dir>`. Eyeball the produced sample frames. PPT screencast = `--mode scene`; Zoom recording = `--mode fps --interval 90`; talking-head = abandon the slide-pairing approach.

2. **Always quality-gate Whisper.** `slidoc transcribe` exits 4 if unique-line ratio < 80%. Retry with `--model large-v3` (anti-hallucination flags applied automatically).

3. **Maximum 2 cleanup subagents concurrent.** Each agent reads vision-heavy slide images. > 25 segments per video → run alone. The prompt MUST tell the agent to read images "ONE AT A TIME (sequential, NOT parallel)".

4. **Don't rebuild upstream artifacts.** `slidoc align` is idempotent; re-running it never wastes compute. Same goes for `slidoc transcribe` (it overwrites the SRT but you can copy to `.bak` first if you want).

## Recipe

```bash
slidoc inspect ~/my-batch                                    # decide mode per video
slidoc frames ~/my-batch/1.mp4 --out video-doc/videos/1-x --mode scene
slidoc transcribe ~/my-batch/1.mp4 --out video-doc/subtitles --basename 1-x --model medium
slidoc align video-doc
slidoc check video-doc                                            # status table
slidoc prompt video-doc                                           # prints LLM prompts
```

Or all-in-one:
```bash
slidoc run ~/my-batch
```

For stage 4, dispatch the printed prompts as Claude Code subagents (`general-purpose`, `run_in_background: true`). Wait for each, then re-run `slidoc check` for final verification.

## Common mistakes

| Mistake | Fix |
|---|---|
| Skip `slidoc inspect` and assume scene-detect works | Always inspect; Zoom recordings need fps mode |
| Use `medium` model and trust silently | quality gate is mandatory; retry with large-v3 on failure |
| Dispatch all cleanup agents in parallel | cap concurrency at 2 |
| Let cleanup agents "read all images in parallel" | the prompt must say sequential |
| Modify an old `raw_segments.json` by hand | regenerate via `slidoc align` instead |
| Treat `video-doc.md` as authoritative without spot-check | always cross-check 2-3 segments against original SRT |

## See also

- Main project: https://github.com/shyenx/slidoc
- Pipeline architecture: `docs/architecture.md` in the repo
- Lessons-learned (full failure log): `docs/lessons-learned.md`
- Cleanup prompt template: `templates/cleanup-prompt.md`
