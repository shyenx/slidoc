# 快速上手（中文讲座视频）

[English](README.md) · [中文](README.zh-CN.md)

把一段中文讲座 mp4 放到本目录，命名为 `lecture.mp4`，然后：

```bash
slidoc inspect .
# inspect 会为每个视频抽 3 张样图，肉眼判断：
#   PPT 录屏   → --mode scene
#   Zoom 风格 → --mode fps --interval 90

mkdir -p subtitles videos
slidoc frames lecture.mp4 --out videos/1-demo --mode scene
slidoc transcribe lecture.mp4 --out subtitles --basename 1-demo --model medium
slidoc align .            # 生成 videos/1-demo/raw_segments.json
slidoc check .
slidoc prompt .           # 打印 LLM 清洗 prompt
```

把打印出来的 prompt 粘进你的 LLM（推荐 Claude Code subagent；见 [docs/cleanup-with-claude.zh-CN.md](../../docs/cleanup-with-claude.zh-CN.md)）。

最终产出：`videos/1-demo/video-doc.md`。
