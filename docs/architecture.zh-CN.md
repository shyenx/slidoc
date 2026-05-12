# 架构

[English](architecture.md) · [中文](architecture.zh-CN.md)

```
┌────────────────────────────────────────────────────────────────────┐
│                        slidoc 流水线                                 │
└────────────────────────────────────────────────────────────────────┘

   input/
   ├── 1-speaker-topic.mp4         ┐
   ├── 2-another-talk.mp4          │  Stage 0: slidoc inspect
   └── ...                         ┘  （每个视频抽 3 帧，人工分类 A/B/C）
              │
              ▼
   ╔══════════════════════════════════════════════════════════════╗
   ║  Stage 1: 关键帧             ║  Stage 2: 转字幕                ║
   ║  ffmpeg + select=scene       ║  whisper.cpp                   ║
   ║  或 fps=1/N                  ║  + 质量门控（≥80% 唯一）        ║
   ║                              ║  + 不达标自动 large-v3 重转    ║
   ║  → frames/k_NNNN.jpg         ║  → subtitles/N-title.srt       ║
   ║  → frame_log.txt             ║                                ║
   ╚══════════════════════════════════════════════════════════════╝
              │                              │
              └──────────────┬───────────────┘
                             ▼
   ╔══════════════════════════════════════════════════════════════╗
   ║  Stage 3: align（Python，幂等）                                ║
   ║                                                                ║
   ║  解析 frame_log.txt → [(pts_time, frame_path)]                ║
   ║  pHash 去重相邻帧（已是 k_NNNN 命名则跳过）                    ║
   ║  解析 SRT → [(start, end, text)]                              ║
   ║  对每个保留帧 t_i，收集 [t_i, t_{i+1}) 内的所有 SRT 段        ║
   ║                                                                ║
   ║  → raw_segments.json  [{idx, ts, frame, raw}, ...]            ║
   ╚══════════════════════════════════════════════════════════════╝
                             │
                             ▼
   ╔══════════════════════════════════════════════════════════════╗
   ║  Stage 4: 清洗（LLM subagent，最多 2 并发）                    ║
   ║                                                                ║
   ║  每个视频派一个 agent，输入：                                  ║
   ║    • raw_segments.json 路径                                   ║
   ║    • frames/ 路径                                              ║
   ║    • cleanup-prompt.md 指令                                    ║
   ║                                                                ║
   ║  agent 顺序读每张帧，删口水/互动/幻觉，保留主干，写：          ║
   ║                                                                ║
   ║  → video-doc.md（每段：1 张 PPT + 1-3 段清洗文字）             ║
   ╚══════════════════════════════════════════════════════════════╝
```

## 阶段边界

每个阶段都产出**一个可持久化的磁盘产物**。下游阶段从来不需要重跑上游。这是核心设计原则——一段长 whisper 转写，永远不该因为你调整了清洗 prompt 就被迫重跑。

| 阶段 | 产物 | 重跑成本 |
|---|---|---|
| 1 | `frames/`、`frame_log.txt` | 每小时视频约 1 分钟 |
| 2 | `subtitles/N-title.srt` | Apple Silicon 上 medium 约 1x realtime；large-v3 约 1.5x |
| 3 | `raw_segments.json` | 秒级；幂等 |
| 4 | `video-doc.md` | 每视频几分钟（LLM-bound） |

## 为什么 Python 包 + shell 脚本两套？

Python 包是用户主入口，也是状态跟踪的地方（mtime 缓存、质量门控判定）。`scripts/` 里的 shell 脚本和 Python 模块功能 1:1 等价，存在的两个理由：

1. **可审计**——能直接读到底层 ffmpeg / whisper-cli 命令，不用钻 Python。
2. **可移植**——Python 装不上 / import 出问题，shell 脚本还能手动跑。

## 为什么要 pHash 去重

scene-detect 模式下，光标闪烁 / 短暂浮层会产生两张几乎重复的帧；去重把它们合并。fps 固定间隔模式下，慢变化内容（同一张 PPT 讲很久）会出现一连串重复帧，去重压成一张代表帧。阈值 8（64-bit dHash 上的 Hamming 距离）很保守——误判极少，漏判可以接受（LLM 处理连续两张相同 PPT 没问题）。

## 文件命名约定

| 文件 | 格式 | 含义 |
|---|---|---|
| `f_NNNN.jpg` | 当前抽帧产出，未去重 | |
| `k_NNNN.jpg` | 去重后保留 + 重新编号。这个前缀告诉 `align` 别再 pHash。 |
| `*.srt.bad` | 低质量 SRT 在用 large-v3 重转前备份。留作调试。 |
| `raw_segments.json` | 时间对齐的「帧 + 讲稿」结构；stage 3 → stage 4 的合同。 |
| `video-doc.md` | Stage 4 最终产出：每段一张 PPT + 一段清洗讲稿。 |
