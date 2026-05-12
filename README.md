<div align="center">

# 🎬 slidoc

### Turn lecture videos into Markdown that pairs every slide with its cleaned narration.

[English](README.md) · [中文](README.zh-CN.md)

[![CI](https://github.com/shyenx/slidoc/actions/workflows/ci.yml/badge.svg)](https://github.com/shyenx/slidoc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![ffmpeg](https://img.shields.io/badge/requires-ffmpeg-orange.svg)](https://ffmpeg.org/)
[![whisper.cpp](https://img.shields.io/badge/requires-whisper.cpp-purple.svg)](https://github.com/ggerganov/whisper.cpp)

</div>

---

## 💡 The problem

Video is the most natural medium for **explanation, demos, and discussion** — but it's terrible to consume after the fact.

| | What you can't do with a 2-hour mp4 |
|---|---|
| 🔍 | **Skim.** No Ctrl-F for spoken content. |
| 🎚️ | **Sample.** Scrubbing tells you nothing about content density. |
| 🧷 | **Quote.** Want one line, one slide, one number? Rewatch. |
| 📚 | **Batch.** A 10-video series buries the same insights under 15+ hours. |

> Reading is **5–10× faster** than watching.

A document of *slide thumbnail + cleaned narration* gives you something **scannable, searchable, quotable, reusable** — and every paragraph still ties back to a specific moment in the original video.

### Built for three concrete situations

> 🎯  **One long video, 30 minutes of your time.**
> Read the doc, jump to the slide that matters.

> 📝  **You attended live; you want notes.**
> Get a per-slide transcript faster than you could type one yourself.

> 🗂️  **You have a whole series.**
> Batch 5+ videos into a searchable archive, not a folder of mp4s.

**In one sentence:** *video is information-rich but opaque; slidoc makes it as scannable as a book.*

---

## 📦 What this is

`slidoc` is a **hybrid project** — a Python CLI package that ships with a bundled Claude Code skill. Pick whichever surface fits your workflow; both wrap the same pipeline.

🐚 &nbsp;**As a CLI tool**
&nbsp;&nbsp;&nbsp;&nbsp;`pip install -e .` then run `slidoc inspect | frames | transcribe | align | check | prompt | run`.
&nbsp;&nbsp;&nbsp;&nbsp;Good for CI, scripts, non-Claude workflows.

🤖 &nbsp;**As a Claude Code skill**
&nbsp;&nbsp;&nbsp;&nbsp;`make install-skill`, then say *"convert these lecture videos to Markdown"* and Claude drives the whole pipeline end-to-end.

---

## ⚙️ How it works

A four-stage local pipeline. Each stage produces a durable artifact, so a tweak downstream never costs you the long whisper run upstream.

```
 mp4 ─┬─► ①  frames        ffmpeg  (scene-detect or fixed-interval)
      │
      ├─► ②  srt           whisper.cpp  + quality gate
      │
      ├─► ③  raw_segments  slidoc align  (SRT × frames time-window join)
      │
      └─► ④  video-doc.md  LLM subagent  (slide + cleaned narration)
```

Every PPT slide thumbnail is paired with the cleaned narration the speaker delivered while that slide was on screen. Filler words, audience interaction, and Whisper hallucinations are stripped automatically; concepts, frameworks, names, numbers, and Q&A are preserved.

---

## 🛡️ Why a dedicated tool (vs. "just run Whisper")

If you've ever tried to *just transcribe* a 2-hour lecture, you know the pain:

- 🌀 &nbsp;**Whisper hallucinates** on long audio — one line repeated 500 times, silently destroying 25 min of content.
- 📡 &nbsp;**Scene detection breaks** on Zoom recordings — chat sidebar movement → 194 false-positive frames.
- 💥 &nbsp;**Parallel cleanup blows up memory** — agents reading 20+ slide images each → OOM.
- 📜 &nbsp;**Output becomes a wall of text** with no visual anchor.

> *slidoc was built and battle-tested on **7.5 hours** of real-world training videos. Every rule in this pipeline corresponds to a bug we hit.*

---

## ✨ What you get

One Markdown file per video:

```markdown
# Effective Training Delivery — Core Skills & Growth Path

> Speaker: B  |  Duration: 1h05m  |  Frames: 28  |  Source: MP4

## Table of contents
- [00:00  §1 — opening sound check](#section-1)
- [03:32  §6 — opening of the practice journey](#section-6)
- [04:53  §7 — introduction and team](#section-7)
...

## §7 · 04:53
![slide](frames/k_0007.jpg)

Brief self-introduction: longtime practitioner in the prompt-engineering
space, graduate of an early cohort of a well-known training program…

(Filler words, interaction adjustments, and whisper hallucinations
stripped; all substantive content preserved.)
```

---

## 🚀 Quick start

### 1. Install

```bash
git clone https://github.com/shyenx/slidoc.git
cd slidoc
pip install -e .                                # Python package
which ffmpeg whisper-cli                        # system deps
ls ~/.cache/whisper/ggml-medium.bin             # at least one model
```

System dependencies:

- **ffmpeg** — `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)
- **whisper.cpp** — install [whisper-cli](https://github.com/ggerganov/whisper.cpp) and put it on `$PATH`
- **whisper models** — download `ggml-medium.bin` (and ideally `ggml-large-v3.bin`) to `~/.cache/whisper/`

### 2. Lay out your batch

```
my-batch/
├── 1-speaker-topic.mp4
├── 2-another-speaker.mp4
└── ...
```

The leading `N-` index pairs files across stages (SRT ↔ frames ↔ output dir).

### 3. Run — pick your level of automation

<details open>
<summary><b>🅐 &nbsp;One sentence in Claude Code</b> &nbsp;<i>(fully automated, recommended)</i></summary>

```bash
make install-skill
```

Then in any Claude Code session:

> *"Convert the videos in `/path/to/my-batch/` into Markdown documents."*
>
> 中文：把 `/path/to/my-batch/` 里的视频整理成文档

Claude invokes the bundled `lecture-video-to-doc` skill and drives the whole pipeline. You only confirm the extraction mode per video and wait for transcription.

</details>

<details>
<summary><b>🅑 &nbsp;One shell command</b> &nbsp;<i>(CLI orchestrator)</i></summary>

```bash
slidoc run my-batch/
```

Runs stages 1–3 and prints the cleanup prompts for stage 4. Paste each into your LLM of choice (Claude Code, OpenAI, Ollama, …). Good for scripting, CI, or non-Claude LLMs.

</details>

<details>
<summary><b>🅒 &nbsp;Stage by stage</b> &nbsp;<i>(full manual control)</i></summary>

```bash
# Stage 0 — verify each video's format
slidoc inspect my-batch/

# Stage 1 — keyframes
slidoc frames my-batch/1-speaker-topic.mp4 --out video-doc/videos/1-speaker --mode scene
slidoc frames my-batch/3-zoom-recording.mp4 --out video-doc/videos/3-zoom --mode fps --interval 90

# Stage 2 — transcribe with quality gate
slidoc transcribe my-batch/1-speaker-topic.mp4 --out video-doc/subtitles --basename 1-speaker --model medium
# Exits 4 if unique-line ratio < 80%; prints the large-v3 retry command.

# Stage 3 — align frames × SRT (idempotent)
slidoc align video-doc/

# Stage 4 — generate cleanup prompts; dispatch them yourself
slidoc prompt video-doc/

# Final verification
slidoc check video-doc/
```

Best for debugging, swapping a stage, or running only part of the pipeline.

</details>

---

## ⏱️ Time budget on a real batch

5 videos · 7.5 hours of recording:

| Stage | Wall clock | You're doing |
|---|---|---|
| 0–1 &nbsp;inspect + frames | ~20 min | Confirm mode per video |
| 2 &nbsp;&nbsp;&nbsp;whisper (medium + occasional large-v3) | 4–5 h | Other things |
| 3 &nbsp;&nbsp;&nbsp;align | seconds | — |
| 4 &nbsp;&nbsp;&nbsp;LLM cleanup (2 concurrent) | ~15 min | Sip coffee |

> 🧑‍💻 &nbsp;**~10 minutes of hands-on user time, total.**

---

## 🏗️ Architecture

Four small tools, not one monolith. Each can run independently, be retried, or be replaced.

| Stage | Tool | Output |
|:---:|---|---|
| ① | `slidoc frames`  (wraps `ffmpeg`) | `frames/k_NNNN.jpg` + `frame_log.txt` |
| ② | `slidoc transcribe`  (wraps `whisper-cli`) | `subtitles/N-title.srt` |
| ③ | `slidoc align`  (Python) | `raw_segments.json` |
| ④ | LLM subagent + [`cleanup-prompt.md`](templates/cleanup-prompt.md) | `video-doc.md` |

Stage 4 is intentionally **not automated inside slidoc** — users have different LLM providers, model choices, and rate-limit budgets. The cleanup prompt template is fully specified and one copy-paste away. The bundled Claude Code skill handles the dispatch for you.

---

## 📐 Four rules, learned the hard way

1. 🎯 &nbsp;**Sample-verify the video format before extraction.** `slidoc inspect` saves you an hour of wrong-mode extraction.
2. 🚨 &nbsp;**Always quality-gate Whisper output.** Below 80% unique-line ratio → fail loudly and recommend `large-v3`.
3. 🚧 &nbsp;**Cap LLM subagent concurrency at 2.** Three concurrent agents reading 20+ slide images each → OOM.
4. ♻️ &nbsp;**Make alignment idempotent.** `slidoc align` caches `raw_segments.json` by mtime and skips re-running pHash on already-deduped frames.

Full failure log: [docs/lessons-learned.md](docs/lessons-learned.md)

---

## 📖 CLI reference

```
slidoc inspect    <dir>                       Detect video format (PPT / Zoom / talking-head)
slidoc frames     <video>  [--mode] [--param] Extract keyframes
slidoc transcribe <video>  [--model]          Generate SRT + quality gate
slidoc align      <batch>                     Build raw_segments.json (idempotent)
slidoc run        <batch>                     Orchestrate all stages + emit cleanup prompts
slidoc check      <batch>                     Verify artifacts + quality stats
slidoc prompt     <batch>                     Print stage-4 cleanup prompts
```

Every command supports `--help`.

---

## 📊 Project status

- **v0.1.0** — battle-tested on one 7.5 h batch (5 videos, 7 PPT chapters). Production-ready output.
- **Next**: pluggable LLM backends for stage ④, English-language test fixtures, 30 s end-to-end smoke test in CI. See [docs/roadmap.md](docs/roadmap.md).

---

## 🤝 Contributing

PRs welcome — please read [CONTRIBUTING.md](CONTRIBUTING.md) first. The project is small and focused; major changes start with an issue.

## 📄 License

[MIT](LICENSE)

## 🙏 Acknowledgements

- [**ffmpeg**](https://ffmpeg.org/) — keyframe & audio extraction
- [**whisper.cpp**](https://github.com/ggerganov/whisper.cpp) — local speech-to-text
- [**Pillow**](https://python-pillow.org/) — pHash-based deduplication
- Validated on a real 7.5-hour batch of private training material — the project that surfaced every failure mode this pipeline now handles.
