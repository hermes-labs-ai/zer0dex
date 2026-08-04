# zer0dex Evaluation

## Methodology

The evaluation compares three memory retrieval approaches across n=97 test cases:

- **Mode A (Flat File):** MEMORY.md compressed index only, no vector retrieval
- **Mode B (zer0dex):** MEMORY.md index + mem0 vector store retrieval (the dual-layer approach)
- **Mode C (Full RAG):** mem0 vector store only, no compressed index

### Test Case Generation

97 test cases across 3 categories:
- **Direct recall** (n=82): Single-fact retrieval ("What is X?")
- **Cross-reference** (n=10): Multi-fact connections ("How does X relate to Y?")
- **Negative** (n=5): Questions about facts NOT in memory (tests false positive rejection)

Test cases are generated from the actual memory store contents, then manually verified for correctness.

### Scoring

Each test case is scored on recall (0-100%):
- Does the retrieved context contain the relevant facts?
- Are cross-references correctly connected?
- Are negative queries correctly rejected (no hallucinated matches)?

### Hardware

Tested on MacBook Pro M-series, 48GB RAM:
- **Ollama:** nomic-embed-text for embeddings, mistral:7b for extraction
- **ChromaDB:** Local vector store, 86 memories
- **Latency:** Measured per-query, averaged across all test cases

## Results

| Metric | Flat File (A) | Full RAG (C) | zer0dex (B) |
|---|---|---|---|
| Average recall | 52.2% | 80.3% | **91.2%** |
| ≥75% pass rate | 41% (40/97) | 77% (75/97) | **87% (84/97)** |
| Avg latency | 0ms | 13.2ms | **13.6ms** |
| Token overhead | 782 | 104 | **886** |

### By Question Type

| Type | Flat File | Full RAG | zer0dex |
|---|---|---|---|
| Direct recall (n=82) | 47.2% | 84.3% | **92.1%** |
| Cross-reference (n=10) | 70.0% | 37.5% | **80.0%** |
| Negative (n=5) | 100% | 100% | **100%** |

### Head-to-Head

- zer0dex vs Flat File: **47 wins, 50 ties, 0 losses**
- zer0dex vs Full RAG: **14 wins, 83 ties, 0 losses**

Note: The 80.3% overall vs 84.3% direct recall difference is because overall includes cross-reference (37.5%) and negative (100%) categories which pull the average in different directions.

## Running the Evaluation

```bash
# Full evaluation (n=97, ~5 minutes)
python eval/evaluate.py

# Quick evaluation (n=10, ~30 seconds)
python eval/evaluate_small.py
```

### Requirements

- Ollama running with `nomic-embed-text` and `mistral:7b`
- mem0ai and chromadb installed
- A seeded zer0dex memory store

## Benchmark workload and transfer limits

The published workload is the 97 manually verified questions described above,
drawn from one agent's 86-memory local store. It is useful for reproducing the
reported comparison on that source and hardware setup; it is not a general
benchmark of all agent-memory workloads. The questions overlap the evaluated
store, so the result does not establish performance on an unseen corpus,
different agents, larger stores, another embedding/extraction model, or a
hosted deployment.

To compare a changed runtime, record the exact store, question set, models,
hardware, and run count. Do not transfer the table's recall, latency, token,
or head-to-head values into a claim about another domain without a separately
reproduced evaluation.

## Limitations

- Single agent's memory store (86 memories)
- Test cases derived from the same memory store (potential overfitting)
- Not tested at scale (thousands of memories)
- Hardware-specific latency numbers
- No confidence intervals (single-run evaluation)
- Results are workload-specific and should not be treated as a universal
  retrieval, safety, or production-performance guarantee

We encourage replication on different memory stores and welcome contributions to the evaluation suite.
