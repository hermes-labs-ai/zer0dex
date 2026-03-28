# AGENTS.md — zer0dex

## Role
You are working on zer0dex, a dual-layer memory architecture for AI agents.
Stack: Python 3.11+, mem0ai, chromadb, ollama (nomic-embed-text, mistral:7b).

## Commands
```bash
pip install -e ".[dev]"          # Install with dev deps
python -m pytest tests/ -v       # Run tests
python eval/evaluate.py          # Full benchmark (n=97, ~5 min)
python eval/evaluate_small.py    # Quick benchmark (n=10, ~30 sec)
zer0dex serve                    # Start memory server (port 18420)
zer0dex seed --source docs/      # Seed from markdown files
zer0dex query "test query"       # Query the running server
zer0dex status                   # Health check
```

## Project Structure
```
src/zer0dex/
  __init__.py      — Package init, version
  server.py        — HTTP memory server (POST /query, POST /add, GET /health)
  seed.py          — Markdown → vector store seeder
  cli.py           — CLI entry point (check/init/seed/serve/query/status/add)
  hook_example.ts  — TypeScript integration example
eval/
  evaluate.py      — Full benchmark suite (n=97)
  evaluate_small.py — Quick benchmark (n=10)
  README.md        — Evaluation methodology
```

## Code Style
- Type hints on all function signatures
- Google-style docstrings on public functions
- No `print()` in library code (use logging)
- Constants at module top, UPPER_SNAKE_CASE

## Testing
- The benchmark is the source of truth: don't break 91.2% recall
- Run quick eval (`evaluate_small.py`) for fast iteration
- Run full eval before any PR that touches memory logic

## Git Workflow
- Branch names: `feat/`, `fix/`, `docs/`, `refactor/`
- Commit messages: imperative mood ("Add hook endpoint" not "Added")
- Never commit: `.env`, `*.key`, `.zer0dex/`, `.mem0_chroma/`

## Boundaries
- ✅ **Always:** run lint before committing, update CHANGELOG.md for user-facing changes
- ⚠️ **Ask first:** pyproject.toml changes, new dependencies, eval modifications
- 🚫 **Never:** modify eval ground truth data, commit API keys or local DB files, change recall metrics without re-running full benchmark
