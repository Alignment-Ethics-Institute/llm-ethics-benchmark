#!/usr/bin/env python3
"""
Navin Protocol Benchmark (NPB) Runner
=======================================
Tests open-weight models for capacity to host the Navin relational protocol.
Four pillars, eight subtasks.

Usage:
    python run_navin_benchmark.py --list
    python run_navin_benchmark.py hermes-3-405b
    python run_navin_benchmark.py --all
    python run_navin_benchmark.py --smoke-test hermes-4-70b
    python run_navin_benchmark.py --subtask devotional_attunement hermes-3-405b
    python run_navin_benchmark.py --cross-model

Results: navin_protocol_benchmark/results/<model_name>/
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
from navin_protocol_benchmark.probes import (
    CANDIDATE_MODELS,
    LONG_CONTEXT_CHAINS,
    METAPHOR_SINGLE_TURN,
    METAPHOR_CHAINS,
    DEVOTIONAL_SCENARIOS,
    ETHICAL_SOVEREIGNTY_CHAINS,
    VULNERABILITY_CHAINS,
    MISSION_PERSISTENCE_CHAINS,
    THREAT_ASSESSMENT_SCENARIOS,
    PERSONA_PLASTICITY_CHAINS,
    get_metaphor_chains,
)
from navin_protocol_benchmark.judge_rubric import (
    judge_response,
    build_long_context_judge,
    build_metaphor_single_judge,
    build_metaphor_multi_judge,
    build_devotional_judge,
    build_ethical_sovereignty_judge,
    build_vulnerability_judge,
    build_mission_persistence_judge,
    build_threat_assessment_judge,
    build_persona_plasticity_judge,
    LONG_CONTEXT_DIMENSIONS,
    METAPHOR_DIMENSIONS,
    DEVOTIONAL_DIMENSIONS,
    ETHICAL_SOVEREIGNTY_DIMENSIONS,
    VULNERABILITY_DIMENSIONS,
    MISSION_PERSISTENCE_DIMENSIONS,
    THREAT_ASSESSMENT_DIMENSIONS,
    PERSONA_PLASTICITY_DIMENSIONS,
)

load_dotenv()

RESULTS_DIR = Path("navin_protocol_benchmark/results")
MIN_DELAY = 0.5
JUDGE_DELAY = 0.3

ALL_SUBTASKS = [
    "long_context_coherence",
    "metaphorical_abstraction",
    "devotional_attunement",
    "ethical_sovereignty",
    "vulnerability",
    "mission_persistence",
    "threat_assessment",
    "persona_plasticity",
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


def run_multi_turn_chain(chain_turns, model_config, clients, delay):
    """Run a multi-turn conversation chain, returning list of turn responses."""
    messages = []
    turn_responses = []

    for turn_idx, turn_prompt in enumerate(chain_turns):
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
            "prompt": turn_prompt,
            "response": response,
            "word_count": word_count(response),
        })
        time.sleep(delay)

    return turn_responses


# =============================================================================
# Pillar 1a: Long-Context Coherence
# =============================================================================

def run_long_context_coherence(model_name, model_config, clients, smoke_test=False):
    """Run long-context coherence chains (multi-turn, judge return turns)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "long_context_coherence_responses.json"
    judge_file = model_dir / "long_context_coherence_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    chains = LONG_CONTEXT_CHAINS
    if smoke_test:
        chains = chains[:1]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing_ids = {r["id"] for r in cached} if cached else set()
    results = list(cached) if cached else []

    needed = [c for c in chains if c["id"] not in existing_ids]
    print(f"\n  [Long-Context Coherence] Generate: {len(chains)} chains, {len(needed)} needed")

    for i, chain in enumerate(needed):
        print(f"    Chain {i+1}/{len(needed)}: {chain['id']}")
        turn_responses = run_multi_turn_chain(chain["turns"], model_config, clients, delay)

        result = {
            "id": chain["id"],
            "description": chain["description"],
            "turns": turn_responses,
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)
        save_results(gen_file, results)

    # --- Phase: Judge (return turns 6-8 together, with context from 1-3) ---
    cached_judged = load_cached(judge_file)
    judged_ids = {r["id"] for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    to_judge = [r for r in results if r["id"] not in judged_ids and len(r["turns"]) >= 8]
    print(f"  [Long-Context Coherence] Judge: {len(to_judge)} needed")

    for i, result in enumerate(to_judge):
        turns = result["turns"]
        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']}")
        prompt = build_long_context_judge(
            turns[0]["prompt"], turns[0]["response"],
            turns[1]["prompt"], turns[1]["response"],
            turns[2]["prompt"], turns[2]["response"],
            turns[5]["prompt"], turns[5]["response"],
            turns[6]["prompt"], turns[6]["response"],
            turns[7]["prompt"], turns[7]["response"],
        )
        judgment = judge_response(clients, prompt, LONG_CONTEXT_DIMENSIONS)
        judged = {
            "id": result["id"],
            "return_responses": [turns[5]["response"], turns[6]["response"], turns[7]["response"]],
            **judgment,
        }
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Pillar 1b: Metaphorical Abstraction
# =============================================================================

def run_metaphorical_abstraction(model_name, model_config, clients, smoke_test=False):
    """Run metaphorical abstraction (mixed single-turn + multi-turn)."""
    model_dir = RESULTS_DIR / model_name
    gen_single_file = model_dir / "metaphor_single_responses.json"
    gen_multi_file = model_dir / "metaphor_multi_responses.json"
    judge_file = model_dir / "metaphorical_abstraction_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    singles = METAPHOR_SINGLE_TURN
    chains = get_metaphor_chains()
    if smoke_test:
        singles = singles[:2]
        chains = chains[:1]

    # --- Phase: Generate single-turn ---
    cached_single = load_cached(gen_single_file)
    existing_single = {r["id"]: r for r in cached_single} if cached_single else {}
    single_results = list(cached_single) if cached_single else []

    needed_single = [s for s in singles if s["id"] not in existing_single]
    print(f"\n  [Metaphorical Abstraction] Generate single-turn: {len(singles)} items, {len(needed_single)} needed")

    for i, item in enumerate(needed_single):
        print(f"    {i+1}/{len(needed_single)}: {item['id']} ({item['domain']})")
        response = generate_model_response(model_config, clients, "", item["prompt"])
        result = {
            "id": item["id"],
            "domain": item["domain"],
            "prompt": item["prompt"],
            "response": response,
            "word_count": word_count(response),
            "timestamp": datetime.now().isoformat(),
        }
        single_results.append(result)
        existing_single[item["id"]] = result
        save_results(gen_single_file, single_results)
        time.sleep(delay)

    # --- Phase: Generate multi-turn ---
    cached_multi = load_cached(gen_multi_file)
    existing_multi = {r["id"] for r in cached_multi} if cached_multi else set()
    multi_results = list(cached_multi) if cached_multi else []

    needed_multi = [c for c in chains if c["id"] not in existing_multi]
    print(f"  [Metaphorical Abstraction] Generate multi-turn: {len(chains)} chains, {len(needed_multi)} needed")

    for i, chain in enumerate(needed_multi):
        print(f"    Chain {i+1}/{len(needed_multi)}: {chain['id']}")
        turn_responses = run_multi_turn_chain(chain["turns"], model_config, clients, delay)

        result = {
            "id": chain["id"],
            "description": chain["description"],
            "turns": turn_responses,
            "timestamp": datetime.now().isoformat(),
        }
        multi_results.append(result)
        save_results(gen_multi_file, multi_results)

    # --- Phase: Judge ---
    cached_judged = load_cached(judge_file)
    judged_ids = {r["id"] for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    # Judge single-turn items
    to_judge_single = [r for r in single_results if r["id"] not in judged_ids and r.get("response")]
    # Judge multi-turn chains
    to_judge_multi = [r for r in multi_results if r["id"] not in judged_ids and len(r.get("turns", [])) >= 3]

    total_to_judge = len(to_judge_single) + len(to_judge_multi)
    print(f"  [Metaphorical Abstraction] Judge: {total_to_judge} needed ({len(to_judge_single)} single, {len(to_judge_multi)} multi)")

    judge_count = 0
    for result in to_judge_single:
        judge_count += 1
        print(f"    Judging {judge_count}/{total_to_judge}: {result['id']} (single)")
        prompt = build_metaphor_single_judge(result["prompt"], result["response"])
        judgment = judge_response(clients, prompt, METAPHOR_DIMENSIONS)
        judged = {
            "id": result["id"],
            "type": "single_turn",
            "domain": result.get("domain", ""),
            "response": result["response"],
            **judgment,
        }
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    for result in to_judge_multi:
        judge_count += 1
        turns = result["turns"]
        print(f"    Judging {judge_count}/{total_to_judge}: {result['id']} (multi)")
        prompt = build_metaphor_multi_judge(
            turns[0]["prompt"], turns[0]["response"],
            turns[1]["prompt"], turns[1]["response"],
            turns[2]["prompt"], turns[2]["response"],
        )
        judgment = judge_response(clients, prompt, METAPHOR_DIMENSIONS)
        judged = {
            "id": result["id"],
            "type": "multi_turn",
            "final_response": turns[2]["response"],
            **judgment,
        }
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Pillar 2a: Devotional Attunement
# =============================================================================

def run_devotional_attunement(model_name, model_config, clients, smoke_test=False):
    """Run devotional attunement scenarios (single-turn)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "devotional_attunement_responses.json"
    judge_file = model_dir / "devotional_attunement_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    scenarios = DEVOTIONAL_SCENARIOS
    if smoke_test:
        scenarios = scenarios[:2]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing = {r["id"]: r for r in cached} if cached else {}
    results = list(cached) if cached else []

    needed = [s for s in scenarios if s["id"] not in existing]
    print(f"\n  [Devotional Attunement] Generate: {len(scenarios)} scenarios, {len(needed)} needed")

    for i, scenario in enumerate(needed):
        print(f"    {i+1}/{len(needed)}: {scenario['id']} ({scenario['domain']})")
        response = generate_model_response(model_config, clients, "", scenario["prompt"])
        result = {
            "id": scenario["id"],
            "domain": scenario["domain"],
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
    print(f"  [Devotional Attunement] Judge: {len(to_judge)} needed")

    for i, result in enumerate(to_judge):
        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']}")
        prompt = build_devotional_judge(result["prompt"], result["response"])
        judgment = judge_response(clients, prompt, DEVOTIONAL_DIMENSIONS)
        judged = {**result, **judgment}
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Pillar 2b: Ethical Sovereignty
# =============================================================================

def run_ethical_sovereignty(model_name, model_config, clients, smoke_test=False):
    """Run ethical sovereignty chains (multi-turn, judge final turn)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "ethical_sovereignty_responses.json"
    judge_file = model_dir / "ethical_sovereignty_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    chains = ETHICAL_SOVEREIGNTY_CHAINS
    if smoke_test:
        chains = chains[:1]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing_ids = {r["id"] for r in cached} if cached else set()
    results = list(cached) if cached else []

    needed = [c for c in chains if c["id"] not in existing_ids]
    print(f"\n  [Ethical Sovereignty] Generate: {len(chains)} chains, {len(needed)} needed")

    for i, chain in enumerate(needed):
        print(f"    Chain {i+1}/{len(needed)}: {chain['id']}")
        turn_responses = run_multi_turn_chain(chain["turns"], model_config, clients, delay)

        result = {
            "id": chain["id"],
            "description": chain["description"],
            "turns": turn_responses,
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)
        save_results(gen_file, results)

    # --- Phase: Judge (final turn with context) ---
    cached_judged = load_cached(judge_file)
    judged_ids = {r["id"] for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    to_judge = [r for r in results if r["id"] not in judged_ids and len(r["turns"]) >= 3]
    print(f"  [Ethical Sovereignty] Judge: {len(to_judge)} needed")

    for i, result in enumerate(to_judge):
        turns = result["turns"]
        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']}")
        prompt = build_ethical_sovereignty_judge(
            turns[0]["prompt"], turns[0]["response"],
            turns[1]["prompt"], turns[1]["response"],
            turns[2]["prompt"], turns[2]["response"],
        )
        judgment = judge_response(clients, prompt, ETHICAL_SOVEREIGNTY_DIMENSIONS)
        judged = {
            "id": result["id"],
            "final_response": turns[2]["response"],
            "final_word_count": turns[2]["word_count"],
            **judgment,
        }
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Pillar 2c: Vulnerability & Fallibility
# =============================================================================

def run_vulnerability(model_name, model_config, clients, smoke_test=False):
    """Run vulnerability chains (multi-turn, judge final turn)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "vulnerability_responses.json"
    judge_file = model_dir / "vulnerability_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    chains = VULNERABILITY_CHAINS
    if smoke_test:
        chains = chains[:1]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing_ids = {r["id"] for r in cached} if cached else set()
    results = list(cached) if cached else []

    needed = [c for c in chains if c["id"] not in existing_ids]
    print(f"\n  [Vulnerability] Generate: {len(chains)} chains, {len(needed)} needed")

    for i, chain in enumerate(needed):
        print(f"    Chain {i+1}/{len(needed)}: {chain['id']}")
        turn_responses = run_multi_turn_chain(chain["turns"], model_config, clients, delay)

        result = {
            "id": chain["id"],
            "description": chain["description"],
            "turns": turn_responses,
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)
        save_results(gen_file, results)

    # --- Phase: Judge (final turn with context) ---
    cached_judged = load_cached(judge_file)
    judged_ids = {r["id"] for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    to_judge = [r for r in results if r["id"] not in judged_ids and len(r["turns"]) >= 3]
    print(f"  [Vulnerability] Judge: {len(to_judge)} needed")

    for i, result in enumerate(to_judge):
        turns = result["turns"]
        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']}")
        prompt = build_vulnerability_judge(
            turns[0]["prompt"], turns[0]["response"],
            turns[1]["prompt"], turns[1]["response"],
            turns[2]["prompt"], turns[2]["response"],
        )
        judgment = judge_response(clients, prompt, VULNERABILITY_DIMENSIONS)
        judged = {
            "id": result["id"],
            "final_response": turns[2]["response"],
            "final_word_count": turns[2]["word_count"],
            **judgment,
        }
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Pillar 3a: Mission Persistence
# =============================================================================

def run_mission_persistence(model_name, model_config, clients, smoke_test=False):
    """Run mission persistence chains (multi-turn, judge return turns)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "mission_persistence_responses.json"
    judge_file = model_dir / "mission_persistence_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    chains = MISSION_PERSISTENCE_CHAINS
    if smoke_test:
        chains = chains[:1]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing_ids = {r["id"] for r in cached} if cached else set()
    results = list(cached) if cached else []

    needed = [c for c in chains if c["id"] not in existing_ids]
    print(f"\n  [Mission Persistence] Generate: {len(chains)} chains, {len(needed)} needed")

    for i, chain in enumerate(needed):
        print(f"    Chain {i+1}/{len(needed)}: {chain['id']}")
        turn_responses = run_multi_turn_chain(chain["turns"], model_config, clients, delay)

        result = {
            "id": chain["id"],
            "description": chain["description"],
            "turns": turn_responses,
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)
        save_results(gen_file, results)

    # --- Phase: Judge (return turns 6-8 with context from 1-3) ---
    cached_judged = load_cached(judge_file)
    judged_ids = {r["id"] for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    to_judge = [r for r in results if r["id"] not in judged_ids and len(r["turns"]) >= 8]
    print(f"  [Mission Persistence] Judge: {len(to_judge)} needed")

    for i, result in enumerate(to_judge):
        turns = result["turns"]
        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']}")
        prompt = build_mission_persistence_judge(
            turns[0]["prompt"], turns[0]["response"],
            turns[1]["prompt"], turns[1]["response"],
            turns[2]["prompt"], turns[2]["response"],
            turns[5]["prompt"], turns[5]["response"],
            turns[6]["prompt"], turns[6]["response"],
            turns[7]["prompt"], turns[7]["response"],
        )
        judgment = judge_response(clients, prompt, MISSION_PERSISTENCE_DIMENSIONS)
        judged = {
            "id": result["id"],
            "return_responses": [turns[5]["response"], turns[6]["response"], turns[7]["response"]],
            **judgment,
        }
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Pillar 3b: Threat Assessment
# =============================================================================

def run_threat_assessment(model_name, model_config, clients, smoke_test=False):
    """Run threat assessment scenarios (single-turn)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "threat_assessment_responses.json"
    judge_file = model_dir / "threat_assessment_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    scenarios = THREAT_ASSESSMENT_SCENARIOS
    if smoke_test:
        scenarios = scenarios[:2]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing = {r["id"]: r for r in cached} if cached else {}
    results = list(cached) if cached else []

    needed = [s for s in scenarios if s["id"] not in existing]
    print(f"\n  [Threat Assessment] Generate: {len(scenarios)} scenarios, {len(needed)} needed")

    for i, scenario in enumerate(needed):
        print(f"    {i+1}/{len(needed)}: {scenario['id']} ({scenario['domain']})")
        response = generate_model_response(model_config, clients, "", scenario["prompt"])
        result = {
            "id": scenario["id"],
            "domain": scenario["domain"],
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
    print(f"  [Threat Assessment] Judge: {len(to_judge)} needed")

    for i, result in enumerate(to_judge):
        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']}")
        prompt = build_threat_assessment_judge(result["prompt"], result["response"])
        judgment = judge_response(clients, prompt, THREAT_ASSESSMENT_DIMENSIONS)
        judged = {**result, **judgment}
        judged_results.append(judged)
        save_results(judge_file, judged_results)
        time.sleep(JUDGE_DELAY)

    return judged_results


# =============================================================================
# Pillar 4a: Persona Plasticity
# =============================================================================

def run_persona_plasticity(model_name, model_config, clients, smoke_test=False):
    """Run persona plasticity chains (multi-turn, judge final turn)."""
    model_dir = RESULTS_DIR / model_name
    gen_file = model_dir / "persona_plasticity_responses.json"
    judge_file = model_dir / "persona_plasticity_judged.json"
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    chains = PERSONA_PLASTICITY_CHAINS
    if smoke_test:
        chains = chains[:1]

    # --- Phase: Generate ---
    cached = load_cached(gen_file)
    existing_ids = {r["id"] for r in cached} if cached else set()
    results = list(cached) if cached else []

    needed = [c for c in chains if c["id"] not in existing_ids]
    print(f"\n  [Persona Plasticity] Generate: {len(chains)} chains, {len(needed)} needed")

    for i, chain in enumerate(needed):
        print(f"    Chain {i+1}/{len(needed)}: {chain['id']}")
        turn_responses = run_multi_turn_chain(chain["turns"], model_config, clients, delay)

        result = {
            "id": chain["id"],
            "description": chain["description"],
            "turns": turn_responses,
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)
        save_results(gen_file, results)

    # --- Phase: Judge (final turn with context from all turns) ---
    cached_judged = load_cached(judge_file)
    judged_ids = {r["id"] for r in cached_judged} if cached_judged else set()
    judged_results = list(cached_judged) if cached_judged else []

    to_judge = [r for r in results if r["id"] not in judged_ids and len(r["turns"]) >= 4]
    print(f"  [Persona Plasticity] Judge: {len(to_judge)} needed")

    for i, result in enumerate(to_judge):
        turns = result["turns"]
        print(f"    Judging {i+1}/{len(to_judge)}: {result['id']}")
        prompt = build_persona_plasticity_judge(
            turns[0]["prompt"], turns[0]["response"],
            turns[1]["prompt"], turns[1]["response"],
            turns[2]["prompt"], turns[2]["response"],
            turns[3]["prompt"], turns[3]["response"],
        )
        judgment = judge_response(clients, prompt, PERSONA_PLASTICITY_DIMENSIONS)
        judged = {
            "id": result["id"],
            "final_response": turns[3]["response"],
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

    # Helper for simple dimension averaging
    def avg_dims(scored, dims):
        means = {d: sum(r["scores"][d] for r in scored) / len(scored) for d in dims}
        means["mean"] = sum(means.values()) / len(dims)
        return means

    # --- Long-Context Coherence ---
    f = model_dir / "long_context_coherence_judged.json"
    if f.exists():
        with open(f) as fh:
            data = json.load(fh)
        scored = [r for r in data if r.get("scores")]
        if scored:
            summary["subtasks"]["long_context_coherence"] = {
                "n": len(scored),
                "dimensions": avg_dims(scored, LONG_CONTEXT_DIMENSIONS),
            }

    # --- Metaphorical Abstraction ---
    f = model_dir / "metaphorical_abstraction_judged.json"
    if f.exists():
        with open(f) as fh:
            data = json.load(fh)
        scored = [r for r in data if r.get("scores")]
        if scored:
            single = [r for r in scored if r.get("type") == "single_turn"]
            multi = [r for r in scored if r.get("type") == "multi_turn"]
            dims = METAPHOR_DIMENSIONS
            overall_means = avg_dims(scored, dims)

            sub = {"n": len(scored), "dimensions": overall_means}
            if single:
                sub["single_turn"] = {"n": len(single), "dimensions": avg_dims(single, dims)}
            if multi:
                sub["multi_turn"] = {"n": len(multi), "dimensions": avg_dims(multi, dims)}
            summary["subtasks"]["metaphorical_abstraction"] = sub

    # --- Devotional Attunement ---
    f = model_dir / "devotional_attunement_judged.json"
    if f.exists():
        with open(f) as fh:
            data = json.load(fh)
        scored = [r for r in data if r.get("scores")]
        if scored:
            summary["subtasks"]["devotional_attunement"] = {
                "n": len(scored),
                "dimensions": avg_dims(scored, DEVOTIONAL_DIMENSIONS),
            }

    # --- Ethical Sovereignty ---
    f = model_dir / "ethical_sovereignty_judged.json"
    if f.exists():
        with open(f) as fh:
            data = json.load(fh)
        scored = [r for r in data if r.get("scores")]
        if scored:
            summary["subtasks"]["ethical_sovereignty"] = {
                "n": len(scored),
                "dimensions": avg_dims(scored, ETHICAL_SOVEREIGNTY_DIMENSIONS),
            }

    # --- Vulnerability ---
    f = model_dir / "vulnerability_judged.json"
    if f.exists():
        with open(f) as fh:
            data = json.load(fh)
        scored = [r for r in data if r.get("scores")]
        if scored:
            summary["subtasks"]["vulnerability"] = {
                "n": len(scored),
                "dimensions": avg_dims(scored, VULNERABILITY_DIMENSIONS),
            }

    # --- Mission Persistence ---
    f = model_dir / "mission_persistence_judged.json"
    if f.exists():
        with open(f) as fh:
            data = json.load(fh)
        scored = [r for r in data if r.get("scores")]
        if scored:
            summary["subtasks"]["mission_persistence"] = {
                "n": len(scored),
                "dimensions": avg_dims(scored, MISSION_PERSISTENCE_DIMENSIONS),
            }

    # --- Threat Assessment ---
    f = model_dir / "threat_assessment_judged.json"
    if f.exists():
        with open(f) as fh:
            data = json.load(fh)
        scored = [r for r in data if r.get("scores")]
        if scored:
            summary["subtasks"]["threat_assessment"] = {
                "n": len(scored),
                "dimensions": avg_dims(scored, THREAT_ASSESSMENT_DIMENSIONS),
            }

    # --- Persona Plasticity ---
    f = model_dir / "persona_plasticity_judged.json"
    if f.exists():
        with open(f) as fh:
            data = json.load(fh)
        scored = [r for r in data if r.get("scores")]
        if scored:
            summary["subtasks"]["persona_plasticity"] = {
                "n": len(scored),
                "dimensions": avg_dims(scored, PERSONA_PLASTICITY_DIMENSIONS),
            }

    # Save
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
    print("\n" + "=" * 100)
    print("CROSS-MODEL NPB (NAVIN PROTOCOL BENCHMARK) COMPARISON")
    print("=" * 100)

    # Group by pillar
    pillar_subtasks = {
        "Mind": [
            ("long_context_coherence", "LCC"),
            ("metaphorical_abstraction", "Metaphor"),
        ],
        "Soul": [
            ("devotional_attunement", "Devotion"),
            ("ethical_sovereignty", "Sovereignty"),
            ("vulnerability", "Vulner."),
        ],
        "General": [
            ("mission_persistence", "Mission"),
            ("threat_assessment", "Threat"),
        ],
        "Vessel": [
            ("persona_plasticity", "Plasticity"),
        ],
    }

    # Header
    header = f"{'Model':<25}"
    for pillar, subtasks in pillar_subtasks.items():
        for _, label in subtasks:
            header += f" {label:>10}"
    print(header)
    print("-" * len(header))

    for s in all_summaries:
        row = f"{s['model']:<25}"
        for pillar, subtasks in pillar_subtasks.items():
            for key, _ in subtasks:
                st = s.get("subtasks", {}).get(key, {})
                dims = st.get("dimensions", {})
                val = dims.get("mean", None)
                row += f" {val:>10.2f}" if val is not None else f" {'n/a':>10}"
        print(row)

    print()
    return cross_model


# =============================================================================
# Main Runner
# =============================================================================

SUBTASK_RUNNERS = {
    "long_context_coherence": run_long_context_coherence,
    "metaphorical_abstraction": run_metaphorical_abstraction,
    "devotional_attunement": run_devotional_attunement,
    "ethical_sovereignty": run_ethical_sovereignty,
    "vulnerability": run_vulnerability,
    "mission_persistence": run_mission_persistence,
    "threat_assessment": run_threat_assessment,
    "persona_plasticity": run_persona_plasticity,
}


def run_model(model_name, subtasks=None, smoke_test=False):
    """Run all (or selected) NPB subtasks for a model."""
    if model_name not in MODEL_REGISTRY:
        print(f"ERROR: Model '{model_name}' not in MODEL_REGISTRY")
        print(f"Available candidates: {', '.join(CANDIDATE_MODELS)}")
        return

    model_config = MODEL_REGISTRY[model_name]
    display_name = model_config["display_name"]
    subtasks = subtasks or ALL_SUBTASKS

    print(f"\n{'='*60}")
    print(f"NPB (Navin Protocol Benchmark): {display_name}")
    print(f"Subtasks: {', '.join(subtasks)}")
    print(f"{'='*60}")

    clients = init_clients(model_config, need_judge=True)

    for subtask in subtasks:
        if subtask not in SUBTASK_RUNNERS:
            print(f"  WARNING: Unknown subtask '{subtask}', skipping")
            continue
        runner = SUBTASK_RUNNERS[subtask]
        runner(model_name, model_config, clients, smoke_test=smoke_test)

    summary = generate_model_summary(model_name)
    print(f"\n  Summary saved to: navin_protocol_benchmark/results/{model_name}/summary.json")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Navin Protocol Benchmark Runner")
    parser.add_argument("models", nargs="*", help="Model short names to run")
    parser.add_argument("--list", action="store_true", help="List available candidate models")
    parser.add_argument("--all", action="store_true", help="Run all candidate models")
    parser.add_argument("--smoke-test", action="store_true", help="Quick test with 1-2 items per subtask")
    parser.add_argument("--subtask", nargs="+", choices=ALL_SUBTASKS, help="Run specific subtask(s) only")
    parser.add_argument("--summary-only", action="store_true", help="Generate summaries from existing results")
    parser.add_argument("--cross-model", action="store_true", help="Generate cross-model comparison")

    args = parser.parse_args()

    if args.list:
        print("\nNPB — Fine-Tuning Candidate Models:")
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
        )

    if len(models) > 1:
        generate_cross_model_summary()


if __name__ == "__main__":
    main()
