# Changelog

[English](CHANGELOG.md) · [中文](CHANGELOG.zh-CN.md)

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-12

### Added

- Initial public release.
- Four-stage pipeline: keyframe extraction, transcription, alignment, LLM cleanup.
- `slidoc` CLI with sub-commands: `inspect`, `frames`, `transcribe`, `align`, `run`, `check`.
- Idempotent alignment (`raw_segments.json` cache via mtime).
- Quality gate for Whisper SRT output (unique-line ratio).
- Anti-hallucination retry flags for `whisper-cli large-v3`.
- pHash-based frame deduplication with skip-list for fixed-interval extractions.
- Cleanup prompt template for LLM subagents (Claude / GPT / local LLMs).
- Bundled Claude Code skill at `.claude/skills/lecture-video-to-doc/`.
- Battle-tested on 7.5 hours of real Chinese training video (5 videos + 7 PPT chapters).

### Known limitations

- Stage ④ (LLM cleanup) is not automated; user must dispatch their own agent.
- Tested only on Chinese audio so far; English should work but lacks regression fixtures.
- macOS / Apple Silicon primary target. Linux untested but should work.

[Unreleased]: https://github.com/shyenx/slidoc/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/shyenx/slidoc/releases/tag/v0.1.0
