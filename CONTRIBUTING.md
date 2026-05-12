# Contributing to slidoc

[English](CONTRIBUTING.md) · [中文](CONTRIBUTING.zh-CN.md)

Thanks for considering a contribution. slidoc is small, focused, and battle-tested — the best way to help is to make it more reliable, more portable, or extend it to formats it doesn't yet handle.

## Before you start

1. **Open an issue first** for non-trivial changes. Describe the failure you hit, or the workflow you want to enable.
2. **Read [docs/lessons-learned.md](docs/lessons-learned.md)** — every rule and default in the pipeline corresponds to a real production failure. Don't relax one without reading why it's there.

## Development setup

```bash
git clone https://github.com/shyenx/slidoc.git
cd slidoc
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# External tools
brew install ffmpeg      # or apt install
# whisper.cpp: follow https://github.com/ggerganov/whisper.cpp
```

## Running tests

```bash
pytest                    # unit tests
pytest -v tests/integration/   # integration (requires ffmpeg + a sample mp4)
ruff check slidoc tests   # lint
ruff format slidoc tests  # formatter
```

The CI runs the same commands.

## Project layout

```
slidoc/                 # Python package
├── __init__.py
├── cli.py              # `slidoc` entry point + sub-command dispatch
├── inspect.py          # video format detection
├── frames.py           # ffmpeg keyframe extraction
├── transcribe.py       # whisper.cpp wrapper + quality gate
├── align.py            # SRT × frames alignment
├── check.py            # batch verification
└── prompt.py           # cleanup-prompt template emit

scripts/                # standalone shell scripts (no Python needed)
templates/              # LLM cleanup prompt template
docs/                   # additional documentation
tests/                  # unit + integration tests
examples/               # tiny sample data for tests / demos
```

## Style

- **Python**: ruff-formatted, type hints on public APIs, docstrings on `cli.py` sub-commands.
- **Shell**: `set -euo pipefail` at the top of every script; `shellcheck` clean.
- **Markdown**: `mdformat` for consistency.

## Adding a new feature

1. Open an issue.
2. Write a failing test (or document the manual reproduction case).
3. Implement.
4. Update [CHANGELOG.md](CHANGELOG.md) under `## [Unreleased]`.
5. Open a PR. Squash before merge.

## Things we'd love help with

- **English-language fixture** under `examples/` (10–30 sec mp4 + slides).
- **Whisper backend abstraction** so users can plug in `faster-whisper`, `whisperx`, or cloud APIs.
- **Linux CI matrix** (current CI is macOS-only because Whisper Metal acceleration is macOS-specific).
- **HTML output renderer** that turns the Markdown into a browsable site with searchable transcripts.
- **End-to-end smoke test** that runs the full pipeline on the included 30-sec sample within 5 minutes.

## Code of Conduct

Be kind, be specific, be brief. We follow the [Contributor Covenant](https://www.contributor-covenant.org/) v2.1.
