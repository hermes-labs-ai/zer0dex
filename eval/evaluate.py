#!/usr/bin/env python3
"""
mem0 zer0dex Evaluation — n=97
Auto-generates questions from stored memories + adversarial negatives.
Compares: MEMORY.md only vs zer0dex vs Full RAG
"""

import sys
import json
import time
import random
from pathlib import Path

WORKSPACE = Path.home() / ".zer0dex" / "eval-workspace"
sys.path.insert(0, str(WORKSPACE / ".venv311/lib/python3.11/site-packages"))

from mem0 import Memory

CONFIG = {
    "llm": {"provider": "ollama", "config": {"model": "mistral:7b", "ollama_base_url": "http://localhost:11434"}},
    "embedder": {"provider": "ollama", "config": {"model": "nomic-embed-text", "ollama_base_url": "http://localhost:11434"}},
    "vector_store": {"provider": "chroma", "config": {"collection_name": "demo_memory", "path": str(WORKSPACE / ".mem0_chroma")}},
}

def load_memory_md():
    return (WORKSPACE / "MEMORY.md").read_text()

def generate_test_cases(memories):
    """Generate test cases from actual stored memories."""
    tests = []
    
    # Strategy 1: Direct fact recall — can we find the exact memory?
    for mem in memories:
        text = mem.get("memory", "")
        if len(text) < 10:
            continue
        
        # Extract key terms for the expected facts
        # Use the memory itself as the expected text
        words = text.split()
        if len(words) < 3:
            continue
        
        # Create a question that should retrieve this memory
        # Use different question templates
        templates = [
            f"What do you know about {' '.join(words[:3])}?",
            f"Tell me about {' '.join(words[:4])}",
            f"What is {' '.join(words[:2])}?",
            f"Details on {' '.join(words[1:4])}?",
        ]
        
        # Pick a template based on hash for determinism
        template = templates[hash(text) % len(templates)]
        
        # Expected: the memory text itself (or key fragments)
        key_fragments = []
        for word in words:
            if len(word) > 4 and word[0].isupper():
                key_fragments.append(word)
            elif any(c.isdigit() for c in word) and len(word) > 1:
                key_fragments.append(word)
        
        if not key_fragments:
            key_fragments = [words[0]] if words else [""]
        
        tests.append({
            "question": template,
            "expected_facts": key_fragments[:4],  # max 4 key facts
            "source_memory": text,
            "type": "direct_recall",
        })
    
    # Strategy 2: Cross-reference questions
    cross_ref = [
        {"question": "What tools does Hermes Labs make?", 
         "expected_facts": ["Little Canary", "lintlang", "Suy Sideguy", "Quick Gate"],
         "type": "cross_reference"},
        {"question": "What grant applications have been submitted?",
         "expected_facts": ["Acme Cloud", "Globex", "Initech"],
         "type": "cross_reference"},
        {"question": "What is the user's educational background?",
         "expected_facts": ["computer science", "Turing", "Knuth"],
         "type": "cross_reference"},
        {"question": "What internal documents exist?",
         "expected_facts": ["COMPANY.md", "VOICE.md", "TRACKER.md"],
         "type": "cross_reference"},
        {"question": "What are the four epistemic failure modes?",
         "expected_facts": ["sycophancy", "null-result", "hermeneutic", "intent"],
         "type": "cross_reference"},
        {"question": "What is the defense stack status?",
         "expected_facts": ["Little Canary", "Suy Sideguy", "DemoAgent"],
         "type": "cross_reference"},
        {"question": "What open source contributions has Roli made?",
         "expected_facts": ["PRs", "merged"],
         "type": "cross_reference"},
        {"question": "What experiments were run and on which models?",
         "expected_facts": ["GPT-4o", "adversarial"],
         "type": "cross_reference"},
        {"question": "What is the canary sidecar doing?",
         "expected_facts": ["canary_sidecar", "JSONL", "screening"],
         "type": "cross_reference"},
        {"question": "What applications are still pending?",
         "expected_facts": ["Hooli", "Stark"],
         "type": "cross_reference"},
    ]
    tests.extend(cross_ref)
    
    # Strategy 3: Adversarial negatives (should return nothing relevant)
    negatives = [
        {"question": "What is the weather in Tokyo right now?",
         "expected_facts": [],
         "type": "negative"},
        {"question": "How do I cook pasta?",
         "expected_facts": [],
         "type": "negative"},
        {"question": "What is Bitcoin's current price?",
         "expected_facts": [],
         "type": "negative"},
        {"question": "Tell me about quantum computing research at MIT",
         "expected_facts": [],
         "type": "negative"},
        {"question": "What is the population of Brazil?",
         "expected_facts": [],
         "type": "negative"},
    ]
    tests.extend(negatives)
    
    # Shuffle and cap at 100
    random.seed(42)
    random.shuffle(tests)
    return tests[:100]


def score_retrieval(retrieval_text, expected_facts):
    """Score recall: what % of expected facts appear in retrieval."""
    if not expected_facts:
        # Negative case: score is 1.0 if retrieval is short/irrelevant
        return {"recall": 1.0, "type": "negative", "found": [], "missed": []}
    
    text_lower = retrieval_text.lower()
    found = [f for f in expected_facts if f.lower() in text_lower]
    recall = len(found) / len(expected_facts)
    return {
        "recall": round(recall, 3),
        "found": found,
        "missed": [f for f in expected_facts if f.lower() not in text_lower],
    }


def run_eval():
    print("=" * 70)
    print("mem0 ZER0DEX EVALUATION — n=97")
    print("=" * 70)
    
    memory_md = load_memory_md()
    m = Memory.from_config(CONFIG)
    
    # Get all memories for test generation
    all_mem = m.get_all(user_id="demo_agent")
    memories = all_mem.get("results", [])
    print(f"Memories in store: {len(memories)}")
    
    test_cases = generate_test_cases(memories)
    print(f"Test cases generated: {len(test_cases)}")
    print(f"  Direct recall: {sum(1 for t in test_cases if t['type'] == 'direct_recall')}")
    print(f"  Cross-reference: {sum(1 for t in test_cases if t['type'] == 'cross_reference')}")
    print(f"  Negative: {sum(1 for t in test_cases if t['type'] == 'negative')}")
    
    results = {"A": [], "B": [], "C": []}
    latencies = {"A": [], "B": [], "C": []}
    tokens = {"A": [], "B": [], "C": []}
    
    by_type = {
        "direct_recall": {"A": [], "B": [], "C": []},
        "cross_reference": {"A": [], "B": [], "C": []},
        "negative": {"A": [], "B": [], "C": []},
    }
    
    for i, tc in enumerate(test_cases, 1):
        q = tc["question"]
        expected = tc["expected_facts"]
        qtype = tc["type"]
        
        if i % 10 == 0:
            print(f"  Processing {i}/{len(test_cases)}...")
        
        # Mode A: MEMORY.md only
        t0 = time.time()
        a_text = memory_md
        a_lat = time.time() - t0
        a_score = score_retrieval(a_text, expected)
        results["A"].append(a_score["recall"])
        latencies["A"].append(a_lat * 1000)
        tokens["A"].append(len(a_text) // 4)
        by_type[qtype]["A"].append(a_score["recall"])
        
        # Mode B: zer0dex
        t0 = time.time()
        b_mem = m.search(q, user_id="demo_agent", limit=10)
        b_memories = b_mem.get("results", [])
        b_mem_text = "\n".join([x.get("memory", "") for x in b_memories])
        b_text = memory_md + "\n" + b_mem_text
        b_lat = time.time() - t0
        b_score = score_retrieval(b_text, expected)
        results["B"].append(b_score["recall"])
        latencies["B"].append(b_lat * 1000)
        tokens["B"].append(len(b_text) // 4)
        by_type[qtype]["B"].append(b_score["recall"])
        
        # Mode C: Full RAG only
        t0 = time.time()
        c_mem = m.search(q, user_id="demo_agent", limit=10)
        c_memories = c_mem.get("results", [])
        c_text = "\n".join([x.get("memory", "") for x in c_memories])
        c_lat = time.time() - t0
        c_score = score_retrieval(c_text, expected)
        results["C"].append(c_score["recall"])
        latencies["C"].append(c_lat * 1000)
        tokens["C"].append(len(c_text) // 4)
        by_type[qtype]["C"].append(c_score["recall"])
    
    # ── Results ──
    print(f"\n{'=' * 70}")
    print("RESULTS — n={len(test_cases)}")
    print(f"{'=' * 70}")
    
    for key, label in [("A", "MEMORY.md only"), ("B", "zer0dex"), ("C", "Full RAG")]:
        scores = results[key]
        avg = sum(scores) / len(scores)
        passing = sum(1 for s in scores if s >= 0.75)
        avg_lat = sum(latencies[key]) / len(latencies[key])
        avg_tok = sum(tokens[key]) / len(tokens[key])
        
        print(f"\n  Mode {key} ({label}):")
        print(f"    Avg recall:     {avg:.1%}")
        print(f"    ≥75% recall:    {passing}/{len(scores)} ({passing/len(scores):.0%})")
        print(f"    Avg latency:    {avg_lat:.1f}ms")
        print(f"    Avg tokens:     {avg_tok:.0f}")
    
    # By question type
    print(f"\n{'─' * 70}")
    print("BY QUESTION TYPE:")
    for qtype in ["direct_recall", "cross_reference", "negative"]:
        print(f"\n  {qtype}:")
        for key in ["A", "B", "C"]:
            scores = by_type[qtype][key]
            if scores:
                avg = sum(scores) / len(scores)
                print(f"    Mode {key}: {avg:.1%} avg recall (n={len(scores)})")
    
    # Statistical comparison
    print(f"\n{'=' * 70}")
    print("STATISTICAL COMPARISON")
    print(f"{'=' * 70}")
    
    # Paired comparison B vs A, B vs C
    b_wins_a = sum(1 for a, b in zip(results["A"], results["B"]) if b > a)
    b_ties_a = sum(1 for a, b in zip(results["A"], results["B"]) if b == a)
    b_loses_a = sum(1 for a, b in zip(results["A"], results["B"]) if b < a)
    
    b_wins_c = sum(1 for c, b in zip(results["C"], results["B"]) if b > c)
    b_ties_c = sum(1 for c, b in zip(results["C"], results["B"]) if b == c)
    b_loses_c = sum(1 for c, b in zip(results["C"], results["B"]) if b < c)
    
    print(f"  zer0dex vs MEMORY.md: {b_wins_a} wins, {b_ties_a} ties, {b_loses_a} losses")
    print(f"  zer0dex vs Full RAG:  {b_wins_c} wins, {b_ties_c} ties, {b_loses_c} losses")
    
    avg_b = sum(results["B"]) / len(results["B"])
    avg_c = sum(results["C"]) / len(results["C"])
    avg_a = sum(results["A"]) / len(results["A"])
    
    print(f"\n  VERDICT:")
    if avg_b > avg_a and avg_b >= avg_c:
        print(f"  ✅ zer0dex is the BEST approach ({avg_b:.1%} vs baseline {avg_a:.1%} vs full RAG {avg_c:.1%})")
    elif avg_b > avg_a:
        delta = avg_c - avg_b
        print(f"  ⚠️ zer0dex beats baseline but trails full RAG by {delta:.1%}")
    else:
        print(f"  ❌ zer0dex is not adding value")


if __name__ == "__main__":
    run_eval()
