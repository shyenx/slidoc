# Architecture

[English](architecture.md) · [中文](architecture.zh-CN.md)

```
┌────────────────────────────────────────────────────────────────────┐
│                          slidoc pipeline                            │
└────────────────────────────────────────────────────────────────────┘

   input/
   ├── 1-speaker-topic.mp4         ┐
   ├── 2-another-talk.mp4          │  Stage 0: slidoc inspect
   └── ...                         ┘  (sample 3 frames per video,
                                       human-classifies A/B/C)
              │
              ▼
   ╔══════════════════════════════════════════════════════════════╗
   ║  Stage 1: keyframes        ║  Stage 2: transcribe            ║
   ║  ffmpeg + select=scene     ║  whisper.cpp                    ║
   ║  OR fps=1/N                ║  + quality gate (≥80% unique)   ║
   ║                            ║  + large-v3 retry if needed     ║
   ║  → frames/k_NNNN.jpg       ║  → subtitles/N-title.srt             ║
   ║  → frame_log.txt           ║                                 ║
   ╚══════════════════════════════════════════════════════════════╝
              │                              │
              └──────────────┬───────────────┘
                             ▼
   ╔══════════════════════════════════════════════════════════════╗
   ║  Stage 3: align (Python, idempotent)                          ║
   ║                                                                ║
   ║  parse frame_log.txt → list of (pts_time, frame_path)         ║
   ║  pHash dedup adjacent frames (skip if already k_NNNN named)   ║
   ║  parse SRT → [(start, end, text)]                             ║
   ║  for each kept frame t_i, collect SRT lines in [t_i, t_{i+1}) ║
   ║                                                                ║
   ║  → raw_segments.json  [{idx, ts, frame, raw}, ...]             ║
   ╚══════════════════════════════════════════════════════════════╝
                             │
                             ▼
   ╔══════════════════════════════════════════════════════════════╗
   ║  Stage 4: cleanup (LLM subagent, max 2 concurrent)            ║
   ║                                                                ║
   ║  For each video, dispatch ONE agent with:                     ║
   ║    • raw_segments.json path                                   ║
   ║    • frames/ path                                              ║
   ║    • cleanup-prompt.md instructions                            ║
   ║                                                                ║
   ║  Agent reads each frame sequentially, removes fillers /        ║
   ║  interaction / hallucinations, preserves substance, writes:    ║
   ║                                                                ║
   ║  → video-doc.md  (1 PPT thumbnail + 1-3 short paragraphs per seg)   ║
   ╚══════════════════════════════════════════════════════════════╝
```

## Stage boundaries

Each stage produces a single, durable artifact on disk. Re-running a downstream stage never requires re-running an upstream stage. This is the central design choice — long Whisper transcription should never have to repeat just because you tweaked the cleanup prompt.

| Stage | Artifact | Re-run cost |
|---|---|---|
| 1 | `frames/`, `frame_log.txt` | ~1 minute per hour of video |
| 2 | `subtitles/N-title.srt` | ~1x realtime on Apple Silicon (medium); ~1.5x (large-v3) |
| 3 | `raw_segments.json` | seconds; idempotent |
| 4 | `video-doc.md` | minutes per video (LLM-bound) |

## Why split into a Python package + shell scripts?

The Python package is the user-facing CLI and the place where state-tracking lives (mtime cache, quality gate verdicts). The shell scripts in `scripts/` are byte-for-byte equivalent to what the Python module does and exist for two reasons:

1. **Auditability.** You can read the exact ffmpeg / whisper-cli command without diving into Python.
2. **Portability.** If Python is unavailable or the package fails to import, the shell scripts can still be run by hand.

## Why pHash dedup at all?

For scene-detect extractions, animation noise (cursor blinks, brief overlays) can produce two near-duplicate frames at adjacent timestamps. Dedup collapses these. For fps-interval extractions on slow-changing content, dedup collapses long stretches of "same slide" into a single representative frame. The threshold of 8 Hamming distance on a 64-bit dHash is conservative — false positives are extremely rare; false negatives are tolerable because the LLM can still understand back-to-back identical slides.

## File naming conventions

| File | Format | Meaning |
|---|---|---|
| `f_NNNN.jpg` | Frame from current extraction, not yet deduped | |
| `k_NNNN.jpg` | Kept after dedup, renumbered. Signals "already processed" to `align`. |
| `*.srt.bad` | Backup of a low-quality SRT before retry with large-v3. Kept for debugging. |
| `raw_segments.json` | Time-aligned frames+narration; the contract between stage 3 and stage 4. |
| `video-doc.md` | Final stage 4 output: one PPT thumbnail + cleaned narration per segment. |
