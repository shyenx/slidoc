<div align="center">

# 🎬 slidoc

### 把讲座视频整理成「PPT 缩略图 + 清洗后讲稿」的 Markdown 文档。

[English](README.md) · [中文](README.zh-CN.md)

[![CI](https://github.com/shyenx/slidoc/actions/workflows/ci.yml/badge.svg)](https://github.com/shyenx/slidoc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![ffmpeg](https://img.shields.io/badge/requires-ffmpeg-orange.svg)](https://ffmpeg.org/)
[![whisper.cpp](https://img.shields.io/badge/requires-whisper.cpp-purple.svg)](https://github.com/ggerganov/whisper.cpp)

</div>

---

## 💡 要解决的问题

视频是最自然的**讲解 / 演示 / 讨论**载体——但事后回看效率极低。

| | 一段两小时的 mp4 你做不到 |
|---|---|
| 🔍 | **跳读。** 视频内容没有 Ctrl-F。 |
| 🎚️ | **采样。** 拉时间轴根本看不出哪一段内容密度高。 |
| 🧷 | **引用。** 想引一句话、一张幻灯片、一个数字？回到视频翻。 |
| 📚 | **批量。** 10 段视频反复讲同一套方法论，淹没在 15+ 小时录像里。 |

> 读文字比看视频快 **5–10 倍**。

一份「PPT 缩略图 + 清洗后的讲稿」给你**可扫读、可搜索、可摘录、可复用**的文档——而且每段都对应回原视频的具体时间点。

### 三个具体场景

> 🎯  **一段长视频，我只有 30 分钟。**
> 读文档代替看视频，跳到关心的那张 PPT 即可。

> 📝  **现场听过，但没记笔记。**
> 比你自己速记更快地拿到一份「带 PPT 的逐段讲稿」。

> 🗂️  **我有一整个系列。**
> 一次性处理 5+ 个视频，把「一堆 mp4」变成「一份可搜索的资料库」。

**一句话：** *视频内容信息量大但不透明；slidoc 让它像一本书一样可翻可查。*

---

## 📦 这是什么

`slidoc` 是一个**混合项目**——一个 Python CLI 包，同时打包了一个 Claude Code skill。两个入口包的是同一条流水线，按你顺手的方式来。

🐚 &nbsp;**作为 CLI 工具**
&nbsp;&nbsp;&nbsp;&nbsp;`pip install -e .` 之后跑 `slidoc inspect | frames | transcribe | align | check | prompt | run`。
&nbsp;&nbsp;&nbsp;&nbsp;适合 CI、脚本、非 Claude 工作流。

🤖 &nbsp;**作为 Claude Code skill**
&nbsp;&nbsp;&nbsp;&nbsp;`make install-skill` 安装好，之后一句「把这些视频整理成文档」Claude 会替你跑完整条流水线。

---

## ⚙️ 工作原理

四阶段本地流水线。每一阶段都产出磁盘上可持久的产物，下游阶段调整不会影响上游已跑过的长任务。

```
 mp4 ─┬─► ①  关键帧抽取    ffmpeg  (scene-detect 或固定间隔)
      │
      ├─► ②  SRT 字幕      whisper.cpp  + 质量门控
      │
      ├─► ③  raw_segments  slidoc align  (SRT × 帧 时间窗对齐)
      │
      └─► ④  video-doc.md  LLM subagent  (PPT 帧 + 清洗讲稿)
```

每张 PPT 缩略图配上主讲人讲那张幻灯片时的清洗讲稿。口水词、互动调音、whisper 幻觉自动剥离；核心内容（概念、框架、人名、数字、问答）完整保留。

---

## 🛡️ 为什么需要专门工具（而不是「直接跑 Whisper」）

如果你试过「直接转一段两小时的讲座」，你大概知道这些坑：

- 🌀 &nbsp;**Whisper 长音频幻觉** — 同一句循环 500 遍，悄悄吃掉 25 分钟实质内容。
- 📡 &nbsp;**Scene 检测在 Zoom 录屏上失效** — 聊天侧栏一直滚 → 194 个误判帧。
- 💥 &nbsp;**并行清洗内存爆炸** — 每个 agent 读 20+ 张 PPT 图 → OOM。
- 📜 &nbsp;**产出是一堵文字墙**，没有视觉锚点告诉你「这段在讲哪张幻灯片」。

> *slidoc 是处理 **7.5 小时** 真实培训视频时一点点打磨出来的；每条规则都对应一个我们踩过的坑。*

---

## ✨ 产出长这样

每个视频一份 Markdown：

```markdown
# Effective Training Delivery — Core Skills & Growth Path

> 主讲：Speaker B  |  时长：1h05m  |  帧数：28  |  原视频：MP4

## 目录
- [00:00  §1 — 开场调试](#段-1)
- [03:32  §6 — 修炼之路开篇](#段-6)
- [04:53  §7 — 自我介绍与团队](#段-7)
...

## §7 · 04:53
![slide](frames/k_0007.jpg)

简短自我介绍：提示工程领域的长期实践者，某知名培训项目早期毕业……

（已删除填充词、互动调音、whisper 幻觉，保留全部主干内容）
```

---

## 🚀 快速上手

### 1. 安装

```bash
git clone https://github.com/shyenx/slidoc.git
cd slidoc
pip install -e .                                # Python 包
which ffmpeg whisper-cli                        # 系统依赖
ls ~/.cache/whisper/ggml-medium.bin             # 至少一个模型
```

系统依赖：

- **ffmpeg** — `brew install ffmpeg`（macOS）或 `apt install ffmpeg`（Linux）
- **whisper.cpp** — 装好 [whisper-cli](https://github.com/ggerganov/whisper.cpp) 并放到 `$PATH`
- **whisper 模型** — 把 `ggml-medium.bin`（理想情况再加 `ggml-large-v3.bin`）下到 `~/.cache/whisper/`

### 2. 准备视频批次

```
my-batch/
├── 1-speaker-topic.mp4
├── 2-another-speaker.mp4
└── ...
```

前缀 `N-` 用来在不同阶段之间配对（SRT ↔ 帧 ↔ 输出目录）。

### 3. 跑起来——按你想要的自动化程度挑一个

<details open>
<summary><b>🅐 &nbsp;Claude Code 一句话</b> &nbsp;<i>（最自动化，推荐）</i></summary>

```bash
make install-skill
```

之后在任意 Claude Code 会话里说：

> *把 `/path/to/my-batch/` 里的视频整理成文档*

Claude 会调用 bundled `lecture-video-to-doc` skill 跑完整条流水线。你只需要确认每个视频用什么抽帧模式，然后等转字幕。

</details>

<details>
<summary><b>🅑 &nbsp;一行 shell 命令</b> &nbsp;<i>（CLI 编排器）</i></summary>

```bash
slidoc run my-batch/
```

依次跑 stage 1-3，最后打印每个视频的清洗 prompt。把它们粘进你选的 LLM（Claude Code / OpenAI / Ollama / …）。适合脚本化、CI、非 Claude LLM。

</details>

<details>
<summary><b>🅒 &nbsp;分阶段执行</b> &nbsp;<i>（完全手动控制）</i></summary>

```bash
# Stage 0 — 抽样验证每个视频的格式
slidoc inspect my-batch/

# Stage 1 — 关键帧抽取
slidoc frames my-batch/1-speaker-topic.mp4 --out video-doc/videos/1-speaker --mode scene
slidoc frames my-batch/3-zoom-recording.mp4 --out video-doc/videos/3-zoom --mode fps --interval 90

# Stage 2 — 转字幕 + 质量门控
slidoc transcribe my-batch/1-speaker-topic.mp4 --out video-doc/subtitles --basename 1-speaker --model medium
# 唯一行比率 < 80% 时退出码 4 + 打印 large-v3 重试命令

# Stage 3 — 帧 × SRT 对齐（幂等）
slidoc align video-doc/

# Stage 4 — 生成清洗 prompt；自己派给 LLM
slidoc prompt video-doc/

# 验收
slidoc check video-doc/
```

适合调试、替换某一步、只跑部分阶段。

</details>

---

## ⏱️ 真实批次耗时

5 个视频 · 7.5 小时录像：

| 阶段 | 耗时 | 你在做什么 |
|---|---|---|
| 0–1 &nbsp;抽样 + 抽帧 | ~20 分钟 | 给每个视频选模式 |
| 2 &nbsp;&nbsp;&nbsp;whisper（medium + 偶尔 large-v3） | 4–5 小时 | 干别的事 |
| 3 &nbsp;&nbsp;&nbsp;对齐 | 秒级 | — |
| 4 &nbsp;&nbsp;&nbsp;LLM 清洗（2 并发） | ~15 分钟 | 喝杯咖啡 |

> 🧑‍💻 &nbsp;**用户实际投入约 10 分钟。**

---

## 🏗️ 架构

四个小工具，不是一个大命令。每个都能独立跑、独立重试、独立替换。

| 阶段 | 工具 | 产出 |
|:---:|---|---|
| ① | `slidoc frames`  （包 `ffmpeg`） | `frames/k_NNNN.jpg` + `frame_log.txt` |
| ② | `slidoc transcribe`  （包 `whisper-cli`） | `subtitles/N-title.srt` |
| ③ | `slidoc align`  （Python） | `raw_segments.json` |
| ④ | LLM subagent + [`cleanup-prompt.md`](templates/cleanup-prompt.md) | `video-doc.md` |

第四阶段**刻意不内置**——不同用户用不同 LLM、不同模型、不同配额。Prompt 模板写得完整、清洗规则验证过，复制粘贴即可。如果你用 Claude Code，bundled skill 替你做派发。

---

## 📐 四条铁律（踩坑换来的）

1. 🎯 &nbsp;**抽帧前先抽样确认视频格式。** `slidoc inspect` 让你不用浪费一小时跑错模式。
2. 🚨 &nbsp;**whisper 输出永远过质量门控。** 唯一行比率 < 80% → 直接失败 + 推荐 `large-v3`。
3. 🚧 &nbsp;**清洗 subagent 并发上限 = 2。** 3 个并发读 20+ 张图 → OOM。
4. ♻️ &nbsp;**对齐必须幂等。** `slidoc align` 用 mtime 缓存 `raw_segments.json`，对已去重的帧跳过 pHash。

完整失败日志：[docs/lessons-learned.zh-CN.md](docs/lessons-learned.zh-CN.md)

---

## 📖 CLI 速查

```
slidoc inspect    <dir>                       检测视频格式（PPT / Zoom / talking-head）
slidoc frames     <video>  [--mode] [--param] 抽关键帧
slidoc transcribe <video>  [--model]          生成 SRT + 质量门控
slidoc align      <batch>                     生成 raw_segments.json（幂等）
slidoc run        <batch>                     编排所有阶段 + 输出清洗 prompt
slidoc check      <batch>                     验收：产物齐了吗，质量统计
slidoc prompt     <batch>                     打印 stage 4 清洗 prompt
```

每个命令支持 `--help`。

---

## 📊 项目状态

- **v0.1.0** — 一个 7.5 小时批次（5 视频 + 7 章 PPT）实战验证过，产出可用。
- **下一步**：stage 4 可插拔 LLM 后端、英文测试样本、CI 跑 30 秒端到端 smoke 测。见 [docs/roadmap.zh-CN.md](docs/roadmap.zh-CN.md)。

---

## 🤝 贡献

欢迎 PR——请先读 [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)。项目小而聚焦，大改动先开 issue。

## 📄 许可证

[MIT](LICENSE)

## 🙏 致谢

- [**ffmpeg**](https://ffmpeg.org/) — 关键帧 / 音频抽取
- [**whisper.cpp**](https://github.com/ggerganov/whisper.cpp) — 本地语音转文字
- [**Pillow**](https://python-pillow.org/) — pHash 帧去重
- 在一个 7.5 小时的真实私域培训批次上验证——那个项目暴露了这条流水线现在能扛住的每一种失败模式。
