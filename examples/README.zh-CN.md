# 示例

[English](README.md) · [中文](README.zh-CN.md)

最小可复现的端到端 demo。每个子目录是一个独立场景。

## quickstart-zh

一个最小的中文讲座视频场景，对应原始验证批次。**仓库里不带 mp4**（太大，git 装不下）；README 告诉你怎么把任意一段短视频放进来就能跑。

```bash
cd examples/quickstart-zh
# 把任意一段短的中文讲座 mp4 放在这里，命名为 lecture.mp4
slidoc inspect .
slidoc frames lecture.mp4 --out work --mode scene
slidoc transcribe lecture.mp4 --out subtitles --basename 1-demo --model medium
slidoc align .
slidoc check .
slidoc prompt .   # 把打印出来的 prompt 粘进 Claude Code
```

## fixture-en（v0.2 规划）

会内置一段 30 秒英文视频 + 金标输出。CI 会在这个样本上跑全流水线做回归。见 [docs/roadmap.zh-CN.md](../docs/roadmap.zh-CN.md)。
