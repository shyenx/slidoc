# 清洗 subagent 提示模板

派 general-purpose agent 时，把下面文本复制进 prompt，替换 `{...}` 占位符。

---

```
You will produce a clean lecture transcript for video {N} — "{TITLE}" by {SPEAKER}.

Inputs:
- Aligned data: `{VDIR}/raw_segments.json` ({N_SEGMENTS} segments)
  Each item has {idx, ts (HH:MM:SS), frame (relative path), raw (concatenated SRT lines for this frame's time window)}.
- PPT frames: `{VDIR}/frames/k_NNNN.jpg` (or f_NNNN.jpg)

Output (Write tool, single file, overwrite if exists):
`{VDIR}/video-doc.md`

Cleaning rules for each segment's `raw`:
1. **Remove fillers**: 嗯、啊、呃、那个、就是说、我想说的是、对吧、是吧、哦、无意义的"然后".
2. **Remove interaction & chitchat**: "大家有没有听到", "在吗", "能听到吗", "扣个1", "等下我喝口水", "稍等", "我刚说到哪了", "OK 好的".
3. **Remove technical disruption**: "有点卡", "网络不太好", "我重新说一下", "麦克风".
4. **Remove whisper hallucinations**: identical sentence repeated 3+ times in a row → keep ONE occurrence (or delete entirely if it's clearly nonsense).
5. **PRESERVE everything substantive**: concepts, frameworks, steps, numbers, names, examples, quotes, case stories, audience-relevant Q&A, references to slides.
6. **Smooth into 1-3 short paragraphs** of natural Chinese. Do NOT paraphrase aggressively — keep the speaker's voice.
7. If a segment is essentially empty after cleaning, output: `> （此段无实质内容）`
8. **Read each frame image ONE AT A TIME (sequential, NOT parallel)** to keep memory low. When the speaker references the slide, mention the slide topic naturally in the cleanup.

Document format:
```markdown
# {TITLE}

> 主讲：{SPEAKER}　|　时长：{DURATION}　|　帧数：{N_SEGMENTS}　|　原视频：[MP4]({RELATIVE_PATH_TO_MP4})

## 目录
- [00:00 段 1：xxx](#段-1)
- [01:30 段 2：xxx](#段-2)
- ...

---

<a id="段-1"></a>
## 段 1 · 00:00:00
![](frames/k_0001.jpg)

{cleaned narration}

<a id="段-2"></a>
## 段 2 · 00:01:30
...
```

For TOC labels: 4-8 字 short topic phrase inferred from cleaned narration + frame.

Process segments sequentially. Reply only "DONE" when finished.
```

---

## 并发调度规则

| 帧/段数 | 安排 |
|---|---|
| ≤ 15 | 可与另一个 ≤ 15 段的视频并行（最多 2） |
| 15-25 | **单独跑**（一个 agent） |
| > 25 | **单独跑** + 在 prompt 里加粗强调 "Read images ONE AT A TIME" |

绝不超过 2 个清洗 agent 并发。否则 vision token 内存爆掉。

## 占位符变量

| 变量 | 值（举例） |
|---|---|
| `{N}` | 1 |
| `{TITLE}` | AI 企业培训入门 |
| `{SPEAKER}` | 陈天 |
| `{VDIR}` | `/path/to/video-doc/videos/1-chentian-ai-training-intro` |
| `{N_SEGMENTS}` | 28 |
| `{DURATION}` | 1h33m |
| `{RELATIVE_PATH_TO_MP4}` | `../../../1【教练分享】AI企业培训入门_陈天.mp4` |

## 实战已验证示例（输入 → 输出）

输入 raw（一段口语化原始字幕）：
```
我想说的是 嗯 就是说大家有没有听到 听到的扣个1吧 好 那我接下来就开始讲了
那个 第一步是确定方向 啊 这个方向呢 关键词是大方向、体系化、持续性、思想迭代
对吧 然后 选择比努力更重要
```

期望清洗输出：
```markdown
第一步是确定方向，关键词是大方向、体系化、持续性、思想迭代。选择比努力更重要。
```
