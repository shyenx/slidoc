# 踩坑笔记

[English](lessons-learned.md) · [中文](lessons-learned.zh-CN.md)

> 流水线里**每条规则为什么存在**。任何想拆掉某条护栏的人，请先读对应这条规则的失败案例。

本文记录我们在一个真实生产批次（5 个视频，共 7.5 小时）里踩过的所有失败模式。流水线的默认值全部对应到这些事故。

## 1. whisper-medium 在长中文音频上幻觉

**症状。** 一段 1h33m 视频（培训入门讲座）前 5 分钟转写正常，之后崩成同一句重复 88 分钟：

```
00:05:32  听到的扣个1吧
00:05:34  听到的扣个1吧
00:05:36  听到的扣个1吧
... （之后又重复 2200 多次直到结束） ...
```

最终 SRT **2575 行里只有 7 行是唯一的**。实际课程内容一句没捕到。

**机理。** 长静音段或低信息量段会把解码器推进一个"吸引子状态"，某个 token 序列开始统治输出。`medium` 比 `large-v3` 更容易陷进去；长讲座视频里观众等待、呼吸停顿、背景噪声都是触发器。

**修正。** `slidoc transcribe` 必跑质量门控：

```python
unique_ratio = unique_lines / total_lines
if unique_ratio < 0.80:   # 经验阈值
    sys.exit(4)           # 调用方应该用 --model large-v3 重试
```

`--model large-v3` 时自动加抗幻觉参数：

```bash
whisper-cli -et 2.0 -lpt -0.8 -mc 2.0 ...
```

这些参数收紧 whisper.cpp 内部 entropy / log-probability / compression-ratio 三道阈值，更早触发"切换更高解码温度"的 fallback，从而摆脱循环吸引子。

加上这些参数后同一段 V1 音频重新转，**97% 唯一行**，内容全在。

## 2. Scene-detect 在 Zoom 录屏上失效

**症状。** 同一段视频（V1）其实是 Zoom 屏幕分享录制：右侧一个小 PPT 面板，中间是聊天侧栏一直在滚，下面一排摄像头小窗口。scene-detect 阈值 0.30 给了 **194 个关键帧 / 93 分钟视频**——绝大多数只是聊天又冒出一条新消息。

**机理。** ffmpeg scene-detect 算的是全局像素差。任何独立于 PPT 切换而变化的元素（聊天滚动、摄像头小窗、鼠标光标、画中画）都会触发假阳性。把阈值抬到 0.50 帧数降到 90——还是大多无用。

**修正。** 两层：

1. **`slidoc inspect` 在 60s / 5m / 30m 三个时间点抽样**，让用户用肉眼判断视频格式，分类成：
   - **(A) PPT 录屏** → `--mode scene`
   - **(B) Zoom 多面板** → `--mode fps --interval 90`
   - **(C) 纯主讲人脸** → 别走这条流水线，只产 SRT 即可
2. **fps 固定间隔模式（`--mode fps`）** 每 N 秒采一张，完全忽略像素差。1.5h 演讲，90s 一帧 = 62 帧，正好够把讲稿锚定到时间轴上而不洪水。

V1 改成 `--mode fps --interval 90` 后帧数从 194 降到 62，pHash 再去重剩 28 张有意义的帧。

## 3. 朴素并行清洗 → OOM 杀

**症状。** 第一次尝试：派 14 个 Claude Code subagent 同时跑，每个要读 7-19 张 PPT 图、产清洗讲稿。几分钟内 launcher 被 OOM kill；6 个任务报"Agent killed"。

**机理。** 每个 agent 把 PPT 图载入视觉 token 上下文（每张约 1500-3000 token）。14 个并发，每个平均 10 张 → 累积内存压力把宿主 swap 打满。

**修正。** 三条硬规则：

1. **同时最多 2 个清洗 agent。**
2. **段数 > 25 的视频单独跑。** 清洗 prompt 模板的批次建议见 [templates/cleanup-prompt.md](../templates/cleanup-prompt.md)。
3. **prompt 里明令禁止 agent 内部并行：** "Read each frame image ONE AT A TIME (sequential, NOT parallel)"。没这句的话 agent 会自己同时读所有图，单 agent 内复现 OOM。

加上这三条后，峰值内存约等于两个 agent 的合并大小（我们生产批次测得约 2 GB）。

## 4. 对齐脚本不幂等

**症状。** `align_frames_srt.py` 跑两次结果不同（第二次错）。第一次：62 帧输入，pHash 留 28，重命名 `k_0001.jpg ... k_0028.jpg`。第二次：找到 28 张 jpg + `frame_log.txt` 里 62 个时间戳，又跑一遍 pHash，把幸存的 28 张映射到**前 28 个**时间戳——结果 90 分钟音频被压在 40 分钟幻灯片上。

**机理。** 会改输入文件（重命名、删除）的流水线，不思考状态就反复跑必出问题。

**修正。** `slidoc.align.process_video` 同时做两件事：

1. **mtime 缓存：** `raw_segments.json` 比 `frame_log.txt` 和 SRT 都新就跳过。
2. **状态感知去重：** 帧名以 `k_NNNN.jpg` 开头就视为已去重过的产物，**不再 pHash**。

`slidoc align` 现在可以被脚本、重试逻辑、人类好奇心反复触发都安全。

## 5. ffmpeg `showinfo` 偶尔多记一帧

**症状。** 某个视频 ffmpeg 写出 12 张 jpg，但 showinfo log 记了 13 个 `pts_time:`。朴素对齐崩在这个 off-by-one 上。

**机理。** scene-detect + showinfo 会偶尔输出一行最终帧的 `pts_time` 行，但实际不写出 jpg（编码器缓冲产物）。

**修正。** `slidoc.align` 始终用 `min(len(times), len(frames))` 并 warn。最多丢视频末尾 1 帧，可接受。

## 6. 别信文件名

**症状。** 一个标题叫"讲师介绍"的视频实际全程是摄像头拍人脸，根本没有幻灯片。差点把整条流水线都跑完才发现。

**修正。** Stage 0（`slidoc inspect`）强制执行。每个视频 3 秒抽样，胜过 30 分钟浪费 whisper 转写一个根本不适合本流水线的视频。

## 7. 清洗过于激进会丢内容

**症状。** 早期 cleanup prompt 写的是"summarize this segment"——agent 过度压缩，删掉了具体人名、数字、案例细节。

**修正。** 现在 prompt 模板用精确动词：

> **PRESERVE** everything substantive: concepts, frameworks, steps, numbers, names, examples, quotes, case stories, audience-relevant Q&A, references to slides.
> Smooth into 1-3 short paragraphs of natural prose. Do NOT paraphrase aggressively — keep the speaker's voice.

[templates/cleanup-prompt.md](../templates/cleanup-prompt.md) 里的清洗前后对照样例锚定期望的口吻。
