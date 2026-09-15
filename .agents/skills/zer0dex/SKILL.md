---
name: zer0dex
description: Use when a long-running local agent needs persistent memory across sessions — a compact, human-editable markdown index paired with semantic retrieval from a local vector store, queried over HTTP before each message. Local-first, requires Ollama; plain HTTP server, not MCP.
license: Apache-2.0
compatibility: Requires Python 3.11 or 3.12; installs via pip. Needs Ollama running locally at http://localhost:11434 with the nomic-embed-text and mistral:7b models pulled.
---

# zer0dex

zer0dex gives a long-running agent local recall without forcing every detail
into its prompt: a small, human-readable markdown memory index paired with
semantic retrieval from a local mem0/Chroma vector store. It supplies a CLI
and a local HTTP server; wiring the query into model calls is an agent-host
step.

## Use it for

- Persisting agent memory across sessions in a plain markdown file plus a
  local vector store
- Querying stored memories over HTTP (`POST /query`) before a model call, and
  adding new memories (`POST /add`)
- Standing up a project-local memory server for one working directory
  (`.zer0dex.json` / `.zer0dex/`)
- Inspecting or hand-editing the markdown index when a flat `MEMORY.md` has
  grown too large to keep in context

## Do not use it for

- Hosted or multi-tenant memory infrastructure
- A complete agent framework or an automatic pre-message hook — the host
  still decides when to call `/query` and how to use the results
- A compliance, access-control, or governance system
- Treating retrieved memories as verified truth — they are untrusted data
  like any other retrieved content

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install zer0dex

ollama pull nomic-embed-text
ollama pull mistral:7b

printf '%s\n' '# Memory' '## Project Atlas' '- Deployment target: staging' > MEMORY.md
zer0dex check
zer0dex init
zer0dex seed --source MEMORY.md
zer0dex serve --background
zer0dex query "Where does Project Atlas deploy?"
zer0dex add "Project Atlas deploys from the release branch"
zer0dex status
zer0dex stop
```

## Output shape

- `zer0dex query "..."`: JSON with a `memories` array of `{text, score,
  source}` objects
- `zer0dex status`: reports whether the background server is running
- `zer0dex check`: verifies Ollama and the required models are reachable
  before setup proceeds
- HTTP `POST /query`, `POST /add`, `GET /health` mirror the CLI operations

## Common gotchas

- `zer0dex stop` refuses to signal a PID unless the server proves its
  per-launch identity, so stale state cannot kill an unrelated process.
- The package is Alpha (0.1.x line); expect refinement, and check the
  compatibility policy before pinning a version in automation.
- This is a plain local CLI and HTTP server, not an MCP server.
- Requires a local Ollama install with two specific models pulled first —
  `zer0dex check` catches a missing prerequisite before `init`/`seed` fail.

## More

Full docs, CLI and HTTP references:
https://github.com/hermes-labs-ai/zer0dex
