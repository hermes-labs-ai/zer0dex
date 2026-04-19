# AGENTS.md

`zer0dex` is a local dual-layer memory architecture for AI agents.

## Use it for

- giving agents a compressed markdown memory index plus semantic retrieval
- seeding local memory from markdown or notes
- querying memory through a local HTTP server before each agent message

## Do not use it for

- hosted memory infrastructure
- compliance or governance controls
- assuming benchmark numbers transfer unchanged to every domain

## Minimal commands

```bash
pip install -e ".[dev]"
zer0dex --help
zer0dex init
python -m pytest tests/ -q
```

## Output shape

- `zer0dex check`: prerequisite validation with pass/fail lines
- `zer0dex seed`: chunk and memory-count progress
- `zer0dex query`: scored memory matches
- `zer0dex status`: health plus memory count

## Success means

- local setup, seeding, serving, and querying all work from the CLI
- tests pass offline with mocked dependencies
- the README quick-start flow matches the actual CLI commands

## Common failure cases

- Ollama or required local models are not installed
- users treat the compressed index as full memory instead of a navigation layer
- teams expect zero tuning across very different memory workloads

## Maintainer notes

- keep benchmark claims tied to the published evaluation docs
- keep the architecture framed as a local pattern and implementation, not a universal memory guarantee
- do not commit local store directories or secrets
