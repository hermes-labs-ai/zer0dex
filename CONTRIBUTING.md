# Contributing to zer0dex

Thanks for your interest in contributing!

## Getting Started

```bash
git clone https://github.com/hermes-labs-ai/zer0dex.git
cd zer0dex
pip install -e ".[dev]"
pytest tests/ -v
```

## Requirements

- Python 3.11+
- [Ollama](https://ollama.ai) with `nomic-embed-text` and `mistral:7b` (for integration testing)

## Making Changes

1. Fork the repo and create a branch from `main`
2. Write tests for your changes
3. Run `pytest tests/ -v` — all 37 tests must pass
4. Submit a pull request

## Code Style

- Type hints on function signatures
- Google-style docstrings on public functions
- Constants at module top, UPPER_SNAKE_CASE

## Reporting Bugs

Use the [bug report template](https://github.com/hermes-labs-ai/zer0dex/issues/new?template=bug_report.yml).
