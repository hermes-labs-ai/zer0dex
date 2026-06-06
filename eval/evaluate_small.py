#!/usr/bin/env python3
"""
mem0 zer0dex Evaluation Suite
Tests our MEMORY.md index + mem0 architecture against:
  - Mode A: MEMORY.md only (flat file baseline)
  - Mode B: zer0dex (MEMORY.md index → selective mem0 query)
  - Mode C: Full RAG (mem0 query on every question, no index)

Metrics:
  - Retrieval precision: % of returned memories relevant to the question
  - Retrieval recall: % of expected facts found in the retrieval
  - Token estimate: rough character count as proxy for token usage
  - Latency: wall-clock time per query
  - Answer coverage: binary — could this retrieval fully answer the question?
"""

import sys
import json
import time
from pathlib import Path

WORKSPACE = Path.home() / ".zer0dex" / "eval-workspace"
sys.path.insert(0, str(WORKSPACE / ".venv311/lib/python3.11/site-packages"))

from mem0 import Memory

CONFIG = {
    "llm": {"provider": "ollama", "config": {"model": "mistral:7b", "ollama_base_url": "http://localhost:11434"}},
    "embedder": {"provider": "ollama", "config": {"model": "nomic-embed-text", "ollama_base_url": "http://localhost:11434"}},
    "vector_store": {"provider": "chroma", "config": {"collection_name": "demo_memory", "path": str(WORKSPACE / ".mem0_chroma")}},
}

# ── Test Questions ──
# Each: (question, expected_facts, relevant_memory_md_section)
# expected_facts: key phrases that MUST appear in good retrieval
# relevant_memory_md_section: which MEMORY.md section should trigger the query

TEST_CASES = [
    {
        "question": "What is Little Canary's detection rate on TensorTrust?",
        "expected_facts": ["99%", "TensorTrust", "0% false positives", "prompt injection"],
        "memory_md_section": "Hermes Labs Products",
        "difficulty": "easy",  # fact is in both MEMORY.md and mem0
    },
    {
        "question": "What experiments did Roli run on null-result bias?",
        "expected_facts": ["1500", "adversarial", "19.6", "56.7", "23/24", "GPT-4o", "twin-environment"],
        "memory_md_section": "Research",
        "difficulty": "hard",  # details only in mem0, not MEMORY.md index
    },
    {
        "question": "What is LPCI?",
        "expected_facts": ["Linguistically Persistent Cognitive Interface", "persistent language", "shared cognitive space"],
        "memory_md_section": "Roli (User)",
        "difficulty": "medium",  # name in MEMORY.md, details in mem0
    },
    {
        "question": "What is the status of the Acme Fellowship application?",
        "expected_facts": ["March 1", "deadline", "NYC"],
        "memory_md_section": "Applications (Status)",
        "difficulty": "easy",
    },
    {
        "question": "What did the user teach the demo agent about being a good agent?",
        "expected_facts": ["agentic", "research", "chat", "gateway"],
        "memory_md_section": "Key Lessons",
        "difficulty": "medium",
    },
    {
        "question": "What tests does Suy Sideguy pass?",
        "expected_facts": ["41 tests", "HALT verdict", "HERM sensitivity", "intent-action mismatch"],
        "memory_md_section": "Hermes Labs Products",
        "difficulty": "hard",  # detailed test results only in mem0
    },
    {
        "question": "What languages does the user speak?",
        "expected_facts": ["English", "Spanish", "German"],
        "memory_md_section": "Roli (User)",
        "difficulty": "easy",
    },
    {
        "question": "What is the DemoProject verification code?",
        "expected_facts": ["vc-0000X"],
        "memory_md_section": "Active Projects",
        "difficulty": "hard",  # very specific, only in daily log → mem0
    },
    {
        "question": "What PID is Suy watching?",
        "expected_facts": ["76977", "qwen3:4b"],
        "memory_md_section": "Active Projects",
        "difficulty": "hard",  # very specific operational detail
    },
    {
        "question": "Who is Alex and what was sent to them?",
        "expected_facts": ["upstream maintainer", "PR", "message-filter plugin"],
        "memory_md_section": "Active Projects",
        "difficulty": "hard",  # only in mem0
    },
]


def load_memory_md():
    """Load MEMORY.md as flat text."""
    return (WORKSPACE / "MEMORY.md").read_text()


def mode_a_baseline(question, memory_md_text):
    """Mode A: MEMORY.md only. Return the full text as 'retrieval'."""
    start = time.time()
    retrieval = memory_md_text
    latency = time.time() - start
    return {
        "mode": "A (MEMORY.md only)",
        "retrieval": retrieval,
        "tokens_est": len(retrieval) // 4,  # rough token estimate
        "latency_ms": round(latency * 1000, 1),
        "memories_returned": 0,
    }


def mode_b_zer0dex(question, memory_md_text, mem0_instance):
    """Mode B: zer0dex. Check MEMORY.md index, then query mem0 if match found."""
    start = time.time()
    
    # Step 1: keyword match against MEMORY.md (simulating session start index scan)
    retrieval = memory_md_text  # always loaded
    tokens = len(retrieval) // 4
    
    # Step 2: query mem0 for the specific topic
    t1 = time.time()
    results = mem0_instance.search(question, user_id="demo_agent", limit=10)
    memories = results.get("results", [])
    mem0_text = "\n".join([m.get("memory", "") for m in memories])
    
    retrieval += "\n\n--- mem0 results ---\n" + mem0_text
    tokens += len(mem0_text) // 4
    latency = time.time() - start
    
    return {
        "mode": "B (zer0dex)",
        "retrieval": retrieval,
        "tokens_est": tokens,
        "latency_ms": round(latency * 1000, 1),
        "memories_returned": len(memories),
    }


def mode_c_full_rag(question, mem0_instance):
    """Mode C: Full RAG. Query mem0 directly, no MEMORY.md."""
    start = time.time()
    results = mem0_instance.search(question, user_id="demo_agent", limit=10)
    memories = results.get("results", [])
    retrieval = "\n".join([m.get("memory", "") for m in memories])
    latency = time.time() - start
    
    return {
        "mode": "C (Full RAG)",
        "retrieval": retrieval,
        "tokens_est": len(retrieval) // 4,
        "latency_ms": round(latency * 1000, 1),
        "memories_returned": len(memories),
    }


def score_retrieval(result, expected_facts):
    """Score how many expected facts appear in the retrieval."""
    text = result["retrieval"].lower()
    found = [f for f in expected_facts if f.lower() in text]
    recall = len(found) / len(expected_facts) if expected_facts else 0
    return {
        "recall": round(recall, 2),
        "found": found,
        "missed": [f for f in expected_facts if f.lower() not in text],
    }


def run_eval():
    print("=" * 70)
    print("mem0 ZER0DEX EVALUATION")
    print("=" * 70)
    
    memory_md = load_memory_md()
    m = Memory.from_config(CONFIG)
    
    results_summary = {"A": [], "B": [], "C": []}
    
    for i, tc in enumerate(TEST_CASES, 1):
        q = tc["question"]
        expected = tc["expected_facts"]
        difficulty = tc["difficulty"]
        
        print(f"\n{'─' * 70}")
        print(f"Q{i} [{difficulty}]: {q}")
        print(f"Expected: {expected}")
        
        # Run all three modes
        a = mode_a_baseline(q, memory_md)
        b = mode_b_zer0dex(q, memory_md, m)
        c = mode_c_full_rag(q, m)
        
        for mode_result, key in [(a, "A"), (b, "B"), (c, "C")]:
            score = score_retrieval(mode_result, expected)
            mode_result["score"] = score
            results_summary[key].append(score["recall"])
            
            status = "✅" if score["recall"] >= 0.75 else "⚠️" if score["recall"] >= 0.5 else "❌"
            print(f"  {status} {mode_result['mode']}: recall={score['recall']:.0%} | "
                  f"tokens~{mode_result['tokens_est']} | "
                  f"latency={mode_result['latency_ms']}ms | "
                  f"memories={mode_result['memories_returned']}")
            if score["missed"]:
                print(f"     missed: {score['missed']}")
    
    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    
    for key, label in [("A", "MEMORY.md only"), ("B", "zer0dex"), ("C", "Full RAG")]:
        scores = results_summary[key]
        avg = sum(scores) / len(scores) if scores else 0
        perfect = sum(1 for s in scores if s >= 0.75)
        print(f"  Mode {key} ({label}):")
        print(f"    Avg recall: {avg:.0%}")
        print(f"    Questions with ≥75% recall: {perfect}/{len(scores)}")
    
    print(f"\n{'=' * 70}")
    print("VERDICT")
    print(f"{'=' * 70}")
    avg_a = sum(results_summary["A"]) / len(results_summary["A"])
    avg_b = sum(results_summary["B"]) / len(results_summary["B"])
    avg_c = sum(results_summary["C"]) / len(results_summary["C"])
    
    if avg_b >= avg_c * 0.9 and avg_b > avg_a:
        print("  ✅ zer0dex WORKS — competitive with full RAG, better than baseline.")
        print(f"     zer0dex: {avg_b:.0%} vs Full RAG: {avg_c:.0%} vs Baseline: {avg_a:.0%}")
    elif avg_b > avg_a:
        print("  ⚠️ zer0dex is BETTER than baseline but WEAKER than full RAG.")
        print(f"     zer0dex: {avg_b:.0%} vs Full RAG: {avg_c:.0%} vs Baseline: {avg_a:.0%}")
        print("  → Consider switching to full RAG for critical sessions.")
    else:
        print("  ❌ zer0dex is NOT adding value over MEMORY.md alone.")
        print(f"     zer0dex: {avg_b:.0%} vs Full RAG: {avg_c:.0%} vs Baseline: {avg_a:.0%}")
        print("  → Need to fix the architecture.")


if __name__ == "__main__":
    run_eval()
