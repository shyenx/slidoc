# Examples

[English](README.md) · [中文](README.zh-CN.md)

Tiny end-to-end demos. Each subdirectory is a self-contained reproduction.

## quickstart-zh

A minimal Chinese-language scenario that mirrors the original validation batch. **No real mp4 is included** (too large for git); the README shows you how to drop in any short lecture video and run the pipeline against it.

```bash
cd examples/quickstart-zh
# Put a short Chinese lecture mp4 here, e.g. lecture.mp4
slidoc inspect .
slidoc frames lecture.mp4 --out work --mode scene
slidoc transcribe lecture.mp4 --out subtitles --basename 1-demo --model medium
slidoc align .
slidoc check .
slidoc prompt .  # copy the printed prompt into Claude Code
```

## fixture-en (planned, v0.2)

A bundled 30-second English clip with golden output. CI runs the full pipeline against this fixture to detect regressions. See [docs/roadmap.md](../docs/roadmap.md).
