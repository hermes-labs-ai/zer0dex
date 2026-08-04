# Changelog

All notable changes to zer0dex are documented here.

## [0.0.10] - 2026-08-04

### Changed
- Improved the public README, package description, keywords, project links, and
  Hermes Labs attribution so the local dual-layer memory pattern is easier to
  understand and discover.
- Added GitHub CI, contribution and security guidance, issue templates,
  Dependabot configuration, and a pre-commit configuration.
- Replaced private evaluation fixtures and workspace examples with synthetic
  equivalents while preserving the public evaluation mechanics.
- Added credential-free PyPI publishing through GitHub Actions trusted
  publishing.

### Evidence boundary
- This release packages documentation, metadata, repository hygiene, and
  privacy improvements already present on `main`. It does not change the core
  memory runtime or extend the benchmark claims from 0.0.9.

## [0.0.9] - 2026-03-28

### Added
- `zer0dex check` command — validates Ollama connectivity, required models, and Python dependencies before init/seed
- Test suite (37 tests covering CLI, seed logic, and server endpoints)

### Changed
- README updated with CLI-based quick start (replaces direct `python` invocations)

## [0.0.8] - 2026-03-11

### Added
- Initial public release
- Dual-layer memory architecture (compressed index + vector store)
- CLI with `init`, `seed`, `serve`, `query`, `status`, `add` commands
- HTTP memory server with `/query`, `/add`, `/health` endpoints
- Evaluation suite (n=97): 91.2% recall, 87% pass rate, 80% cross-reference accuracy
- Markdown chunking and seeding pipeline

### Fixed
- Removed deprecated license classifier for setuptools PEP 639 compatibility (0.0.8 patch)
