# 更新日志

[English](CHANGELOG.md) · [中文](CHANGELOG.zh-CN.md)

本项目的所有重要改动都记录在此。格式遵循 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)。

## [Unreleased]

## [0.1.0] - 2026-05-12

### 新增

- 首个公开版本。
- 四阶段流水线：关键帧抽取、转字幕、对齐、LLM 清洗。
- `slidoc` CLI 子命令：`inspect`、`frames`、`transcribe`、`align`、`run`、`check`。
- 幂等对齐（基于 mtime 的 `raw_segments.json` 缓存）。
- whisper SRT 质量门控（唯一行比率）。
- `whisper-cli large-v3` 抗幻觉重试参数。
- 基于 pHash 的帧去重，固定间隔抽帧自动跳过。
- 给 LLM subagent（Claude / GPT / 本地 LLM）用的清洗 prompt 模板。
- bundled Claude Code skill（`.claude/skills/lecture-video-to-doc/`）。
- 在 7.5 小时真实中文培训视频上实战验证过（5 个视频 + 7 章 PPT）。

### 已知限制

- Stage 4（LLM 清洗）未自动化；用户需自己派 agent。
- 目前只在中文音频上测过；英文应该能用但缺回归样本。
- macOS / Apple Silicon 是主要目标平台。Linux 未测但理论可用。

[Unreleased]: https://github.com/shyenx/slidoc/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/shyenx/slidoc/releases/tag/v0.1.0
