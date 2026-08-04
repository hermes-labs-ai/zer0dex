# Compatibility and migration (0.1.x developer preview)

The package metadata accepts Python 3.11 and later, but the supported
developer-preview path is CI-tested on Python 3.11 and 3.12. Other Python
versions may work but are not a tested compatibility promise.

The runtime needs local `mem0ai`, `chromadb`, the Python `ollama` client, and
an Ollama service with an embedding model plus an extraction model. The default
models are `nomic-embed-text` and `mistral:7b`. `zer0dex check` is the
authoritative local prerequisite test; `seed` and `serve` do not fall back to
a hosted provider.

Stores are local Chroma directories and `.zer0dex.json` configuration files.
Back up both before changing dependencies, models, collection names, or store
locations. A store produced with a different embedding model should be treated
as a migration boundary and re-seeded rather than assumed comparable.

Within the 0.1.x developer-preview line, changes should be additive where
practical. Before a breaking CLI option, configuration key, HTTP response
shape, default model, or on-disk-store expectation is removed or changed,
publish a migration note that states the affected versions, replacement, and
re-seed or rollback step. The preview makes no compatibility promise for
undocumented internal mem0 or Chroma implementation details.
