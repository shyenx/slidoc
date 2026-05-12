# slidoc

> Turn lecture & training videos into Markdown documents that **pair each slide with its cleaned narration**.

[English](README.md) · [中文](README.zh-CN.md)

[![CI](https://github.com/shyenx/slidoc/actions/workflows/ci.yml/badge.svg)](https://github.com/shyenx/slidoc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![ffmpeg](https://img.shields.io/badge/requires-ffmpeg-orange.svg)](https://ffmpeg.org/)
[![whisper.cpp](https://img.shields.io/badge/requires-whisper.cpp-purple.svg)](https://github.com/ggerganov/whisper.cpp)

## What this is

`slidoc` is a **hybrid project**: a Python CLI package that ships with a bundled Claude Code skill.

- **As a CLI tool** — install with `pip install -e .`, then run `slidoc inspect|frames|transcribe|align|check|prompt|run` from any shell. Useful in CI, scripts, or non-Claude workflows.
- **As a Claude Code skill** — symlink `.claude/skills/lecture-video-to-doc/` into your `~/.claude/skills/` (`make install-skill`) and Claude drives the whole pipeline end-to-end when you mention lecture videos.

Pick the surface that fits your workflow; both wrap the same four-stage pipeline.

---

`slidoc` is a four-stage local pipeline that converts one or many lecture videos (Chinese or English, speaker + slides) into a structured Markdown document where **each PPT slide thumbnail is paired with the cleaned narration the speaker delivered while that slide was on screen**. Filler words, audience interaction, technical chitchat, and Whisper hallucinations are stripped automatically; substantive content (concepts, frameworks, names, numbers, examples, Q&A) is preserved.

```
 mp4 ─┬─► ① frames        (ffmpeg scene-detect or fixed-interval)
      ├─► ② srt           (whisper.cpp with quality gate)
      ├─► ③ raw_segments  (slidoc align: SRT × frames time-window join)
      └─► ④ video-doc.md       (LLM cleanup via subagent, slide + cleaned narration)
```

## Why slidoc?

If you've ever tried to "just transcribe" a 2-hour lecture, you know the pain:

- **Whisper hallucinates** on long audio — the same line repeated 500 times, silently destroying 25 min of content.
- **Scene detection breaks** on Zoom recordings (chat sidebar keeps moving → 194 false-positive frames).
- **Naive parallel transcript cleaning blows up memory** when each agent reads 20+ slide images at once.
- **Output is a wall of text** with no visual anchor to what was on screen.

slidoc was built and battle-tested while processing 7.5 hours of real-world training videos. Every rule in this pipeline corresponds to a bug we hit.

## What you get

A single Markdown document like this per video:

```markdown
# Effective Training Delivery — Core Skills & Growth Path

> Speaker: B  |  Duration: 1h05m  |  Frames: 28  |  Source: [MP4](...)

## Table of contents
- [00:00 Section 1: opening sound check](#section-1)
- [03:32 Section 6: opening of the practice journey](#section-6)
- [04:53 Section 7: introduction and team](#section-7)
...

## Section 7 · 00:04:53
![slide](frames/k_0007.jpg)

Brief self-introduction: longtime practitioner in the prompt-engineering space,
graduate of an early cohort of a well-known training program...
(filler words, interaction adjustments, and whisper hallucinations stripped;
all substantive content preserved.)
```

## Quick Start

### 1. Install

```bash
# Clone
git clone https://github.com/shyenx/slidoc.git
cd slidoc

# Install Python package (requires Python 3.9+)
pip install -e .

# Verify external deps
which ffmpeg whisper-cli   # both must exist
ls ~/.cache/whisper/ggml-medium.bin ~/.cache/whisper/ggml-large-v3.bin  # need at least one
```

System dependencies:
- **ffmpeg** — `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)
- **whisper.cpp** with the `whisper-cli` binary on `$PATH` — see [whisper.cpp installation](https://github.com/ggerganov/whisper.cpp)
- **whisper models** — download `ggml-medium.bin` and (recommended) `ggml-large-v3.bin` to `~/.cache/whisper/`

### 2. Lay out your batch

```
my-batch/
├── 1-speaker-topic.mp4
├── 2-another-speaker.mp4
└── ...
```

The leading `N-` index in each filename determines pairing across stages (SRT ↔ frames ↔ output dir).

### 3. Run the pipeline — three options

Pick the level of automation you want.

#### Option A — One sentence in Claude Code (fully automated)

If you use [Claude Code](https://claude.ai/code), install the bundled skill once:

```bash
make install-skill   # symlinks .claude/skills/lecture-video-to-doc → ~/.claude/skills/
```

Then in any Claude Code session just say:

> Convert the videos in `/path/to/my-batch/` into Markdown documents.
>
> （或中文：把 `/path/to/my-batch/` 里的视频整理成文档）

Claude will invoke the `lecture-video-to-doc` skill and drive the entire pipeline — inspect → frames → transcribe → align → dispatch ≤2 cleanup sub-agents → produce one `video-doc.md` per video. You only confirm the extraction mode per video and wait for transcription.

#### Option B — One shell command (CLI orchestrator)

```bash
slidoc run my-batch/
```

Runs stages 1–3 sequentially and prints the cleanup prompts for stage 4. Paste each printed prompt into your LLM of choice (Claude Code, OpenAI, Ollama, …) to produce the final `video-doc.md` files. Good for scripting, CI, or non-Claude LLMs.

#### Option C — Stage-by-stage (full manual control)

```bash
# Stage 0 — verify each video's format (PPT screencast vs Zoom recording)
slidoc inspect my-batch/

# Stage 1 — keyframes
slidoc frames my-batch/1-speaker-topic.mp4 --out video-doc/videos/1-speaker --mode scene
slidoc frames my-batch/3-zoom-recording.mp4 --out video-doc/videos/3-zoom --mode fps --interval 90

# Stage 2 — transcribe with built-in quality gate
slidoc transcribe my-batch/1-speaker-topic.mp4 --out video-doc/subtitles --basename 1-speaker --model medium
# If unique-line ratio < 80%, the tool exits with code 4 and prints the large-v3 retry command.

# Stage 3 — align frames × SRT (idempotent — safe to re-run)
slidoc align video-doc/

# Stage 4 — generate cleanup prompts; dispatch them yourself
slidoc prompt video-doc/

# Final verification
slidoc check video-doc/
```

Best when you're debugging, want to swap one stage's implementation, or only need part of the pipeline.

---

**Expected wall-clock on a real 5-video / 7.5-hour batch:**

| Stage | Time |
|---|---|
| 0–1 (inspect + frames, all videos) | ~20 minutes |
| 2 (whisper, medium + occasional large-v3 retry) | 4–5 hours |
| 3 (align) | seconds |
| 4 (LLM cleanup, 2 concurrent) | ~15 minutes |
| **Hands-on user time** | ~10 minutes total |

## Architecture

`slidoc` is deliberately split into **four small tools** instead of one monolithic command. Each tool can be run independently, retried, or replaced.

| Stage | Tool | Output |
|---|---|---|
| ① Keyframes | `slidoc frames` (wraps `ffmpeg`) | `frames/k_NNNN.jpg` + `frame_log.txt` |
| ② Subtitles | `slidoc transcribe` (wraps `whisper-cli`) | `subtitles/N-title.srt` + quality gate verdict |
| ③ Alignment | `slidoc align` (Python) | `raw_segments.json` |
| ④ Cleanup | LLM subagent + `templates/cleanup-prompt.md` | `video-doc.md` |

The fourth stage is intentionally LLM-driven and not automated inside slidoc — different users have different LLM providers, model choices, and rate-limit budgets. The prompt template is fully specified, includes the validated cleaning rules, and is one copy-paste away.

If you use Claude Code, the bundled skill at `.claude/skills/lecture-video-to-doc/` does the dispatch for you.

## The four rules (learned the hard way)

1. **Sample-verify the video format BEFORE 抽帧.** `slidoc inspect` extracts frames at 60s / 300s / 1800s and reports the type so you don't burn an hour on the wrong extraction mode.
2. **Always quality-gate Whisper output.** `slidoc transcribe` computes the unique-line ratio; below 80% it fails loudly and prints the `large-v3` retry command.
3. **Cap LLM subagent concurrency at 2.** Each agent reads 10-30 vision-heavy slide images; three concurrent agents OOM-killed our test runs.
4. **Make alignment idempotent.** `slidoc align` caches `raw_segments.json` by mtime and skips re-running pHash dedup on already-deduped frames.

See [docs/lessons-learned.md](docs/lessons-learned.md) for the full failure log.

## CLI Reference

```
slidoc inspect <dir>                   Detect video format (PPT / Zoom / talking-head)
slidoc frames <video> [--mode] [--param]   Extract keyframes
slidoc transcribe <video> [--model]    Generate SRT + quality gate
slidoc align <batch_root>              Build raw_segments.json (idempotent)
slidoc run <batch_root>                Orchestrate all stages + emit cleanup prompts
slidoc check <batch_root>              Verify all artifacts present + quality stats
```

Every command supports `--help`.

## Project Status

- **v0.1.0** — battle-tested on one 7.5 h batch (5 videos, 7 PPT chapters). Pipeline produces production-quality output.
- **Roadmap**: see [docs/roadmap.md](docs/roadmap.md). Highest priorities: pluggable LLM backends for stage ④, English-language test fixtures, automated end-to-end test on a 30-second sample video.

## Contributing

PRs welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

The project is small and focused. Major changes start with an issue describing the problem you're trying to solve.

## License

[MIT](LICENSE)

## Acknowledgements

- [ffmpeg](https://ffmpeg.org/) — keyframe extraction, audio extraction
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) — local speech-to-text
- [Pillow](https://python-pillow.org/) — pHash-based deduplication
- Validated on a real 7.5-hour batch of private training material — the project that surfaced every failure mode this pipeline now handles.
