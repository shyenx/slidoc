# Stage 4 — Cleanup with Claude Code

`slidoc` deliberately does not automate the final LLM cleanup step. This page explains the recommended workflow when using **Claude Code** as the LLM, including the bundled skill.

## Why stage 4 is not automated inside slidoc

- Users have different LLM providers, model versions, and quotas.
- Slide images are vision-heavy and rate-limit-sensitive; the right concurrency depends on your plan.
- The cleanup is the only step where prompt engineering matters; making it a copy-paste artifact keeps it auditable and tweakable.

## Bundled Claude Code skill

The repository ships a Claude Code skill at `.claude/skills/lecture-video-to-doc/` (symlinked from your user-wide skills folder if you `make install-skill`). When you say something like "convert these lecture videos to markdown" inside Claude Code, the skill provides:

- A short summary of the four-stage pipeline.
- Pointers to `slidoc inspect | frames | transcribe | align`.
- The cleanup-prompt template for stage 4.
- Concurrency and memory rules.

## Recommended workflow

After stages 1–3 have produced `video-doc/videos/<N-title>/raw_segments.json` for each video:

1. **Inspect segment counts.**

   ```bash
   slidoc check /path/to/video-doc
   ```

2. **Decide concurrency.** Per [docs/lessons-learned.md](lessons-learned.md#3-naive-parallel-llm-cleanup-oom-kills-the-process):
   - ≤15 segments per video → can pair two videos as one round.
   - 15–25 segments → run that video alone.
   - >25 segments → run alone AND remind the prompt to "Read each frame ONE AT A TIME".

3. **Generate prompts.**

   ```bash
   slidoc prompt /path/to/video-doc
   ```

   This prints one fully-substituted cleanup prompt per video. Each prompt names the exact `raw_segments.json` path and the exact output file path.

4. **Dispatch in Claude Code.** Within Claude Code, send each prompt to a `general-purpose` subagent (background:true). The agent reads the JSON, reads frames sequentially, and writes `video-doc.md`.

5. **Verify.**

   ```bash
   slidoc check /path/to/video-doc
   ```

   Every video should now show `doc=XXkB`. Open one or two `video-doc.md` files and spot-check against the original SRT.

## Adapting to other LLMs

The prompt in [`templates/cleanup-prompt.md`](../templates/cleanup-prompt.md) is provider-agnostic. To use it with another LLM:

- Ensure the model can read images from local file paths (or upload them inline).
- Ensure the model can write the output file path you specify.
- Keep the concurrency cap (max 2) — the OOM risk is on the agent runtime, not the LLM API.
