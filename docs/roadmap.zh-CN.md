# 路线图

[English](roadmap.md) · [中文](roadmap.zh-CN.md)

> 截至 v0.1.0 的状态。

## v0.2 — 健壮性

- [ ] **whisper 后端抽象。** 支持 `faster-whisper`、`whisperx`、云 API（OpenAI、AssemblyAI）。当前 `slidoc transcribe` 只 shell out 到 `whisper-cli`。
- [ ] **英文回归样本。** 30 秒带 PPT + 主讲的样本 mp4 + 一份金标 `video-doc.md`，CI 跑完整流水线对照 diff。
- [ ] **Linux smoke 测。** 在没有 Metal 加速的环境下验证 `slidoc run` 能跑；写一份 Linux whisper 构建说明。
- [ ] **可配置目录布局。** 把硬编码的 `subtitles` / `videos` 子目录名抽到 `slidoc.toml` 或 CLI flag。
- [ ] **每视频 override 文件。** 让 batch 自带 `slidoc.batch.yaml`，把每个视频映射到自己的抽帧模式 + 阈值。

## v0.3 — 用户体验

- [ ] **HTML 输出。** 把 `video-doc.md` 渲染成可浏览的、字幕可搜索的静态站点，时间戳点击能 seek 原视频。
- [ ] **Web UI。** 可选 Gradio / Streamlit 前端，给非 CLI 用户。
- [ ] **`inspect` 内联预览。** 起一个快速 HTML 预览展示每个视频的 3 张样图，不用用户自己捞文件路径。
- [ ] **一键升级路径。** 检测到低质量 SRT 时自动建议 `slidoc transcribe ... --model large-v3`。

## v0.4 — 可插拔清洗

- [ ] **`slidoc cleanup` 命令** 通过 provider plugin 派发清洗（Claude Code subagent、Anthropic SDK 直调、OpenAI、Ollama 本地 LLM）。
- [ ] **Diff 模式** 让用户能看到清洗过程中删了什么、留了什么。
- [ ] **成本估算** 跑清洗之前先估钱。

## 远期想法

- **说话人 diarization** 用于多嘉宾论坛（标注 `[Speaker A]: ...`）。
- **多模态接地**：让清洗 LLM 标注某段结论是从哪张幻灯片来的。
- **跨视频索引** 自动把同一批讲座里相关概念互相链接。

要上面任何一项的话，先开 issue 描述你的用例再发 PR。
