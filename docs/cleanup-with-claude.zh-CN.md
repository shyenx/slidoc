# Stage 4 — 用 Claude Code 做清洗

[English](cleanup-with-claude.md) · [中文](cleanup-with-claude.zh-CN.md)

`slidoc` 故意不把最终的 LLM 清洗自动化。本页说明用 **Claude Code** 做清洗时的推荐工作流，以及 bundled skill 怎么用。

## 为什么 stage 4 不内置进 slidoc

- 不同用户用不同 LLM 提供方、不同模型版本、不同配额。
- PPT 图是视觉重型素材，对速率限制敏感；合适的并发取决于你的套餐。
- 清洗是整条流水线里唯一需要 prompt 工程的步骤；做成"复制粘贴的可审计 artifact"比黑盒更好。

## bundled Claude Code skill

Repo 自带一个 skill 在 `.claude/skills/lecture-video-to-doc/`（运行 `make install-skill` 会软链到你的用户级 skills 目录）。在 Claude Code 里说"把这些讲座视频整理成 Markdown"之类的话，skill 会给 Claude 提供：

- 四阶段流水线的简短描述
- `slidoc inspect | frames | transcribe | align` 的指针
- Stage 4 的清洗 prompt 模板
- 并发和内存规则

## 推荐工作流

stage 1-3 跑完，每个视频已经产出 `video-doc/videos/<N-title>/raw_segments.json` 之后：

1. **看每个视频的段数。**

   ```bash
   slidoc check /path/to/video-doc
   ```

2. **定并发。** 按 [docs/lessons-learned.zh-CN.md](lessons-learned.zh-CN.md#3-朴素并行清洗--oom-杀)：
   - ≤ 15 段：可与另一个 ≤ 15 段的视频两两并行
   - 15–25 段：单独跑
   - > 25 段：单独跑，并在 prompt 里加粗强调 "Read each frame ONE AT A TIME"

3. **生成 prompt。**

   ```bash
   slidoc prompt /path/to/video-doc
   ```

   每个视频打印一份已填好占位符的清洗 prompt，里面是确切的 `raw_segments.json` 路径和确切的输出文件路径。

4. **在 Claude Code 里派 agent。** 把每个 prompt 发给 `general-purpose` subagent（`run_in_background: true`）。agent 读 JSON、顺序读帧、写 `video-doc.md`。

5. **验收。**

   ```bash
   slidoc check /path/to/video-doc
   ```

   每个视频都应该有 `doc=XXkB`。打开一两个 `video-doc.md` 抽查，对照原 SRT 看看有没有错删。

## 用别的 LLM

[`templates/cleanup-prompt.md`](../templates/cleanup-prompt.md) 里的 prompt 对提供方无关。换到别的 LLM 上需要：

- 模型能读本地路径图片（或支持 inline 上传）。
- 模型能按你指定路径写文件。
- 守住"并发 ≤ 2"——OOM 风险在 agent runtime，不在 LLM API。
