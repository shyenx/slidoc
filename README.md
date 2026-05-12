# slidoc

> Turn lecture & training videos into Markdown documents that **pair each slide with its cleaned narration**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![ffmpeg](https://img.shields.io/badge/requires-ffmpeg-orange.svg)](https://ffmpeg.org/)
[![whisper.cpp](https://img.shields.io/badge/requires-whisper.cpp-purple.svg)](https://github.com/ggerganov/whisper.cpp)

`slidoc` is a four-stage local pipeline that converts one or many lecture videos (Chinese or English, speaker + slides) into a structured Markdown document where **each PPT slide thumbnail is paired with the cleaned narration the speaker delivered while that slide was on screen**. Filler words, audience interaction, technical chitchat, and Whisper hallucinations are stripped automatically; substantive content (concepts, frameworks, names, numbers, examples, Q&A) is preserved.

```
 mp4 ─┬─► ① frames        (ffmpeg scene-detect or fixed-interval)
      ├─► ② srt           (whisper.cpp with quality gate)
      ├─► ③ raw_segments  (slidoc align: SRT × frames time-window join)
      └─► ④ 整理.md       (LLM cleanup via subagent, slide + cleaned narration)
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
# 探索企业培训师的核心能力和成长路径

> 主讲：胡凯翔  |  时长：1h05m  |  帧数：28  |  原视频：[MP4](...)

## 目录
- [00:00 段 1：开场调试](#段-1)
- [03:32 段 6：修炼之路开篇](#段-6)
- [04:53 段 7：自我介绍与团队](#段-7)
...

## 段 7 · 00:04:53
![slide](frames/k_0007.jpg)

先做自我介绍：提示词领域深耕者，小七姐第一届毕业生……
（已删除填充词、互动调音、whisper 幻觉，保留全部主干内容）
```

## Quick Start

### 1. Install

```bash
# Clone
git clone https://github.com/YOUR-USERNAME/slidoc.git
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

### 3. Run the pipeline

```bash
# Verify each video's format (PPT screencast vs Zoom recording)
slidoc inspect my-batch/

# Extract keyframes (scene-detect by default, fps mode for Zoom recordings)
slidoc frames my-batch/1-speaker-topic.mp4 --mode scene
slidoc frames my-batch/3-zoom-recording.mp4 --mode fps --interval 90

# Transcribe with built-in quality gate
slidoc transcribe my-batch/1-speaker-topic.mp4 --model medium
# If unique-line ratio < 80%, the tool prints a one-liner to re-run with large-v3.

# Align frames × SRT (idempotent — safe to re-run)
slidoc align my-batch/

# Then dispatch an LLM subagent per video with templates/cleanup-prompt.md
# (see docs/cleanup-with-claude.md for how to do this from Claude Code)
```

Or use the all-in-one orchestrator:

```bash
slidoc run my-batch/
# Runs inspect → frames → transcribe → align in sequence, then prints the
# cleanup-prompt for each video so you can paste them into Claude Code / your LLM.
```

## Architecture

`slidoc` is deliberately split into **four small tools** instead of one monolithic command. Each tool can be run independently, retried, or replaced.

| Stage | Tool | Output |
|---|---|---|
| ① Keyframes | `slidoc frames` (wraps `ffmpeg`) | `frames/k_NNNN.jpg` + `frame_log.txt` |
| ② Subtitles | `slidoc transcribe` (wraps `whisper-cli`) | `字幕/N-title.srt` + quality gate verdict |
| ③ Alignment | `slidoc align` (Python) | `raw_segments.json` |
| ④ Cleanup | LLM subagent + `templates/cleanup-prompt.md` | `整理.md` |

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
- Validated on real training material from 《破局俱乐部》大航海 (the project that surfaced every failure mode this pipeline now handles).
