# 贡献指南

[English](CONTRIBUTING.md) · [中文](CONTRIBUTING.zh-CN.md)

感谢愿意贡献。slidoc 小而聚焦、踩过坑、有产出——最有价值的贡献是让它**更可靠、更可移植**，或者让它支持目前还处理不了的格式。

## 动手前

1. **非小改动先开 issue**。说清你踩到的失败模式，或者你想启用的工作流。
2. **读 [docs/lessons-learned.zh-CN.md](docs/lessons-learned.zh-CN.md)**。流水线里的每条默认值都对应一个真实失败案例。改默认值之前先看看它为什么是这样。

## 开发环境

```bash
git clone https://github.com/shyenx/slidoc.git
cd slidoc
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 外部依赖
brew install ffmpeg        # 或 apt install
# whisper.cpp：见 https://github.com/ggerganov/whisper.cpp
```

## 跑测试

```bash
pytest                       # 单测
pytest -v tests/integration/ # 集成（需 ffmpeg + 一个样本 mp4）
ruff check slidoc tests      # lint
ruff format slidoc tests     # 格式
```

CI 跑的就是这几行。

## 项目结构

```
slidoc/                 # Python 包
├── __init__.py
├── cli.py              # `slidoc` 入口 + 子命令派发
├── inspect.py          # 视频格式检测
├── frames.py           # ffmpeg 抽帧
├── transcribe.py       # whisper.cpp wrapper + 质量门控
├── align.py            # SRT × 帧对齐
├── check.py            # 批次验收
└── prompt.py           # 清洗 prompt 模板生成

scripts/                # 独立 shell 脚本（不需要 Python）
templates/              # LLM 清洗 prompt 模板
docs/                   # 额外文档
tests/                  # 单测 + 集成测试
examples/               # 小样本 / 演示数据
```

## 风格

- **Python**：用 ruff 格式化；公共 API 加类型注解；`cli.py` 子命令加 docstring。
- **Shell**：每个脚本顶部 `set -euo pipefail`；过 `shellcheck` 检查。
- **Markdown**：用 `mdformat` 保持一致。

## 加新功能

1. 开 issue。
2. 先写失败测试（或写清楚手工复现步骤）。
3. 实现。
4. 在 [CHANGELOG.md](CHANGELOG.md) / [CHANGELOG.zh-CN.md](CHANGELOG.zh-CN.md) 的 `## [Unreleased]` 下记一笔。
5. 开 PR。合并前 squash。

## 我们最想要的贡献

- **英文回归样本** 放在 `examples/`（10–30 秒 mp4 + PPT）。
- **whisper 后端抽象层**，让用户能换 `faster-whisper`、`whisperx`、云端 API。
- **Linux CI 矩阵**（当前 CI 仅 macOS，因为 Whisper Metal 加速是 macOS 特有）。
- **HTML 输出渲染器**：把 Markdown 转成可浏览的、可搜索字幕的静态网站。
- **端到端 smoke 测**：在 30 秒样本上 5 分钟内跑完整条流水线。

## 行为准则

友善、具体、简洁。遵循 [Contributor Covenant](https://www.contributor-covenant.org/) v2.1。
