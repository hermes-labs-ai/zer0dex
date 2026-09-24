---
name: zer0dex
description: Use when you need a local dual-layer memory pattern for an AI agent — a compressed markdown index for cross-reference queries plus a local vector store queried before each model call — and want a reference implementation to seed and query without a hosted service. Local-first, Alpha.
license: Apache-2.0
compatibility: Requires Python 3.10+ and a local Ollama instance with an embedding model; installs via `pip install zer0dex` or runs standalone via `uvx zer0dex`. No hosted service required.
---

# zer0dex

zer0dex is a local dual-layer memory pattern for AI agents: a compact,
human-readable markdown index paired with semantic retrieval from a local
vector store, queried before each message. It targets cross-project recall
where flat memory files or vector-only RAG fall short. Reference
implementation, local-first, Alpha (0.1.x line).

## Use it for

- Combining a compressed markdown memory index with vector retrieval in one
  local loop
- Running a local memory server an agent host queries before model calls
- Seeding and querying persistent memory without standing up a hosted service
- Prototyping the dual-layer (index + vector) pattern before adopting a
  heavier memory stack

## Do not use it for

- A hosted or multi-tenant memory platform
- A governance or safety layer for memory content
- Proof that any benchmark result transfers unchanged to a different corpus
  or workload

## Quickstart

```bash
pip install zer0dex
zer0dex check
```

Or without installing, via [uv](https://docs.astral.sh/uv/):

```bash
uvx zer0dex check
```

Real output from a working local setup (Ollama running, models pulled):

```
✅ Ollama is running at http://localhost:11434
✅ Model present: nomic-embed-text
✅ Model present: mistral:7b
✅ mem0ai is importable
✅ chromadb is importable
✅ Python Ollama client is importable
```

## Commands

```
zer0dex check              # validate prerequisites (Ollama, models, mem0ai, chromadb)
zer0dex init                # initialize a new memory store
zer0dex seed --source <path> # seed from markdown files
zer0dex serve               # start the local memory server
zer0dex query "<text>"      # query memories
zer0dex status              # check server health
```

## Output shape

- `check`: per-prerequisite pass/fail lines (Ollama reachability, model
  presence, library importability)
- `serve` / `status`: local HTTP health and query results
- `query`: ranked memory matches from the vector store

## Common gotchas

- `check` fails closed if Ollama isn't running locally or the required models
  (`nomic-embed-text`, an LLM tag) aren't pulled — read the specific failing
  line, it names the missing prerequisite.
- This is a reference pattern, not a managed service: there is no built-in
  multi-user isolation or remote auth.
- 0.1.x is a developer-preview compatibility line; check `docs/compatibility.md`
  before pinning across upgrades.

## More

Full docs, CLI/HTTP reference, and compatibility policy:
https://github.com/hermes-labs-ai/zer0dex
