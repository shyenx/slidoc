# Roadmap

> Status as of v0.1.0.

## v0.2 — Robustness

- [ ] **Whisper backend abstraction.** Plug in `faster-whisper`, `whisperx`, or cloud APIs (OpenAI, AssemblyAI). Right now `slidoc transcribe` shells out to `whisper-cli` only.
- [ ] **English-language regression fixture.** ~30-second sample mp4 with slides + speaker, plus a golden `整理.md` to diff against. CI runs full pipeline.
- [ ] **Linux smoke test.** Validate `slidoc run` works without Metal acceleration; document Linux Whisper builds.
- [ ] **Configurable layout.** Replace hardcoded `字幕` / `视频整理` subdir names with a `slidoc.toml` or CLI flags.
- [ ] **Per-video override file.** Let a batch ship `slidoc.batch.yaml` mapping each video to its extraction mode + threshold.

## v0.3 — User experience

- [ ] **HTML output.** Render `整理.md` files into a browsable static site with searchable transcripts and clickable timestamps that seek the original video.
- [ ] **Web UI.** Optional Gradio / Streamlit front-end for non-CLI users.
- [ ] **Inline preview during `inspect`.** Open a quick HTML preview of all 3 sample frames per video so users don't have to fish out file paths.
- [ ] **One-command upgrade path.** Detect when a low-quality SRT is in place and auto-suggest `slidoc transcribe ... --model large-v3`.

## v0.4 — Pluggable cleanup

- [ ] **`slidoc cleanup` command** that dispatches cleanup using a provider plugin (Claude Code subagent, raw Anthropic SDK, OpenAI, local LLM via Ollama).
- [ ] **Diff mode** so users can see what was removed vs preserved in the cleanup pass.
- [ ] **Cost estimator** before running cleanup.

## Long-term ideas

- **Speaker diarization** for multi-speaker panels (annotate `[Speaker A]: ...`).
- **Multimodal grounding**: have the cleanup LLM cite which slide a claim came from.
- **Cross-video index** that auto-links related concepts across a batch of related lectures.

If you want any of the above, open an issue describing your use case before sending a PR.
