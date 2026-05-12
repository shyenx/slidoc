# Quickstart (Chinese lecture video)

Drop a Chinese-language lecture mp4 here named `lecture.mp4`, then:

```bash
slidoc inspect .
# inspect prints 3 sample frames per video; decide:
#   PPT screencast  → --mode scene
#   Zoom-style UI   → --mode fps --interval 90

mkdir -p 字幕 视频整理
slidoc frames lecture.mp4 --out 视频整理/1-demo --mode scene
slidoc transcribe lecture.mp4 --out 字幕 --basename 1-demo --model medium
slidoc align .            # generates 视频整理/1-demo/raw_segments.json
slidoc check .
slidoc prompt .           # prints LLM cleanup prompt
```

Then dispatch the printed prompt to your LLM (Claude Code subagent recommended; see `docs/cleanup-with-claude.md`).

Final output: `视频整理/1-demo/整理.md`.
