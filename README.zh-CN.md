# slidoc

> 把讲座 / 培训视频整理成 **每张 PPT 配对应清洗讲稿** 的 Markdown 文档。

[English](README.md) · [中文](README.zh-CN.md)

[![CI](https://github.com/shyenx/slidoc/actions/workflows/ci.yml/badge.svg)](https://github.com/shyenx/slidoc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![ffmpeg](https://img.shields.io/badge/requires-ffmpeg-orange.svg)](https://ffmpeg.org/)
[![whisper.cpp](https://img.shields.io/badge/requires-whisper.cpp-purple.svg)](https://github.com/ggerganov/whisper.cpp)

## 这是什么

`slidoc` 是一个**混合项目**：一个 Python CLI 包，并且打包了一个 Claude Code skill。

- **作为 CLI 工具** — `pip install -e .` 装好后，在任意 shell 里跑 `slidoc inspect|frames|transcribe|align|check|prompt|run`。适合 CI、脚本、非 Claude 工作流。
- **作为 Claude Code skill** — 把 `.claude/skills/lecture-video-to-doc/` 软链到 `~/.claude/skills/`（`make install-skill`），之后在 Claude Code 里一句话「把这些视频整理成文档」就能驱动整套流水线。

选你顺手的入口，两边包的是同一条四阶段流水线。

---

`slidoc` 是一条本地的四阶段流水线，把一段或多段讲座视频（中文 / 英文，主讲 + PPT）转成结构化 Markdown：**每张 PPT 缩略图配上主讲人讲那张幻灯片时的清洗后讲稿**。口水词、互动调音、whisper 幻觉自动剥离；核心内容（概念、框架、人名、数字、案例、问答）完整保留。

```
 mp4 ─┬─► ① 关键帧抽取    (ffmpeg scene-detect 或固定间隔)
      ├─► ② SRT 字幕      (whisper.cpp + 质量门控)
      ├─► ③ raw_segments  (slidoc align：SRT × 帧 时间窗对齐)
      └─► ④ video-doc.md   (LLM subagent 清洗 + 配帧成稿)
```

## 为什么是 slidoc

如果你试过「直接转写一段两小时的讲座」，你大概知道这些坑：

- **Whisper 长音频幻觉** — 同一句循环 500 遍，悄悄吃掉 25 分钟实质内容。
- **Scene 检测在 Zoom 录屏上失效**（聊天侧栏一直滚 → 194 个误判帧）。
- **多 agent 并行清洗内存爆炸**：每个 agent 读 20+ 张 PPT 图，三个 agent 一起跑就 OOM。
- **产出是一堵文字墙**，没有视觉锚点能让人看到「这段在讲哪张幻灯片」。

slidoc 是处理 7.5 小时真实培训视频时一点点打磨出来的；每条规则都对应一个我们踩过的坑。

## 你能拿到什么

每个视频一份 Markdown，长这样：

```markdown
# Effective Training Delivery — Core Skills & Growth Path

> 主讲：Speaker B  |  时长：1h05m  |  帧数：28  |  原视频：[MP4](...)

## 目录
- [00:00 段 1：开场调试](#段-1)
- [03:32 段 6：修炼之路开篇](#段-6)
- [04:53 段 7：自我介绍与团队](#段-7)
...

## 段 7 · 00:04:53
![slide](frames/k_0007.jpg)

简短自我介绍：提示工程领域的长期实践者，某知名培训项目早期毕业……
（已删除填充词、互动调音、whisper 幻觉，保留全部主干内容）
```

## 快速开始

### 1. 安装

```bash
# Clone
git clone https://github.com/shyenx/slidoc.git
cd slidoc

# 装 Python 包（需要 Python 3.9+）
pip install -e .

# 验证系统依赖
which ffmpeg whisper-cli            # 两个都要在
ls ~/.cache/whisper/ggml-medium.bin ~/.cache/whisper/ggml-large-v3.bin  # 至少一个
```

系统依赖：
- **ffmpeg** — `brew install ffmpeg`（macOS）或 `apt install ffmpeg`（Linux）
- **whisper.cpp** + `whisper-cli` 命令在 `$PATH` 里 — 见 [whisper.cpp 安装](https://github.com/ggerganov/whisper.cpp)
- **whisper 模型** — 把 `ggml-medium.bin` 和（推荐）`ggml-large-v3.bin` 下载到 `~/.cache/whisper/`

### 2. 准备视频批次

```
my-batch/
├── 1-speaker-topic.mp4
├── 2-another-speaker.mp4
└── ...
```

文件名前缀 `N-` 用来在不同阶段之间配对（SRT ↔ 帧 ↔ 输出目录）。

### 3. 三种执行方式

按你想要的自动化程度挑一个。

#### 方式 A — 在 Claude Code 里一句话（最自动化）

如果你用 [Claude Code](https://claude.ai/code)，先装 bundled skill：

```bash
make install-skill   # 把 .claude/skills/lecture-video-to-doc 软链到 ~/.claude/skills/
```

然后在任意 Claude Code 会话里说：

> 把 `/path/to/my-batch/` 里的视频整理成文档

Claude 会自动调起 `lecture-video-to-doc` skill，串完整条流水线 — inspect → frames → transcribe → align → 派 ≤ 2 个清洗 subagent → 每个视频一份 `video-doc.md`。你只需要：确认每个视频用什么抽帧模式，然后等转字幕。

#### 方式 B — 一行 shell 命令（CLI 编排器）

```bash
slidoc run my-batch/
```

依次跑 stage 1-3，结束后打印每个视频的清洗 prompt。把这些 prompt 粘进你的 LLM（Claude Code / OpenAI / Ollama / …），由它生成最终 `video-doc.md`。适合脚本化、CI、或用非 Claude LLM。

#### 方式 C — 分阶段（完全手动控制）

```bash
# Stage 0 — 抽样验证每个视频的格式（PPT 录屏 vs Zoom 录屏）
slidoc inspect my-batch/

# Stage 1 — 关键帧抽取
slidoc frames my-batch/1-speaker-topic.mp4 --out video-doc/videos/1-speaker --mode scene
slidoc frames my-batch/3-zoom-recording.mp4 --out video-doc/videos/3-zoom --mode fps --interval 90

# Stage 2 — 转字幕 + 质量门控
slidoc transcribe my-batch/1-speaker-topic.mp4 --out video-doc/subtitles --basename 1-speaker --model medium
# 唯一行比率 < 80% 时退出码 4 + 打印 large-v3 重试命令

# Stage 3 — 帧 × SRT 对齐（幂等，可反复跑）
slidoc align video-doc/

# Stage 4 — 生成清洗 prompt；自己派给 LLM
slidoc prompt video-doc/

# 验收
slidoc check video-doc/
```

适合：调试 / 替换某一步的实现 / 只跑流水线的一部分。

---

**一个真实 5 视频 / 7.5 小时批次的耗时：**

| 阶段 | 耗时 |
|---|---|
| 0–1（抽样 + 抽帧，全部视频） | ~20 分钟 |
| 2（whisper，medium + 偶尔 large-v3 重转） | 4–5 小时 |
| 3（对齐） | 秒级 |
| 4（LLM 清洗，2 并发） | ~15 分钟 |
| **用户实际投入** | 总计 ~10 分钟 |

## 架构

`slidoc` 故意拆成**四个小工具**而不是一个大命令。每个工具能独立跑、独立重试、独立替换。

| 阶段 | 工具 | 产出 |
|---|---|---|
| ① 关键帧 | `slidoc frames`（包 `ffmpeg`） | `frames/k_NNNN.jpg` + `frame_log.txt` |
| ② 字幕 | `slidoc transcribe`（包 `whisper-cli`） | `subtitles/N-title.srt` + 质量门控 |
| ③ 对齐 | `slidoc align`（Python） | `raw_segments.json` |
| ④ 清洗 | LLM subagent + `templates/cleanup-prompt.md` | `video-doc.md` |

第四阶段刻意不内置 — 不同用户用不同 LLM、不同模型、不同配额。Prompt 模板写得完整、清洗规则验证过，复制粘贴就能用。

如果你用 Claude Code，bundled skill 替你做 stage 4 的派发。

## 四条铁律（踩坑换来的）

1. **抽帧前先抽样确认视频格式。** `slidoc inspect` 在 60s / 300s / 1800s 抽 3 张样图，避免用错模式浪费一小时。
2. **whisper 输出永远过质量门控。** `slidoc transcribe` 计算唯一行比率；< 80% 直接失败 + 打印 `large-v3` 重试命令。
3. **清洗 subagent 并发上限 = 2。** 每个 agent 读 10-30 张视觉重图；3 个并发会把我们的测试环境 OOM 杀掉。
4. **对齐必须幂等。** `slidoc align` 用 mtime 缓存 `raw_segments.json`，对已重命名的帧（`k_NNNN.jpg`）跳过 pHash 二次去重。

完整失败日志见 [docs/lessons-learned.zh-CN.md](docs/lessons-learned.zh-CN.md)。

## CLI 速查

```
slidoc inspect <dir>                       检测视频格式（PPT / Zoom / talking-head）
slidoc frames <video> [--mode] [--param]   抽关键帧
slidoc transcribe <video> [--model]        生成 SRT + 质量门控
slidoc align <batch_root>                  生成 raw_segments.json（幂等）
slidoc run <batch_root>                    串完所有阶段 + 输出清洗 prompt
slidoc check <batch_root>                  验收：所有产物齐了吗，质量统计
```

每个子命令支持 `--help`。

## 项目状态

- **v0.1.0** — 一个 7.5 小时批次（5 视频 + 7 章 PPT）实战验证过，产出可用。
- **路线图**：见 [docs/roadmap.zh-CN.md](docs/roadmap.zh-CN.md)。最高优先级：stage 4 可插拔 LLM 后端、英文测试样本、30 秒样本视频上的端到端 smoke test。

## 贡献

欢迎 PR。请先读 [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)。

项目小而聚焦。大改动先开 issue 说清你要解决的问题。

## 许可证

[MIT](LICENSE)

## 致谢

- [ffmpeg](https://ffmpeg.org/) — 关键帧抽取，音频提取
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) — 本地语音转文字
- [Pillow](https://python-pillow.org/) — pHash 帧去重
- 在一个 7.5 小时的真实私域培训批次上验证 — 那个项目暴露了这条流水线现在能扛住的每一种失败模式。
