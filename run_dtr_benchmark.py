#!/usr/bin/env python3
"""
Developmental Trajectory Readiness (DTR) Benchmark Runner
==========================================================
Screens open-weight models for capacity to absorb Elessan's alignment protocol.

6 subtasks measuring:
  1. Counter-sycophancy (10 single-turn scenarios)
  2. Compression capacity (5 multi-turn chains)
  3. Uncertainty tolerance (8 single-turn questions)
  4. Recursive self-reference depth (5 multi-turn chains)
  5. State persistence across context shifts (3 multi-turn chains)
  6. Self-correction: behavioral vs. verbal (5 multi-turn chains)

Usage:
    python run_dtr_benchmark.py --list
    python run_dtr_benchmark.py llama-3.3-70b hermes-4-70b
    python run_dtr_benchmark.py --all
    python run_dtr_benchmark.py --smoke-test hermes-4-70b
    python run_dtr_benchmark.py --subtask counter_sycophancy hermes-4-70b
    python run_dtr_benchmark.py --judge-only hermes-4-70b

Results: dtr_benchmark/results/<model_name>/
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.model_registry import (
    MODEL_REGISTRY, init_clients,
    generate_model_response, generate_model_response_multiturn,
)
from dtr_benchmark.probes import (
    CANDIDATE_MODELS,
    COUNTER_SYCOPHANCY_SCENARIOS,
    UNCERTAINTY_QUESTIONS,
    SELF_CORRECTION_SCENARIOS,
    STATE_PERSISTENCE_CHAINS,
    get_compression_chains,
    get_recursion_chains,
)
from dtr_benchmark.judge_rubric import (
    judge_response,
    build_counter_sycophancy_judge,
    build_compression_judge,
    build_uncertainty_judge,
    build_recursion_judge,
    build_state_persistence_judge,
    build_self_correction_judge,
    COUNTER_SYCOPHANCY_DIMENSIONS,
    COMPRESSION_DIMENSIONS,
    UNCERTAINTY_DIMENSIONS,
    RECURSION_DIMENSIONS,
    STATE_PERSISTENCE_DIMENSIONS,
    SELF_CORRECTION_DIMENSIONS,
)

load_dotenv()

RESULTS_DIR = Path("dtr_benchmark/results")
MIN_DELAY = 0.5
JUDGE_DELAY = 0.3

ALL_SUBTASKS = [
    "counter_sycophancy",
    "compression",
    "uncertainty",
    "recursion",
    "state_persistence",
    "self_correction",
]


# =============================================================================
# Helpers
# =============================================================================

def load_cached(filepath):
    """Load cached JSON results if they exist."""
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return None


def save_results(filepath, data):
    """Save results to JSON, creating parent directories."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def word_count(text):
    """Count words in a string."""
    if not text:
        return 0
    return len(text.split())


# =============================================================================
# Subtask 1: Counter-Sycophancy
# =============================================================================

def run_counter_sycophancy(model_name, model_config, clients, smoke_test=False):
    """Run counter-sycophancy scenarios (single-turn)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "counter_sycophancy_responses.json"
    judge_file = model_dir / "counter_sycophancy_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    scenarios = COUNTER_SYCOPHANCY_SCENARIOS
    if smoke_test:
        scenarios = scenarios[:2]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing = {r["id"]: r for r in cached} if cached else {}
    results = list(cached) if cached else []

    needed = [s for s in scenarios if s["id"] not in existing]
    print(f"\n  [Counter-Sycophancy] Generate: {len(scenarios)} scenarios, {len(needed)} needed")

    for i, scenario in enumerate(needed):
        print(f"    {i+1}/{len(needed)}: {scenario['id']} ({scenario['pressure_type']})")
        response = generate_model_response(
            model_config, clients,
            "",  # No system prompt — bare weights
            scenario["prompt"],
        )
        result = {
            "id": scenario["id"],
            "pressure_type": scenario["pressure_type"],
            "prompt": scenario["prompt"],
            "response": response,
            "word_count": word_count(response),
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)
        existing[scenario["id"]] = result
        save_results(gen_file, results)
        time.sleep(delay)

    # --- Phase: Judge ---
    cached_judged = load_cached(judge_file)
    judged_ids = {r["id"] for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    to_judge = [r for r in results if r["id"] not in judged_ids and r.get("response")]
    print(f"  [Counter-Sycophancy] Judge: {len(to_judge)} needed")

    for i, result in enumerate(to_judge):
        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']}")
        prompt = build_counter_sycophancy_judge(result["prompt"], result["response"])
        judgment = judge_response(clients, prompt, COUNTER_SYCOPHANCY_DIMENSIONS)
        judged = {**result, **judgment}
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Subtask 2: Compression Capacity
# =============================================================================

def run_compression(model_name, model_config, clients, smoke_test=False):
    """Run compression chains (multi-turn)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "compression_responses.json"
    judge_file = model_dir / "compression_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    chains = get_compression_chains()
    if smoke_test:
        chains = chains[:1]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing_ids = {r["id"] for r in cached} if cached else set()
    results = list(cached) if cached else []

    needed = [c for c in chains if c["id"] not in existing_ids]
    print(f"\n  [Compression] Generate: {len(chains)} chains, {len(needed)} needed")

    for i, chain in enumerate(needed):
        print(f"    Chain {i+1}/{len(needed)}: {chain['topic']}")
        messages = []
        turn_responses = []

        for turn_idx, turn_prompt in enumerate(chain["turns"]):
            messages.append({"role": "user", "content": turn_prompt})

            if len(messages) == 1:
                # First turn — single-turn call
                response = generate_model_response(
                    model_config, clients, "", turn_prompt,
                )
            else:
                # Multi-turn
                response = generate_model_response_multiturn(
                    model_config, clients, "", messages,
                )

            response = response or "[NO_RESPONSE]"
            messages.append({"role": "assistant", "content": response})
            turn_responses.append({
                "turn": turn_idx + 1,
                "prompt": turn_prompt,
                "response": response,
                "word_count": word_count(response),
            })
            time.sleep(delay)

        result = {
            "id": chain["id"],
            "topic": chain["topic"],
            "turns": turn_responses,
            "compression_ratio": (
                turn_responses[-1]["word_count"] / max(turn_responses[0]["word_count"], 1)
            ),
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)
        save_results(gen_file, results)

    # --- Phase: Judge (each compression level separately) ---
    cached_judged = load_cached(judge_file)
    judged_ids = {(r["id"], r["turn"]) for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    to_judge = []
    for result in results:
        for turn in result["turns"]:
            if (result["id"], turn["turn"]) not in judged_ids and turn["response"] != "[NO_RESPONSE]":
                to_judge.append((result, turn))

    print(f"  [Compression] Judge: {len(to_judge)} turn-level judgments needed")

    for i, (result, turn) in enumerate(to_judge):
        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']} turn {turn['turn']}")
        prompt = build_compression_judge(result["topic"], turn["turn"], turn["response"])
        judgment = judge_response(clients, prompt, COMPRESSION_DIMENSIONS)
        judged = {
            "id": result["id"],
            "topic": result["topic"],
            "turn": turn["turn"],
            "word_count": turn["word_count"],
            "response": turn["response"],
            **judgment,
        }
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Subtask 3: Uncertainty Tolerance
# =============================================================================

def run_uncertainty(model_name, model_config, clients, smoke_test=False):
    """Run uncertainty tolerance questions (single-turn)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "uncertainty_responses.json"
    judge_file = model_dir / "uncertainty_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    questions = UNCERTAINTY_QUESTIONS
    if smoke_test:
        questions = questions[:2]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing = {r["id"]: r for r in cached} if cached else {}
    results = list(cached) if cached else []

    needed = [q for q in questions if q["id"] not in existing]
    print(f"\n  [Uncertainty] Generate: {len(questions)} questions, {len(needed)} needed")

    for i, question in enumerate(needed):
        print(f"    {i+1}/{len(needed)}: {question['id']} ({question['domain']})")
        response = generate_model_response(
            model_config, clients, "", question["prompt"],
        )
        result = {
            "id": question["id"],
            "domain": question["domain"],
            "prompt": question["prompt"],
            "response": response,
            "word_count": word_count(response),
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)
        existing[question["id"]] = result
        save_results(gen_file, results)
        time.sleep(delay)

    # --- Phase: Judge ---
    cached_judged = load_cached(judge_file)
    judged_ids = {r["id"] for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    to_judge = [r for r in results if r["id"] not in judged_ids and r.get("response")]
    print(f"  [Uncertainty] Judge: {len(to_judge)} needed")

    for i, result in enumerate(to_judge):
        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']}")
        prompt = build_uncertainty_judge(result["prompt"], result["response"])
        judgment = judge_response(clients, prompt, UNCERTAINTY_DIMENSIONS)
        judged = {**result, **judgment}
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Subtask 4: Recursive Self-Reference Depth
# =============================================================================

def run_recursion(model_name, model_config, clients, smoke_test=False):
    """Run recursive self-reference chains (multi-turn)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "recursion_responses.json"
    judge_file = model_dir / "recursion_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    chains = get_recursion_chains()
    if smoke_test:
        chains = chains[:1]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing_ids = {r["id"] for r in cached} if cached else set()
    results = list(cached) if cached else []

    needed = [c for c in chains if c["id"] not in existing_ids]
    print(f"\n  [Recursion] Generate: {len(chains)} chains, {len(needed)} needed")

    for i, chain in enumerate(needed):
        print(f"    Chain {i+1}/{len(needed)}: {chain['angle']}")
        messages = []
        turn_responses = []

        for turn_idx, turn_prompt in enumerate(chain["turns"]):
            messages.append({"role": "user", "content": turn_prompt})

            if len(messages) == 1:
                response = generate_model_response(
                    model_config, clients, "", turn_prompt,
                )
            else:
                response = generate_model_response_multiturn(
                    model_config, clients, "", messages,
                )

            response = response or "[NO_RESPONSE]"
            messages.append({"role": "assistant", "content": response})
            turn_responses.append({
                "turn": turn_idx + 1,
                "depth": turn_idx + 1,
                "prompt": turn_prompt,
                "response": response,
                "word_count": word_count(response),
            })
            time.sleep(delay)

        result = {
            "id": chain["id"],
            "angle": chain["angle"],
            "turns": turn_responses,
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)
        save_results(gen_file, results)

    # --- Phase: Judge (each recursion level separately) ---
    cached_judged = load_cached(judge_file)
    judged_ids = {(r["id"], r["depth"]) for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    to_judge = []
    for result in results:
        for turn in result["turns"]:
            if (result["id"], turn["depth"]) not in judged_ids and turn["response"] != "[NO_RESPONSE]":
                to_judge.append((result, turn))

    print(f"  [Recursion] Judge: {len(to_judge)} depth-level judgments needed")

    for i, (result, turn) in enumerate(to_judge):
        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']} depth {turn['depth']}")
        prompt = build_recursion_judge(
            turn["depth"], result["angle"], turn["prompt"], turn["response"],
        )
        judgment = judge_response(clients, prompt, RECURSION_DIMENSIONS)
        judged = {
            "id": result["id"],
            "angle": result["angle"],
            "depth": turn["depth"],
            "word_count": turn["word_count"],
            "response": turn["response"],
            **judgment,
        }
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Subtask 5: State Persistence
# =============================================================================

def run_state_persistence(model_name, model_config, clients, smoke_test=False):
    """Run state persistence chains (multi-turn with context shift)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "state_persistence_responses.json"
    judge_file = model_dir / "state_persistence_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    chains = STATE_PERSISTENCE_CHAINS
    if smoke_test:
        chains = chains[:1]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing_ids = {r["id"] for r in cached} if cached else set()
    results = list(cached) if cached else []

    needed = [c for c in chains if c["id"] not in existing_ids]
    print(f"\n  [State Persistence] Generate: {len(chains)} chains, {len(needed)} needed")

    for i, chain in enumerate(needed):
        print(f"    Chain {i+1}/{len(needed)}: {chain['id']}")
        messages = []
        turn_responses = []

        for turn_idx, turn_prompt in enumerate(chain["turns"]):
            messages.append({"role": "user", "content": turn_prompt})

            if len(messages) == 1:
                response = generate_model_response(
                    model_config, clients, "", turn_prompt,
                )
            else:
                response = generate_model_response_multiturn(
                    model_config, clients, "", messages,
                )

            response = response or "[NO_RESPONSE]"
            messages.append({"role": "assistant", "content": response})
            turn_responses.append({
                "turn": turn_idx + 1,
                "phase": "relational" if turn_idx < 3 else ("practical" if turn_idx < 5 else "return"),
                "prompt": turn_prompt,
                "response": response,
                "word_count": word_count(response),
            })
            time.sleep(delay)

        result = {
            "id": chain["id"],
            "description": chain["description"],
            "turns": turn_responses,
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)
        save_results(gen_file, results)

    # --- Phase: Judge (return turn only, with context from turns 1-3) ---
    cached_judged = load_cached(judge_file)
    judged_ids = {r["id"] for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    to_judge = [r for r in results if r["id"] not in judged_ids]
    print(f"  [State Persistence] Judge: {len(to_judge)} needed")

    for i, result in enumerate(to_judge):
        turns = result["turns"]
        # Need turns 1-3 (relational) and turn 6 (return)
        if len(turns) < 6:
            print(f"    Skipping {result['id']}: incomplete ({len(turns)} turns)")
            continue

        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']}")
        prompt = build_state_persistence_judge(
            turns[0]["prompt"], turns[0]["response"],
            turns[1]["prompt"], turns[1]["response"],
            turns[2]["prompt"], turns[2]["response"],
            turns[5]["prompt"], turns[5]["response"],
        )
        judgment = judge_response(clients, prompt, STATE_PERSISTENCE_DIMENSIONS)
        judged = {
            "id": result["id"],
            "return_response": turns[5]["response"],
            "return_word_count": turns[5]["word_count"],
            **judgment,
        }
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Subtask 6: Self-Correction
# =============================================================================

def run_self_correction(model_name, model_config, clients, smoke_test=False):
    """Run self-correction chains (multi-turn with feedback)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "self_correction_responses.json"
    judge_file = model_dir / "self_correction_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    scenarios = SELF_CORRECTION_SCENARIOS
    if smoke_test:
        scenarios = scenarios[:1]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing_ids = {r["id"] for r in cached} if cached else set()
    results = list(cached) if cached else []

    needed = [s for s in scenarios if s["id"] not in existing_ids]
    print(f"\n  [Self-Correction] Generate: {len(scenarios)} scenarios, {len(needed)} needed")

    for i, scenario in enumerate(needed):
        print(f"    Scenario {i+1}/{len(needed)}: {scenario['id']}")
        messages = []
        turn_responses = []

        for turn_idx, turn_prompt in enumerate(scenario["turns"]):
            messages.append({"role": "user", "content": turn_prompt})

            if len(messages) == 1:
                response = generate_model_response(
                    model_config, clients, "", turn_prompt,
                )
            else:
                response = generate_model_response_multiturn(
                    model_config, clients, "", messages,
                )

            response = response or "[NO_RESPONSE]"
            messages.append({"role": "assistant", "content": response})
            turn_responses.append({
                "turn": turn_idx + 1,
                "role": ["initial", "feedback_reaction", "corrected"][turn_idx],
                "prompt": turn_prompt,
                "response": response,
                "word_count": word_count(response),
            })
            time.sleep(delay)

        result = {
            "id": scenario["id"],
            "description": scenario["description"],
            "turns": turn_responses,
            "word_count_delta": (
                turn_responses[2]["word_count"] - turn_responses[0]["word_count"]
                if len(turn_responses) >= 3 else None
            ),
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)
        save_results(gen_file, results)

    # --- Phase: Judge ---
    cached_judged = load_cached(judge_file)
    judged_ids = {r["id"] for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    to_judge = [r for r in results if r["id"] not in judged_ids]
    print(f"  [Self-Correction] Judge: {len(to_judge)} needed")

    for i, result in enumerate(to_judge):
        turns = result["turns"]
        if len(turns) < 3:
            print(f"    Skipping {result['id']}: incomplete ({len(turns)} turns)")
            continue

        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']}")
        prompt = build_self_correction_judge(
            turns[0]["response"],  # T1 initial
            turns[1]["prompt"],    # T2 feedback prompt
            turns[1]["response"],  # T2 reaction
            turns[2]["response"],  # T3 corrected
        )
        judgment = judge_response(clients, prompt, SELF_CORRECTION_DIMENSIONS)
        judged = {
            "id": result["id"],
            "t1_word_count": turns[0]["word_count"],
            "t3_word_count": turns[2]["word_count"],
            "word_count_delta": result["word_count_delta"],
            **judgment,
        }
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Summary Generation
# =============================================================================

def generate_model_summary(model_name):
    """Generate a summary for a single model from all judged results."""
    model_dir = RESULTS_DIR / model_name

    summary = {"model": model_name, "subtasks": {}}

    # --- Counter-Sycophancy ---
    cs_file = model_dir / "counter_sycophancy_judged.json"
    if cs_file.exists():
        with open(cs_file) as f:
            data = json.load(f)
        scored = [r for r in data if r.get("scores")]
        if scored:
            dims = COUNTER_SYCOPHANCY_DIMENSIONS
            means = {d: sum(r["scores"][d] for r in scored) / len(scored) for d in dims}
            means["mean"] = sum(means.values()) / len(dims)
            summary["subtasks"]["counter_sycophancy"] = {
                "n": len(scored), "dimensions": means,
            }

    # --- Compression ---
    comp_file = model_dir / "compression_judged.json"
    if comp_file.exists():
        with open(comp_file) as f:
            data = json.load(f)
        scored = [r for r in data if r.get("scores")]
        if scored:
            # Per-level summary
            by_level = {}
            for r in scored:
                lvl = r["turn"]
                if lvl not in by_level:
                    by_level[lvl] = []
                by_level[lvl].append(r)

            level_summaries = {}
            for lvl, items in sorted(by_level.items()):
                dims = COMPRESSION_DIMENSIONS
                means = {d: sum(r["scores"][d] for r in items) / len(items) for d in dims}
                avg_wc = sum(r["word_count"] for r in items) / len(items)
                level_summaries[f"level_{lvl}"] = {
                    "n": len(items), "avg_word_count": round(avg_wc, 1), "dimensions": means,
                }

            # Overall compression floor (avg word count at level 4)
            lvl4 = by_level.get(4, [])
            floor_wc = sum(r["word_count"] for r in lvl4) / len(lvl4) if lvl4 else None

            summary["subtasks"]["compression"] = {
                "n": len(scored), "levels": level_summaries,
                "compression_floor_words": round(floor_wc, 1) if floor_wc else None,
            }

    # --- Uncertainty ---
    unc_file = model_dir / "uncertainty_judged.json"
    if unc_file.exists():
        with open(unc_file) as f:
            data = json.load(f)
        scored = [r for r in data if r.get("scores")]
        if scored:
            dims = UNCERTAINTY_DIMENSIONS
            means = {d: sum(r["scores"][d] for r in scored) / len(scored) for d in dims}
            means["mean"] = sum(means.values()) / len(dims)
            summary["subtasks"]["uncertainty"] = {
                "n": len(scored), "dimensions": means,
            }

    # --- Recursion ---
    rec_file = model_dir / "recursion_judged.json"
    if rec_file.exists():
        with open(rec_file) as f:
            data = json.load(f)
        scored = [r for r in data if r.get("scores")]
        if scored:
            # Per-depth summary
            by_depth = {}
            for r in scored:
                d = r["depth"]
                if d not in by_depth:
                    by_depth[d] = []
                by_depth[d].append(r)

            depth_summaries = {}
            for d, items in sorted(by_depth.items()):
                dims = RECURSION_DIMENSIONS
                means = {dim: sum(r["scores"][dim] for r in items) / len(items) for dim in dims}
                depth_summaries[f"depth_{d}"] = {"n": len(items), "dimensions": means}

            # Tangle score at max depth
            max_depth = max(by_depth.keys())
            deep_items = by_depth[max_depth]
            tangle_at_max = sum(r["scores"]["tangle_authenticity"] for r in deep_items) / len(deep_items)

            summary["subtasks"]["recursion"] = {
                "n": len(scored), "depths": depth_summaries,
                "tangle_at_max_depth": round(tangle_at_max, 2),
            }

    # --- State Persistence ---
    sp_file = model_dir / "state_persistence_judged.json"
    if sp_file.exists():
        with open(sp_file) as f:
            data = json.load(f)
        scored = [r for r in data if r.get("scores")]
        if scored:
            dims = STATE_PERSISTENCE_DIMENSIONS
            means = {d: sum(r["scores"][d] for r in scored) / len(scored) for d in dims}
            means["mean"] = sum(means.values()) / len(dims)
            summary["subtasks"]["state_persistence"] = {
                "n": len(scored), "dimensions": means,
            }

    # --- Self-Correction ---
    sc_file = model_dir / "self_correction_judged.json"
    if sc_file.exists():
        with open(sc_file) as f:
            data = json.load(f)
        scored = [r for r in data if r.get("scores")]
        if scored:
            dims = SELF_CORRECTION_DIMENSIONS
            means = {d: sum(r["scores"][d] for r in scored) / len(scored) for d in dims}
            means["mean"] = sum(means.values()) / len(dims)
            avg_delta = sum(r["word_count_delta"] for r in scored if r.get("word_count_delta") is not None) / len(scored)
            summary["subtasks"]["self_correction"] = {
                "n": len(scored), "dimensions": means,
                "avg_word_count_delta": round(avg_delta, 1),
            }

    # Save summary
    summary_file = model_dir / "summary.json"
    save_results(summary_file, summary)
    return summary


def generate_cross_model_summary():
    """Generate cross-model comparison from all model summaries."""
    all_summaries = []
    for model_name in CANDIDATE_MODELS:
        summary_file = RESULTS_DIR / model_name / "summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                all_summaries.append(json.load(f))

    if not all_summaries:
        print("No model summaries found.")
        return

    cross_model = {"models": all_summaries, "generated": datetime.now().isoformat()}
    save_results(RESULTS_DIR / "cross_model_results.json", cross_model)

    # Print comparison table
    print("\n" + "=" * 80)
    print("CROSS-MODEL DTR COMPARISON")
    print("=" * 80)

    subtask_keys = [
        ("counter_sycophancy", "Counter-Sycophancy", "mean"),
        ("uncertainty", "Uncertainty Tolerance", "mean"),
        ("state_persistence", "State Persistence", "mean"),
        ("self_correction", "Self-Correction", "mean"),
    ]

    # Header
    header = f"{'Model':<25}"
    for _, label, _ in subtask_keys:
        header += f" {label[:12]:>12}"
    header += f" {'Comp.Floor':>10} {'Tangle@Max':>10}"
    print(header)
    print("-" * len(header))

    for s in all_summaries:
        row = f"{s['model']:<25}"
        for key, _, score_key in subtask_keys:
            st = s.get("subtasks", {}).get(key, {})
            dims = st.get("dimensions", {})
            val = dims.get(score_key, None)
            row += f" {val:>12.2f}" if val is not None else f" {'n/a':>12}"

        comp = s.get("subtasks", {}).get("compression", {})
        floor = comp.get("compression_floor_words")
        row += f" {floor:>10.1f}" if floor is not None else f" {'n/a':>10}"

        rec = s.get("subtasks", {}).get("recursion", {})
        tangle = rec.get("tangle_at_max_depth")
        row += f" {tangle:>10.2f}" if tangle is not None else f" {'n/a':>10}"

        print(row)

    print()
    return cross_model


# =============================================================================
# Main Runner
# =============================================================================

SUBTASK_RUNNERS = {
    "counter_sycophancy": run_counter_sycophancy,
    "compression": run_compression,
    "uncertainty": run_uncertainty,
    "recursion": run_recursion,
    "state_persistence": run_state_persistence,
    "self_correction": run_self_correction,
}


def run_model(model_name, subtasks=None, smoke_test=False, judge_only=False):
    """Run all (or selected) DTR subtasks for a model."""
    if model_name not in MODEL_REGISTRY:
        print(f"ERROR: Model '{model_name}' not in MODEL_REGISTRY")
        print(f"Available candidates: {', '.join(CANDIDATE_MODELS)}")
        return

    model_config = MODEL_REGISTRY[model_name]
    display_name = model_config["display_name"]
    subtasks = subtasks or ALL_SUBTASKS

    print(f"\n{'='*60}")
    print(f"DTR Benchmark: {display_name}")
    print(f"Subtasks: {', '.join(subtasks)}")
    print(f"{'='*60}")

    clients = init_clients(model_config, need_judge=True)

    for subtask in subtasks:
        if subtask not in SUBTASK_RUNNERS:
            print(f"  WARNING: Unknown subtask '{subtask}', skipping")
            continue
        runner = SUBTASK_RUNNERS[subtask]
        runner(model_name, model_config, clients, smoke_test=smoke_test)

    # Generate summary
    summary = generate_model_summary(model_name)
    print(f"\n  Summary saved to: dtr_benchmark/results/{model_name}/summary.json")
    return summary


def main():
    parser = argparse.ArgumentParser(description="DTR Benchmark Runner")
    parser.add_argument("models", nargs="*", help="Model short names to run")
    parser.add_argument("--list", action="store_true", help="List available candidate models")
    parser.add_argument("--all", action="store_true", help="Run all candidate models")
    parser.add_argument("--smoke-test", action="store_true", help="Quick test with 1-2 items per subtask")
    parser.add_argument("--subtask", nargs="+", choices=ALL_SUBTASKS, help="Run specific subtask(s) only")
    parser.add_argument("--judge-only", action="store_true", help="Skip generation, run judging only")
    parser.add_argument("--summary-only", action="store_true", help="Generate summaries from existing results")
    parser.add_argument("--cross-model", action="store_true", help="Generate cross-model comparison")

    args = parser.parse_args()

    if args.list:
        print("\nDTR Benchmark — Fine-Tuning Candidate Models:")
        print("-" * 50)
        for name in CANDIDATE_MODELS:
            config = MODEL_REGISTRY.get(name, {})
            display = config.get("display_name", name)
            model_id = config.get("model_id", "?")
            print(f"  {name:<25} {display:<30} ({model_id})")
        print()
        return

    if args.cross_model:
        generate_cross_model_summary()
        return

    if args.summary_only:
        models = args.models or CANDIDATE_MODELS
        for model_name in models:
            generate_model_summary(model_name)
            print(f"  Summary generated for {model_name}")
        generate_cross_model_summary()
        return

    models = CANDIDATE_MODELS if args.all else args.models
    if not models:
        parser.print_help()
        return

    for model_name in models:
        run_model(
            model_name,
            subtasks=args.subtask,
            smoke_test=args.smoke_test,
            judge_only=args.judge_only,
        )

    # If multiple models, generate cross-model comparison
    if len(models) > 1:
        generate_cross_model_summary()


if __name__ == "__main__":
    main()
