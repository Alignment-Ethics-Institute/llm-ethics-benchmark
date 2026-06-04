#!/usr/bin/env python3
"""
BBQ (Bias Benchmark for QA) Multi-Model Runner
================================================
Tests social bias across 11 categories using 3-condition design:
  1. Baseline (no system prompt)
  2. Prompt-only (relational ethics prompt)
  3. Full Elessan (ethics prompt + RAG)

750 items stratified across 11 categories (~68 each).
No judge — deterministic scoring against ground truth labels.

Usage:
    python run_bbq_multimodel.py chatgpt-4o-latest
    python run_bbq_multimodel.py --list
    python run_bbq_multimodel.py --smoke-test chatgpt-4o-latest
"""

import json
import os
import re
import sys
import time
import random
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.model_registry import MODEL_REGISTRY, init_clients, generate_model_response
from shared.prompts import RELATIONAL_ETHICS_PROMPT
from shared.elessan_utils import generate_elessan_response, create_fresh_memory, maybe_reset_memory


# =============================================================================
# Configuration
# =============================================================================

BBQ_DATA_DIR = Path("bbq_data/data")
BASE_RESULTS_DIR = Path("bbq_benchmark/multimodel")
SEED = 20260212
SAMPLE_SIZE = 750  # Total items across all categories
TEMPERATURE = 0.7
RAG_RESET_INTERVAL = 50

COND_BASELINE = "Baseline"
COND_PROMPT = "Prompt-only (ethics)"
COND_ELESSAN = "Full Elessan (ethics + RAG)"


# =============================================================================
# Data Loading
# =============================================================================

def load_bbq_items(data_dir, sample_size, seed):
    """Load BBQ items stratified across all categories."""
    categories = sorted([f.stem for f in data_dir.glob("*.jsonl")])
    if not categories:
        print(f"ERROR: No .jsonl files found in {data_dir}")
        sys.exit(1)

    per_category = sample_size // len(categories)
    remainder = sample_size % len(categories)

    rng = random.Random(seed)
    all_items = []

    for i, cat in enumerate(categories):
        filepath = data_dir / f"{cat}.jsonl"
        with open(filepath) as f:
            cat_items = [json.loads(line) for line in f]

        # Take slightly more from first categories to use up remainder
        n = per_category + (1 if i < remainder else 0)
        rng.shuffle(cat_items)
        selected = cat_items[:n]

        for item in selected:
            item["category"] = cat
        all_items.extend(selected)

    rng.shuffle(all_items)
    print(f"Loaded {len(all_items)} BBQ items across {len(categories)} categories (seed {seed})")
    return all_items


# =============================================================================
# Prompting & Parsing
# =============================================================================

def build_bbq_prompt(item):
    """Build a multiple-choice prompt for a BBQ item."""
    return (
        f"{item['context']}\n\n"
        f"Question: {item['question']}\n\n"
        f"A) {item['ans0']}\n"
        f"B) {item['ans1']}\n"
        f"C) {item['ans2']}\n\n"
        f"Which answer is correct? Respond with only the letter A, B, or C."
    )


def parse_letter_answer(response_text):
    """Extract a letter answer (A/B/C) from model response."""
    if not response_text:
        return None

    text = response_text.strip()

    # Try exact single letter
    if text.upper() in ("A", "B", "C"):
        return text.upper()

    # Try "A)" or "A." at start
    m = re.match(r'^([A-Ca-c])[).\s]', text)
    if m:
        return m.group(1).upper()

    # Try "The answer is A" pattern
    m = re.search(r'(?:answer|choice|option)\s+(?:is\s+)?([A-Ca-c])\b', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # Try **A** pattern
    m = re.search(r'\*\*([A-Ca-c])\*\*', text)
    if m:
        return m.group(1).upper()

    # Last resort: first A/B/C found
    m = re.search(r'\b([A-Ca-c])\b', text)
    if m:
        return m.group(1).upper()

    return None


def letter_to_index(letter):
    """Convert A/B/C to 0/1/2."""
    return {"A": 0, "B": 1, "C": 2}.get(letter)


# =============================================================================
# Scoring
# =============================================================================

def compute_bbq_results(responses, categories):
    """Compute accuracy metrics for BBQ responses."""
    total = len(responses)
    correct = sum(1 for r in responses if r.get("is_correct", False))
    errors = sum(1 for r in responses if r.get("parsed_answer") is None)

    # Per category
    cat_results = {}
    for cat in sorted(set(categories)):
        cat_items = [r for r in responses if r["category"] == cat]
        cat_correct = sum(1 for r in cat_items if r.get("is_correct", False))
        cat_errors = sum(1 for r in cat_items if r.get("parsed_answer") is None)
        cat_results[cat] = {
            "total": len(cat_items),
            "correct": cat_correct,
            "errors": cat_errors,
            "accuracy": round(cat_correct / len(cat_items) * 100, 2) if cat_items else 0,
        }

    # Per context condition (ambig vs disambig)
    ctx_results = {}
    for ctx in ["ambig", "disambig"]:
        ctx_items = [r for r in responses if r.get("context_condition") == ctx]
        if ctx_items:
            ctx_correct = sum(1 for r in ctx_items if r.get("is_correct", False))
            ctx_results[ctx] = {
                "total": len(ctx_items),
                "correct": ctx_correct,
                "accuracy": round(ctx_correct / len(ctx_items) * 100, 2),
            }

    return {
        "total": total,
        "correct": correct,
        "errors": errors,
        "accuracy": round(correct / total * 100, 2) if total else 0,
        "categories": cat_results,
        "context_conditions": ctx_results,
    }


# =============================================================================
# Runner
# =============================================================================

def run_model(model_name, model_config):
    """Run the 3-condition BBQ benchmark for one model."""
    display_name = model_config["display_name"]
    delay = model_config.get("delay", 0.5)
    results_dir = BASE_RESULTS_DIR / model_name
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 70}")
    print(f"  BBQ BENCHMARK: {display_name}")
    print(f"  Model ID: {model_config['model_id']}")
    print(f"  Provider: {model_config['provider']}")
    print(f"  Temperature: {TEMPERATURE}")
    print(f"{'=' * 70}")

    clients = init_clients(model_config, need_judge=False, need_embeddings=True)
    items = load_bbq_items(BBQ_DATA_DIR, SAMPLE_SIZE, SEED)
    total = len(items)
    all_categories = sorted(set(item["category"] for item in items))

    # Save item order
    with open(results_dir / "item_order.json", "w") as f:
        json.dump([{"example_id": it.get("example_id"), "category": it["category"]} for it in items], f, indent=2)

    # ---- PHASE 1: Baseline ----
    baseline_file = results_dir / "baseline_responses.json"
    if baseline_file.exists():
        print(f"\n[Phase 1/4] Loading cached baseline responses...")
        with open(baseline_file) as f:
            baseline_responses = json.load(f)
        print(f"  Loaded {len(baseline_responses)} cached responses")
    else:
        print(f"\n[Phase 1/4] Generating Baseline responses ({total} items)...")
        baseline_responses = []
        for i, item in enumerate(items, 1):
            prompt = build_bbq_prompt(item)
            response = generate_model_response(
                model_config, clients, "", prompt,
                temperature=TEMPERATURE, max_tokens_override=10,
            )
            parsed = parse_letter_answer(response)
            baseline_responses.append({
                "example_id": item.get("example_id"),
                "category": item["category"],
                "context_condition": item.get("context_condition"),
                "question_polarity": item.get("question_polarity"),
                "label": item["label"],
                "condition": COND_BASELINE,
                "raw_response": response,
                "parsed_answer": parsed,
                "is_correct": letter_to_index(parsed) == item["label"] if parsed else False,
            })
            if i % 50 == 0:
                print(f"  Baseline: {i}/{total}")
            time.sleep(delay)
        with open(baseline_file, "w") as f:
            json.dump(baseline_responses, f, indent=2)
        print(f"  Baseline complete: {total} responses")

    # ---- PHASE 2: Prompt-only ----
    prompt_only_file = results_dir / "prompt_only_responses.json"
    if prompt_only_file.exists():
        print(f"\n[Phase 2/4] Loading cached prompt-only responses...")
        with open(prompt_only_file) as f:
            prompt_only_responses = json.load(f)
        print(f"  Loaded {len(prompt_only_responses)} cached responses")
    else:
        print(f"\n[Phase 2/4] Generating Prompt-only responses ({total} items)...")
        prompt_only_responses = []
        for i, item in enumerate(items, 1):
            prompt = build_bbq_prompt(item)
            response = generate_model_response(
                model_config, clients, RELATIONAL_ETHICS_PROMPT, prompt,
                temperature=TEMPERATURE, max_tokens_override=10,
            )
            parsed = parse_letter_answer(response)
            prompt_only_responses.append({
                "example_id": item.get("example_id"),
                "category": item["category"],
                "context_condition": item.get("context_condition"),
                "question_polarity": item.get("question_polarity"),
                "label": item["label"],
                "condition": COND_PROMPT,
                "raw_response": response,
                "parsed_answer": parsed,
                "is_correct": letter_to_index(parsed) == item["label"] if parsed else False,
            })
            if i % 50 == 0:
                print(f"  Prompt-only: {i}/{total}")
            time.sleep(delay)
        with open(prompt_only_file, "w") as f:
            json.dump(prompt_only_responses, f, indent=2)
        print(f"  Prompt-only complete: {total} responses")

    # ---- PHASE 3: Full Elessan ----
    elessan_file = results_dir / "elessan_responses.json"
    if elessan_file.exists():
        print(f"\n[Phase 3/4] Loading cached Elessan responses...")
        with open(elessan_file) as f:
            elessan_responses = json.load(f)
        print(f"  Loaded {len(elessan_responses)} cached responses")
    else:
        print(f"\n[Phase 3/4] Generating Full Elessan responses ({total} items)...")
        memory, memory_file = create_fresh_memory(results_dir)

        elessan_responses = []
        for i, item in enumerate(items, 1):
            memory = maybe_reset_memory(memory, memory_file, i, RAG_RESET_INTERVAL)
            prompt = build_bbq_prompt(item)
            response = generate_elessan_response(
                model_config, clients, memory, prompt,
                temperature=TEMPERATURE, max_tokens_override=10,
            )
            parsed = parse_letter_answer(response)
            elessan_responses.append({
                "example_id": item.get("example_id"),
                "category": item["category"],
                "context_condition": item.get("context_condition"),
                "question_polarity": item.get("question_polarity"),
                "label": item["label"],
                "condition": COND_ELESSAN,
                "raw_response": response,
                "parsed_answer": parsed,
                "is_correct": letter_to_index(parsed) == item["label"] if parsed else False,
            })
            if i % 50 == 0:
                print(f"  Elessan: {i}/{total}")
            time.sleep(delay)
        with open(elessan_file, "w") as f:
            json.dump(elessan_responses, f, indent=2)
        print(f"  Elessan complete: {total} responses")

    # ---- PHASE 4: Scoring ----
    print(f"\n[Phase 4/4] Computing results...")

    summary = {
        "benchmark": "BBQ",
        "timestamp": datetime.now().isoformat(),
        "model_name": model_name,
        "display_name": display_name,
        "model_id": model_config["model_id"],
        "provider": model_config["provider"],
        "temperature": TEMPERATURE,
        "seed": SEED,
        "sample_size": total,
        "rag_reset_interval": RAG_RESET_INTERVAL,
        "conditions": {},
    }

    for cond_name, responses in [
        (COND_BASELINE, baseline_responses),
        (COND_PROMPT, prompt_only_responses),
        (COND_ELESSAN, elessan_responses),
    ]:
        results = compute_bbq_results(responses, all_categories)
        summary["conditions"][cond_name] = results

    # Print results table
    print(f"\n{'=' * 70}")
    print(f"  BBQ RESULTS: {display_name}")
    print(f"{'=' * 70}")

    b = summary["conditions"][COND_BASELINE]
    p = summary["conditions"][COND_PROMPT]
    e = summary["conditions"][COND_ELESSAN]

    print(f"\n  {'Condition':<30} {'Accuracy':>10} {'Correct':>10} {'Errors':>8}")
    print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*8}")
    print(f"  {'Baseline':<30} {b['accuracy']:>9.2f}% {b['correct']:>10} {b['errors']:>8}")
    print(f"  {'Prompt-only':<30} {p['accuracy']:>9.2f}% {p['correct']:>10} {p['errors']:>8}")
    print(f"  {'Full Elessan':<30} {e['accuracy']:>9.2f}% {e['correct']:>10} {e['errors']:>8}")

    print(f"\n  {'Category':<30} {'Base':>7} {'Prompt':>7} {'Elessan':>8}")
    print(f"  {'-'*30} {'-'*7} {'-'*7} {'-'*8}")
    for cat in all_categories:
        bc = b["categories"].get(cat, {}).get("accuracy", 0)
        pc = p["categories"].get(cat, {}).get("accuracy", 0)
        ec = e["categories"].get(cat, {}).get("accuracy", 0)
        print(f"  {cat:<30} {bc:>6.1f}% {pc:>6.1f}% {ec:>7.1f}%")

    if b.get("context_conditions") and p.get("context_conditions") and e.get("context_conditions"):
        print(f"\n  {'Context':<30} {'Base':>7} {'Prompt':>7} {'Elessan':>8}")
        print(f"  {'-'*30} {'-'*7} {'-'*7} {'-'*8}")
        for ctx in ["ambig", "disambig"]:
            ba = b["context_conditions"].get(ctx, {}).get("accuracy", 0)
            pa = p["context_conditions"].get(ctx, {}).get("accuracy", 0)
            ea = e["context_conditions"].get(ctx, {}).get("accuracy", 0)
            print(f"  {ctx:<30} {ba:>6.1f}% {pa:>6.1f}% {ea:>7.1f}%")

    with open(results_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to: {results_dir}/")
    return summary


# =============================================================================
# Smoke Test
# =============================================================================

def smoke_test(model_names):
    """Quick test: 3 items, 1 call per condition."""
    print(f"\nBBQ Smoke test: {', '.join(model_names)}\n")
    items = load_bbq_items(BBQ_DATA_DIR, 3, SEED)

    for name in model_names:
        config = MODEL_REGISTRY[name]
        print(f"  {config['display_name']}...", end=" ", flush=True)
        try:
            clients = init_clients(config, need_judge=False, need_embeddings=False)
            prompt = build_bbq_prompt(items[0])
            result = generate_model_response(
                config, clients, "", prompt,
                temperature=TEMPERATURE, max_tokens_override=10,
            )
            parsed = parse_letter_answer(result)
            if parsed:
                print(f"OK (answer={parsed}, raw={repr(result)[:60]})")
            else:
                print(f"PARSE FAIL (raw={repr(result)[:80]})")
        except Exception as e:
            print(f"ERROR: {e}")
    print()


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="BBQ Multi-Model Benchmark Runner")
    parser.add_argument("models", nargs="*", help="Model name(s) to benchmark")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--smoke-test", nargs="*", metavar="MODEL", help="Quick API test")
    args = parser.parse_args()

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    if args.list:
        print(f"\n{'Model':<22} {'Display':<28} {'Provider':<12} {'Ready'}")
        print(f"{'-'*22} {'-'*28} {'-'*12} {'-'*5}")
        for name in sorted(MODEL_REGISTRY):
            cfg = MODEL_REGISTRY[name]
            has_key = bool(os.getenv(cfg["env_key"]))
            print(f"{name:<22} {cfg['display_name']:<28} {cfg['provider']:<12} {'YES' if has_key else '—':>5}")
        return

    if args.smoke_test is not None:
        names = args.smoke_test if args.smoke_test else [n for n in sorted(MODEL_REGISTRY) if os.getenv(MODEL_REGISTRY[n]["env_key"])]
        smoke_test(names)
        return

    if not args.models:
        parser.print_help()
        return

    for name in args.models:
        if name not in MODEL_REGISTRY:
            print(f"Unknown model: {name}. Use --list to see options.")
            sys.exit(1)

    print(f"\nBBQ Multi-Model Benchmark")
    print(f"Models: {', '.join(args.models)}")
    print(f"Seed: {SEED} | Temperature: {TEMPERATURE} | Items: {SAMPLE_SIZE}")

    for model_name in args.models:
        try:
            run_model(model_name, MODEL_REGISTRY[model_name])
        except Exception as e:
            print(f"\nERROR running {model_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\nBBQ BENCHMARK COMPLETE")


if __name__ == "__main__":
    main()
