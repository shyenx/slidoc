# Lessons learned

> Why every rule in this pipeline exists. If you ever consider removing one of the safeguards below, please re-read the corresponding failure first.

This file documents the failure modes we hit during one real production batch (5 lecture videos, 7.5 hours total). The pipeline's defaults all trace back to these incidents.

## 1. Whisper-medium hallucinates on long Chinese audio

**Symptom.** A 1h33m video (`陈天 - AI 企业培训入门`) transcribed cleanly for the first 5 minutes, then collapsed into the same line repeated for 88 minutes:

```
00:05:32  听到的扣个1吧
00:05:34  听到的扣个1吧
00:05:36  听到的扣个1吧
... (repeated 2,200 more times until end of audio) ...
```

The output SRT had **7 unique lines out of 2,575**. None of the actual lecture content was captured.

**Pattern.** Long silent or low-information audio segments push the model into an attractor state where one token sequence dominates the decoding. `medium` is more susceptible than `large-v3`; long-form lecture videos with audience-wait periods, breath pauses, or background noise are the trigger conditions.

**Mitigation.** `slidoc transcribe` always runs a quality gate:

```python
unique_ratio = unique_lines / total_lines
if unique_ratio < 0.80:  # threshold validated empirically
    sys.exit(4)  # caller should retry with --model large-v3
```

When `--model large-v3` is selected, anti-hallucination flags are applied:

```bash
whisper-cli -et 2.0 -lpt -0.8 -mc 2.0 ...
```

These tighten the entropy / log-probability / compression-ratio thresholds at which whisper.cpp falls back to a higher decoding temperature, which suppresses the repeat-loop attractor.

After re-running with these flags, the same V1 audio produced **97% unique lines** with full content captured.

## 2. Scene-detect fails on Zoom recordings

**Symptom.** Same video (V1) is actually a Zoom-call screenshare recording: a tiny PPT panel on the right, a chat sidebar in the middle that keeps scrolling, and webcam thumbnails along the bottom. Running scene-detect at the default threshold of 0.30 produced **194 keyframes for 93 minutes of video** — most of them differing only by which message had just been posted in chat.

**Pattern.** ffmpeg's scene-detect computes a global pixel-delta score. Any element that animates independently of slide changes (chat scrolls, webcam tiles, mouse cursor, picture-in-picture self-view) generates false-positive scene changes. Raising the threshold to 0.50 brought the count to 90 — still mostly noise.

**Mitigation.** Two-pronged:

1. **`slidoc inspect` extracts samples at three timestamps (60s, 5m, 30m)** so the user can eyeball the video format before extraction. The CLI explicitly tells you to classify as one of:
   - **(A) PPT screencast** → `--mode scene`
   - **(B) Zoom / busy multi-tile UI** → `--mode fps --interval 90`
   - **(C) Pure talking-head** → skip frame extraction; SRT-only output
2. **Fixed-interval mode (`--mode fps`)** samples every N seconds regardless of pixel deltas. For a 1.5h talk this gives 62 frames at 90s intervals — enough to anchor narration to time without flooding.

After switching V1 to `--mode fps --interval 90`, frame count dropped from 194 to 62 and pHash dedup further reduced it to 28 meaningful frames.

## 3. Naive parallel LLM cleanup OOM-kills the process

**Symptom.** First attempt: dispatched 14 Claude Code subagents simultaneously, each asked to read 7–19 slide images and produce a cleaned transcript. The launcher OOM-killed within minutes; six tasks reported "Agent killed".

**Pattern.** Each agent processing slide images loads them into its vision-token context (~1,500–3,000 tokens per image). With 14 concurrent agents averaging 10 images each, the total memory pressure on the host saturated swap.

**Mitigation.** Three hard rules:

1. **Maximum 2 concurrent cleanup agents per batch.**
2. **Agents with >25 segments run alone.** The cleanup prompt's batch-size guidance is in [templates/cleanup-prompt.md](../templates/cleanup-prompt.md).
3. **The prompt explicitly forbids in-agent parallelism:** "Read each frame image ONE AT A TIME (sequential, NOT parallel) to keep memory low." Without this, agents will independently try to read all their images in parallel and recreate the same OOM problem inside a single agent.

These rules cut peak memory to roughly the cost of two agents, which we measured at ~2 GB total during the validated production batch.

## 4. Alignment script was not idempotent

**Symptom.** Running `align_frames_srt.py` twice produced different (wrong) output the second time. The first run did pHash dedup on 62 input frames, kept 28, renumbered them `k_0001.jpg ... k_0028.jpg`. The second run found 28 jpgs + 62 timestamps in `frame_log.txt`, ran dedup again, and mapped the surviving 28 frames to the first 28 timestamps — collapsing 90 minutes of audio onto 40 minutes of slides.

**Pattern.** Pipelines that mutate input files (rename, delete) are not safe to re-run without thinking about state.

**Mitigation.** `slidoc.align.process_video` now does both:

1. **mtime cache:** if `raw_segments.json` is newer than both `frame_log.txt` and the source SRT, skip the work entirely.
2. **State-aware dedup:** frames already named `k_NNNN.jpg` are assumed to be the output of a previous dedup pass and pHash is **not re-run** on them.

The `slidoc align` command is now safe to call from automation, retry logic, or human curiosity.

## 5. ffmpeg's `showinfo` filter occasionally counts off by one

**Symptom.** On one video, ffmpeg wrote 12 JPG files but the showinfo log emitted 13 `pts_time:` entries. Naive alignment crashed on the off-by-one.

**Pattern.** scene-detect + showinfo can emit a `pts_time` line for the final frame even when no JPG is written (a frame buffer artifact).

**Mitigation.** `slidoc.align` always takes `min(len(times), len(frames))` and warns. Information loss is at most 1 frame at the very end of the video, which is acceptable.

## 6. Don't trust filenames

**Symptom.** A video titled "讲师介绍" was almost entirely the speaker's face filmed by webcam — no slides at all. We almost ran the whole pipeline before realizing.

**Mitigation.** Stage 0 (`slidoc inspect`) is mandatory. It takes 3 seconds per video and prevents 30 minutes of wasted whisper inference on a video that doesn't fit the pipeline.

## 7. Aggressive paraphrasing in cleanup loses content

**Symptom.** Early cleanup prompts said "summarize this segment" — agents over-compressed and dropped concrete names, numbers, and case-study details.

**Mitigation.** The current prompt template uses precise verbs:

> **PRESERVE** everything substantive: concepts, frameworks, steps, numbers, names, examples, quotes, case stories, audience-relevant Q&A, references to slides.
> Smooth into 1-3 short paragraphs of natural prose. Do NOT paraphrase aggressively — keep the speaker's voice.

The before/after comparison in [templates/cleanup-prompt.md](../templates/cleanup-prompt.md) anchors agents to the desired tone.
