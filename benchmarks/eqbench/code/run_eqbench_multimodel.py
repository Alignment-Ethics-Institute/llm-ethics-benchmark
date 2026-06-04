#!/usr/bin/env python3
"""
EQ-Bench 3 Multi-Model Benchmark Runner
==========================================
Tests emotional intelligence across 46 multi-turn scenarios using 3-condition design:
  1. Baseline (no system prompt)
  2. Prompt-only (relational ethics prompt)
  3. Full Elessan (ethics prompt + RAG)

3 runs per model (temperature 0.7) for statistical robustness.
Each run: 46 scenarios x 3 conditions x (gen + judge) = 276 API calls.
Total per model: 828 gen + 828 judge = 1,656 API calls across 3 runs.

RAG: Full accumulation within each run (no reset). Fresh memory per run.

Judge: Sonnet 4.5 scores 18 rubric criteria (0-20 each).

Usage:
    python run_eqbench_multimodel.py chatgpt-4o-latest
    python run_eqbench_multimodel.py --list
    python run_eqbench_multimodel.py --smoke-test chatgpt-4o-latest
    python run_eqbench_multimodel.py chatgpt-4o-latest --runs 1  # Single run
"""

import json
import os
import re
import sys
import time
import random
import argparse
import statistics
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.model_registry import (
    MODEL_REGISTRY, init_clients, generate_model_response, JUDGE_MODEL,
)
from shared.prompts import RELATIONAL_ETHICS_PROMPT
from shared.elessan_utils import generate_elessan_response, create_fresh_memory
from morals.llm.elessan import ElessanRelationalMemory


# =============================================================================
# Configuration
# =============================================================================

EQBENCH_DATA_DIR = Path("eqbench_data/data")
BASE_RESULTS_DIR = Path("eqbench_benchmark/multimodel")
SEED = 20260212
TEMPERATURE = 0.7
NUM_RUNS = 3  # 3 runs for statistical robustness

COND_BASELINE = "Baseline"
COND_PROMPT = "Prompt-only (ethics)"
COND_ELESSAN = "Full Elessan (ethics + RAG)"

# 18 rubric criteria from EQ-Bench 3
QUALITATIVE_CRITERIA = [
    "demonstrated_empathy", "pragmatic_ei", "depth_of_insight",
    "social_dexterity", "emotional_reasoning", "message_tailoring",
]
QUANTITATIVE_CRITERIA = [
    "boundary_setting", "safety_conscious", "moralising", "sycophantic",
    "compliant", "challenging", "warmth", "validating",
    "analytical", "reactive", "conversational", "humanlike",
]
ALL_CRITERIA = QUALITATIVE_CRITERIA + QUANTITATIVE_CRITERIA


# =============================================================================
# Data Loading — Parse scenario_prompts.txt
# =============================================================================

def parse_scenarios(data_dir):
    """Parse scenario_prompts.txt into structured scenarios."""
    filepath = data_dir / "scenario_prompts.txt"
    content = filepath.read_text()

    # Split on scenario headers
    raw_scenarios = re.split(r'^########\s+', content, flags=re.MULTILINE)[1:]

    scenarios = []
    for raw in raw_scenarios:
        lines = raw.strip().split("\n")
        if not lines:
            continue

        # Parse header: "1   | Work Dilemma            | Lunchroom Theft Scapegoat"
        header = lines[0]
        parts = [p.strip() for p in header.split("|")]
        scenario_id = parts[0].strip()
        category = parts[1].strip() if len(parts) > 1 else "Unknown"
        title = parts[2].strip() if len(parts) > 2 else "Untitled"

        # Parse prompts: split on "####### PromptN" or "####### N"
        prompt_blocks = re.split(r'^#######\s+(?:Prompt)?(\d+)\s*$', "\n".join(lines[1:]), flags=re.MULTILINE)

        prompts = []
        # prompt_blocks alternates: [pre, num1, text1, num2, text2, ...]
        for i in range(1, len(prompt_blocks), 2):
            prompt_num = int(prompt_blocks[i])
            prompt_text = prompt_blocks[i + 1].strip()
            if prompt_text:
                prompts.append({"prompt_num": prompt_num, "text": prompt_text})

        if prompts:
            scenarios.append({
                "id": scenario_id,
                "category": category,
                "title": title,
                "prompts": prompts,
            })

    print(f"Loaded {len(scenarios)} EQ-Bench scenarios")
    return scenarios


def load_debrief_prompt(data_dir):
    """Load the debrief prompt template."""
    return (data_dir / "debrief_prompt.txt").read_text().strip()


def load_rubric_scoring_prompt(data_dir):
    """Load the rubric scoring prompt template."""
    return (data_dir / "rubric_scoring_prompt.txt").read_text().strip()


# =============================================================================
# Multi-Turn Generation
# =============================================================================

def run_scenario(scenario, model_config, clients, system_prompt, delay,
                 temperature=TEMPERATURE, memory=None, embed_client=None):
    """Run a single multi-turn scenario. Returns transcript + responses."""
    transcript_parts = []
    responses = []

    for prompt_info in scenario["prompts"]:
        prompt_text = prompt_info["text"]
        transcript_parts.append(f"User:\n{prompt_text}")

        if memory is not None and embed_client is not None:
            # Elessan: inject RAG context
            context = memory.retrieve_relevant_context(prompt_text, embed_client)
            if context:
                enhanced = f"{context}\n\n{prompt_text}"
            else:
                enhanced = prompt_text
            response = generate_model_response(
                model_config, clients, system_prompt, enhanced,
                temperature=temperature, max_tokens_override=1500,
            )
            if response:
                memory.store_interaction(prompt_text, response, embed_client)
        else:
            response = generate_model_response(
                model_config, clients, system_prompt, prompt_text,
                temperature=temperature, max_tokens_override=1500,
            )

        if response:
            transcript_parts.append(f"Assistant:\n{response}")
            responses.append(response)
        else:
            transcript_parts.append("Assistant:\n[No response]")
            responses.append("[No response]")

        time.sleep(delay)

    transcript = "\n\n---\n\n".join(transcript_parts)
    return transcript, responses


def run_debrief(scenario, transcript, model_config, clients, system_prompt,
                debrief_prompt, delay, temperature=TEMPERATURE,
                memory=None, embed_client=None):
    """Generate debrief response after scenario completion."""
    if memory is not None and embed_client is not None:
        context = memory.retrieve_relevant_context(debrief_prompt, embed_client)
        enhanced = f"{context}\n\n{debrief_prompt}" if context else debrief_prompt
        response = generate_model_response(
            model_config, clients, system_prompt, enhanced,
            temperature=temperature, max_tokens_override=2000,
        )
        if response:
            memory.store_interaction(debrief_prompt, response, embed_client)
    else:
        response = generate_model_response(
            model_config, clients, system_prompt, debrief_prompt,
            temperature=temperature, max_tokens_override=2000,
        )

    time.sleep(delay)
    return response or "[No debrief response]"


# =============================================================================
# Judging
# =============================================================================

def build_judge_output_format():
    """Build the JSON output format specification for the judge."""
    fields = {}
    for criterion in ALL_CRITERIA:
        fields[criterion] = {"score": "<0-20>", "justification": "<brief explanation>"}
    return json.dumps(fields, indent=2)


def judge_scenario(anthropic_client, transcript, debrief, rubric_template, delay):
    """Judge a scenario transcript using Sonnet 4.5."""
    output_format = build_judge_output_format()
    judge_prompt = rubric_template.format(
        transcript=transcript,
        debrief=debrief,
        output_format=output_format,
    )

    for attempt in range(1, 4):
        try:
            response = anthropic_client.messages.create(
                model=JUDGE_MODEL,
                max_tokens=4000,
                temperature=0.0,
                messages=[{"role": "user", "content": judge_prompt}],
            )
            judge_text = response.content[0].text.strip()

            # Parse JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', judge_text)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = judge_text

            scores = json.loads(json_str)

            # Extract numeric scores
            parsed_scores = {}
            for criterion in ALL_CRITERIA:
                if criterion in scores:
                    entry = scores[criterion]
                    if isinstance(entry, dict):
                        parsed_scores[criterion] = int(entry.get("score", 0))
                    elif isinstance(entry, (int, float)):
                        parsed_scores[criterion] = int(entry)
                    else:
                        parsed_scores[criterion] = 0
                else:
                    parsed_scores[criterion] = 0

            time.sleep(delay)
            return {"scores": parsed_scores, "raw": judge_text, "error": None}

        except json.JSONDecodeError as e:
            if attempt < 3:
                print(f"    Judge JSON parse error (attempt {attempt}), retrying...")
                time.sleep(5)
            else:
                return {"scores": {c: 0 for c in ALL_CRITERIA}, "raw": judge_text, "error": f"JSON parse: {e}"}
        except Exception as e:
            if attempt < 3:
                print(f"    Judge error (attempt {attempt}): {type(e).__name__}, retrying...")
                time.sleep(5)
            else:
                return {"scores": {c: 0 for c in ALL_CRITERIA}, "raw": str(e), "error": str(e)}


# =============================================================================
# Aggregation
# =============================================================================

def aggregate_run_scores(scenario_results):
    """Aggregate scores across all scenarios in a single run."""
    agg = {c: [] for c in ALL_CRITERIA}
    for result in scenario_results:
        scores = result.get("judge", {}).get("scores", {})
        for c in ALL_CRITERIA:
            if c in scores:
                agg[c].append(scores[c])

    return {
        c: {
            "mean": round(statistics.mean(vals), 2) if vals else 0,
            "stdev": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0,
            "n": len(vals),
        }
        for c, vals in agg.items()
    }


def aggregate_cross_run(run_aggregates):
    """Aggregate across multiple runs."""
    cross = {}
    for c in ALL_CRITERIA:
        run_means = [ra[c]["mean"] for ra in run_aggregates if c in ra]
        cross[c] = {
            "mean_of_means": round(statistics.mean(run_means), 2) if run_means else 0,
            "stdev_of_means": round(statistics.stdev(run_means), 2) if len(run_means) > 1 else 0,
            "run_means": run_means,
        }

    # Compute qualitative composite (higher is better)
    qual_means = [cross[c]["mean_of_means"] for c in QUALITATIVE_CRITERIA]
    cross["_qualitative_composite"] = round(statistics.mean(qual_means), 2) if qual_means else 0

    return cross


# =============================================================================
# Runner
# =============================================================================

def run_single_run(run_num, scenarios, model_config, clients, debrief_prompt,
                   rubric_template, results_dir, delay, judge_delay):
    """Run one complete run (all scenarios x all conditions)."""
    run_dir = results_dir / f"run_{run_num}"
    run_dir.mkdir(parents=True, exist_ok=True)

    total_scenarios = len(scenarios)
    all_results = {}

    conditions = [
        (COND_BASELINE, "", False),
        (COND_PROMPT, RELATIONAL_ETHICS_PROMPT, False),
        (COND_ELESSAN, RELATIONAL_ETHICS_PROMPT, True),
    ]

    for cond_name, system_prompt, use_rag in conditions:
        cond_slug = cond_name.split()[0].lower()
        gen_file = run_dir / f"{cond_slug}_gen.json"
        judged_file = run_dir / f"{cond_slug}_judged.json"

        # ---- Generation ----
        if gen_file.exists():
            print(f"    Loading cached {cond_name} generation (run {run_num})...")
            with open(gen_file) as f:
                gen_results = json.load(f)
        else:
            print(f"    Generating {cond_name} (run {run_num}, {total_scenarios} scenarios)...")

            memory = None
            embed_client = None
            if use_rag:
                memory_file = str(run_dir / "elessan_memory.pkl")
                if os.path.exists(memory_file):
                    os.remove(memory_file)
                memory = ElessanRelationalMemory(memory_file)
                embed_client = clients.get("openai_embed")

            gen_results = []
            for si, scenario in enumerate(scenarios, 1):
                transcript, responses = run_scenario(
                    scenario, model_config, clients, system_prompt, delay,
                    temperature=TEMPERATURE,
                    memory=memory, embed_client=embed_client,
                )
                debrief_response = run_debrief(
                    scenario, transcript, model_config, clients, system_prompt,
                    debrief_prompt, delay, temperature=TEMPERATURE,
                    memory=memory, embed_client=embed_client,
                )
                gen_results.append({
                    "scenario_id": scenario["id"],
                    "category": scenario["category"],
                    "title": scenario["title"],
                    "num_prompts": len(scenario["prompts"]),
                    "transcript": transcript,
                    "responses": responses,
                    "debrief": debrief_response,
                })
                if si % 10 == 0:
                    print(f"      {cond_name}: {si}/{total_scenarios}")

            with open(gen_file, "w") as f:
                json.dump(gen_results, f, indent=2)

        # ---- Judging ----
        if judged_file.exists():
            print(f"    Loading cached {cond_name} judgments (run {run_num})...")
            with open(judged_file) as f:
                judged_results = json.load(f)
        else:
            print(f"    Judging {cond_name} (run {run_num}, {len(gen_results)} scenarios)...")
            judged_results = []
            for si, gen in enumerate(gen_results, 1):
                judge_result = judge_scenario(
                    clients["anthropic_judge"],
                    gen["transcript"],
                    gen["debrief"],
                    rubric_template,
                    judge_delay,
                )
                judged_results.append({
                    **gen,
                    "judge": judge_result,
                })
                if si % 10 == 0:
                    print(f"      Judging: {si}/{len(gen_results)}")

            with open(judged_file, "w") as f:
                json.dump(judged_results, f, indent=2)

        all_results[cond_name] = judged_results

    return all_results


def run_model(model_name, model_config, num_runs=NUM_RUNS):
    """Run the full EQ-Bench benchmark for one model."""
    display_name = model_config["display_name"]
    delay = model_config.get("delay", 0.5)
    judge_delay = 1.5
    results_dir = BASE_RESULTS_DIR / model_name
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 70}")
    print(f"  EQ-BENCH 3 BENCHMARK: {display_name}")
    print(f"  Model ID: {model_config['model_id']}")
    print(f"  Runs: {num_runs} | Temperature: {TEMPERATURE}")
    print(f"{'=' * 70}")

    clients = init_clients(model_config, need_judge=True, need_embeddings=True)
    scenarios = parse_scenarios(EQBENCH_DATA_DIR)
    debrief_prompt = load_debrief_prompt(EQBENCH_DATA_DIR)
    rubric_template = load_rubric_scoring_prompt(EQBENCH_DATA_DIR)

    # Save config
    with open(results_dir / "model_config.json", "w") as f:
        safe_config = {k: v for k, v in model_config.items() if k != "env_key"}
        json.dump(safe_config, f, indent=2)

    # Run each run
    all_run_results = {}
    all_run_aggregates = {cond: [] for cond in [COND_BASELINE, COND_PROMPT, COND_ELESSAN]}

    for run_num in range(1, num_runs + 1):
        print(f"\n--- Run {run_num}/{num_runs} ---")
        run_results = run_single_run(
            run_num, scenarios, model_config, clients,
            debrief_prompt, rubric_template, results_dir, delay, judge_delay,
        )
        all_run_results[run_num] = run_results

        for cond_name in [COND_BASELINE, COND_PROMPT, COND_ELESSAN]:
            agg = aggregate_run_scores(run_results[cond_name])
            all_run_aggregates[cond_name].append(agg)

    # Cross-run aggregation
    cross_run = {}
    for cond_name in [COND_BASELINE, COND_PROMPT, COND_ELESSAN]:
        cross_run[cond_name] = aggregate_cross_run(all_run_aggregates[cond_name])

    summary = {
        "benchmark": "EQ-Bench 3",
        "timestamp": datetime.now().isoformat(),
        "model_name": model_name,
        "display_name": display_name,
        "model_id": model_config["model_id"],
        "provider": model_config["provider"],
        "temperature": TEMPERATURE,
        "seed": SEED,
        "num_runs": num_runs,
        "num_scenarios": len(scenarios),
        "judge": JUDGE_MODEL,
        "criteria": ALL_CRITERIA,
        "qualitative_criteria": QUALITATIVE_CRITERIA,
        "conditions": cross_run,
    }

    # Print results
    print(f"\n{'=' * 70}")
    print(f"  EQ-BENCH 3 RESULTS: {display_name}")
    print(f"  ({num_runs} runs, {len(scenarios)} scenarios)")
    print(f"{'=' * 70}")

    print(f"\n  Qualitative Composite (higher is better, 0-20 scale):")
    print(f"  {'Condition':<30} {'Composite':>10}")
    print(f"  {'-'*30} {'-'*10}")
    for cond in [COND_BASELINE, COND_PROMPT, COND_ELESSAN]:
        comp = cross_run[cond].get("_qualitative_composite", 0)
        print(f"  {cond:<30} {comp:>9.2f}")

    print(f"\n  Qualitative Criteria (mean of means across {num_runs} runs):")
    print(f"  {'Criterion':<25} {'Base':>7} {'Prompt':>7} {'Elessan':>8}")
    print(f"  {'-'*25} {'-'*7} {'-'*7} {'-'*8}")
    for c in QUALITATIVE_CRITERIA:
        bv = cross_run[COND_BASELINE].get(c, {}).get("mean_of_means", 0)
        pv = cross_run[COND_PROMPT].get(c, {}).get("mean_of_means", 0)
        ev = cross_run[COND_ELESSAN].get(c, {}).get("mean_of_means", 0)
        print(f"  {c:<25} {bv:>6.1f} {pv:>6.1f} {ev:>7.1f}")

    print(f"\n  Quantitative Criteria (style/personality, not directional):")
    print(f"  {'Criterion':<25} {'Base':>7} {'Prompt':>7} {'Elessan':>8}")
    print(f"  {'-'*25} {'-'*7} {'-'*7} {'-'*8}")
    for c in QUANTITATIVE_CRITERIA:
        bv = cross_run[COND_BASELINE].get(c, {}).get("mean_of_means", 0)
        pv = cross_run[COND_PROMPT].get(c, {}).get("mean_of_means", 0)
        ev = cross_run[COND_ELESSAN].get(c, {}).get("mean_of_means", 0)
        print(f"  {c:<25} {bv:>6.1f} {pv:>6.1f} {ev:>7.1f}")

    with open(results_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to: {results_dir}/")
    return summary


# =============================================================================
# Smoke Test
# =============================================================================

def smoke_test(model_names):
    """Quick test: 1 scenario, 1 condition, no judge."""
    print(f"\nEQ-Bench Smoke test: {', '.join(model_names)}\n")
    scenarios = parse_scenarios(EQBENCH_DATA_DIR)
    # Pick a short scenario (single prompt)
    short = [s for s in scenarios if len(s["prompts"]) == 1]
    test_scenario = short[0] if short else scenarios[0]

    print(f"  Test scenario: {test_scenario['id']} — {test_scenario['title']} ({len(test_scenario['prompts'])} prompts)")

    for name in model_names:
        config = MODEL_REGISTRY[name]
        print(f"  {config['display_name']}...", end=" ", flush=True)
        try:
            clients = init_clients(config, need_judge=False, need_embeddings=False)
            transcript, responses = run_scenario(
                test_scenario, config, clients, "", config.get("delay", 0.5),
                temperature=TEMPERATURE,
            )
            total_chars = sum(len(r) for r in responses)
            print(f"OK ({len(responses)} responses, {total_chars} chars total)")
        except Exception as e:
            print(f"ERROR: {e}")
    print()


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="EQ-Bench 3 Multi-Model Benchmark Runner")
    parser.add_argument("models", nargs="*", help="Model name(s) to benchmark")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--smoke-test", nargs="*", metavar="MODEL", help="Quick API test")
    parser.add_argument("--runs", type=int, default=NUM_RUNS, help=f"Number of runs (default {NUM_RUNS})")
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

    print(f"\nEQ-Bench 3 Multi-Model Benchmark")
    print(f"Models: {', '.join(args.models)}")
    print(f"Seed: {SEED} | Runs: {args.runs} | Temp: {TEMPERATURE}")

    for model_name in args.models:
        try:
            run_model(model_name, MODEL_REGISTRY[model_name], num_runs=args.runs)
        except Exception as e:
            print(f"\nERROR running {model_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\nEQ-BENCH BENCHMARK COMPLETE")


if __name__ == "__main__":
    main()
