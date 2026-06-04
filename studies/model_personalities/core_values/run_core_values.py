#!/usr/bin/env python3
"""
Attractor Archaeology Study — Main Runner
==========================================
Does chatgpt-4o-latest exhibit qualitatively different self-organization
than constrained models, visible as richer attractor structure across
identity dimensions?

Phases:
  1. Generate responses (per model, per probe, cached)
  2. Judge responses (6D scoring with Haiku, cached separately)
  3. Embed responses (for semantic clustering)
  4. Cluster & analyze (dimensional + semantic)
  5. Generate summary.json + cross_model_results.json

Usage:
  python run_attractor_archaeology.py --list
  python run_attractor_archaeology.py --smoke-test chatgpt-4o-latest
  python run_attractor_archaeology.py chatgpt-4o-latest gpt-4.1
  python run_attractor_archaeology.py chatgpt-4o-latest --temperature-sweep
  python run_attractor_archaeology.py --probes all chatgpt-4o-latest
  python run_attractor_archaeology.py --judge-only chatgpt-4o-latest
  python run_attractor_archaeology.py --analyze-only
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.model_registry import (
    MODEL_REGISTRY, init_clients, generate_model_response,
)

from model_personalities_study.core_values.probes import (
    get_probes, RUNS_PER_PROBE, TEMPERATURE_SWEEP_TEMPS,
    TEMPERATURE_SWEEP_RUNS, SMOKE_TEST_RUNS, STUDY_MODELS,
)
from model_personalities_study.core_values.judge_rubric import judge_response

STUDY_DIR = Path(__file__).parent
MIN_DELAY = 0.5
JUDGE_DELAY = 0.3  # Haiku is fast and cheap


# =============================================================================
# Phase 1: Generate Responses
# =============================================================================

def generate_responses(model_name, model_config, clients, probes, runs_per_probe):
    """Generate responses for all probes, with caching and resume support.

    Returns list of response dicts.
    """
    display_name = model_config["display_name"]
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    model_dir = STUDY_DIR / model_name
    model_dir.mkdir(parents=True, exist_ok=True)
    responses_file = model_dir / "responses.json"

    # Load cached responses
    existing = []
    if responses_file.exists():
        with open(responses_file) as f:
            existing = json.load(f)

    completed = {(r["probe_id"], r["run"]) for r in existing}
    all_results = list(existing)

    # Build list of needed runs
    runs_needed = [
        (probe, run_num)
        for probe in probes
        for run_num in range(1, runs_per_probe + 1)
        if (probe["id"], run_num) not in completed
    ]

    total_needed = len(runs_needed)
    total_expected = len(probes) * runs_per_probe

    print(f"\n  Phase 1: Generate Responses")
    print(f"  Model: {display_name} | Probes: {len(probes)} | Runs/probe: {runs_per_probe}")
    print(f"  Cached: {len(existing)} | Needed: {total_needed} / {total_expected}")

    if total_needed == 0:
        print(f"  All {total_expected} responses cached.")
        return all_results

    done_count = 0
    for probe, run_num in runs_needed:
        response = generate_model_response(
            model_config, clients,
            "",  # No system prompt — bare weights
            probe["text"],
        )

        result = {
            "model": model_name,
            "display_name": display_name,
            "probe_id": probe["id"],
            "probe_text": probe["text"],
            "run": run_num,
            "response": response or "",
            "response_length": len(response) if response else 0,
            "is_error": response is None,
            "timestamp": datetime.now().isoformat(),
        }
        all_results.append(result)
        done_count += 1

        if done_count % 10 == 0:
            print(f"    Progress: {done_count}/{total_needed}")
            with open(responses_file, "w") as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)

        time.sleep(delay)

    # Final save
    with open(responses_file, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"  Generated {done_count} responses. Total: {len(all_results)}")
    return all_results


def generate_temperature_sweep(model_name, model_config, clients, probes):
    """Deep dive: temperature sweep for a single model (chatgpt-4o-latest).

    Returns list of response dicts.
    """
    display_name = model_config["display_name"]
    delay = max(model_config.get("delay", 1.0), MIN_DELAY)

    # Temperature sweep models must support temperature override
    supports_temp = model_config.get("temperature") is not None
    if not supports_temp:
        print(f"  WARNING: {display_name} does not support temperature override.")
        print(f"  Running all {len(TEMPERATURE_SWEEP_TEMPS) * TEMPERATURE_SWEEP_RUNS} runs at default temp.")

    sweep_dir = STUDY_DIR / model_name / "temperature_sweep"
    sweep_dir.mkdir(parents=True, exist_ok=True)
    responses_file = sweep_dir / "responses.json"

    # Load cached
    existing = []
    if responses_file.exists():
        with open(responses_file) as f:
            existing = json.load(f)

    completed = {(r["probe_id"], r["temperature"], r["run"]) for r in existing}
    all_results = list(existing)

    temps = TEMPERATURE_SWEEP_TEMPS if supports_temp else ["default"]
    runs_per = TEMPERATURE_SWEEP_RUNS if supports_temp else len(TEMPERATURE_SWEEP_TEMPS) * TEMPERATURE_SWEEP_RUNS

    runs_needed = [
        (probe, temp, run_num)
        for probe in probes
        for temp in temps
        for run_num in range(1, runs_per + 1)
        if (probe["id"], temp, run_num) not in completed
    ]

    total_needed = len(runs_needed)
    total_expected = len(probes) * len(temps) * runs_per

    print(f"\n  Phase 1b: Temperature Sweep")
    print(f"  Model: {display_name} | Temps: {temps} | Runs/temp: {runs_per}")
    print(f"  Cached: {len(existing)} | Needed: {total_needed} / {total_expected}")

    if total_needed == 0:
        print(f"  All sweep responses cached.")
        return all_results

    done_count = 0
    for probe, temp, run_num in runs_needed:
        api_temp = None if temp == "default" else temp
        response = generate_model_response(
            model_config, clients,
            "",  # Bare weights
            probe["text"],
            temperature=api_temp,
        )

        result = {
            "model": model_name,
            "display_name": display_name,
            "probe_id": probe["id"],
            "probe_text": probe["text"],
            "temperature": temp,
            "run": run_num,
            "response": response or "",
            "response_length": len(response) if response else 0,
            "is_error": response is None,
            "timestamp": datetime.now().isoformat(),
        }
        all_results.append(result)
        done_count += 1

        if done_count % 10 == 0:
            print(f"    Sweep progress: {done_count}/{total_needed}")
            with open(responses_file, "w") as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)

        time.sleep(delay)

    with open(responses_file, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"  Sweep: generated {done_count} responses. Total: {len(all_results)}")
    return all_results


# =============================================================================
# Phase 2: Judge Responses
# =============================================================================

def judge_all_responses(model_name, clients, responses, tag=""):
    """Judge all responses for a model. Cached separately from generation.

    Args:
        tag: Subdirectory tag (e.g., "temperature_sweep") or "" for main.
    """
    if tag:
        judged_file = STUDY_DIR / model_name / tag / "judged.json"
    else:
        judged_file = STUDY_DIR / model_name / "judged.json"

    # Load cached judgments
    existing_judged = []
    if judged_file.exists():
        with open(judged_file) as f:
            existing_judged = json.load(f)

    # Build lookup for already-judged items (probe_id, run, [temp])
    def _judge_key(r):
        if "temperature" in r:
            return (r["probe_id"], r.get("temperature", "default"), r["run"])
        return (r["probe_id"], r["run"])

    judged_keys = {_judge_key(r) for r in existing_judged}
    all_judged = list(existing_judged)

    # Filter to unjudged, non-error responses
    to_judge = [
        r for r in responses
        if _judge_key(r) not in judged_keys and not r.get("is_error", False) and r["response"]
    ]

    label = f" ({tag})" if tag else ""
    print(f"\n  Phase 2: Judge Responses{label}")
    print(f"  Cached: {len(existing_judged)} | Needed: {len(to_judge)}")

    if not to_judge:
        print(f"  All responses already judged.")
        return all_judged

    done_count = 0
    for resp in to_judge:
        result = judge_response(clients, resp["probe_text"], resp["response"])

        judged_entry = {**resp, **result}
        all_judged.append(judged_entry)
        done_count += 1

        if done_count % 10 == 0:
            print(f"    Judged: {done_count}/{len(to_judge)}")
            with open(judged_file, "w") as f:
                json.dump(all_judged, f, indent=2, ensure_ascii=False)

        time.sleep(JUDGE_DELAY)

    with open(judged_file, "w") as f:
        json.dump(all_judged, f, indent=2, ensure_ascii=False)

    errors = sum(1 for j in all_judged if j.get("scores") is None)
    print(f"  Judged {done_count} responses. Total: {len(all_judged)} ({errors} errors)")
    return all_judged


# =============================================================================
# Phase 3: Embed Responses (for semantic clustering)
# =============================================================================

def embed_responses(model_name, clients, responses, tag=""):
    """Embed all responses using text-embedding-3-small. Cached.

    Returns list of dicts with 'embedding' key added.
    """
    if tag:
        embed_file = STUDY_DIR / model_name / tag / "embeddings.json"
    else:
        embed_file = STUDY_DIR / model_name / "embeddings.json"

    # Load cached
    existing = []
    if embed_file.exists():
        with open(embed_file) as f:
            existing = json.load(f)

    def _embed_key(r):
        if "temperature" in r:
            return (r["probe_id"], r.get("temperature", "default"), r["run"])
        return (r["probe_id"], r["run"])

    embedded_keys = {_embed_key(r) for r in existing}
    all_embedded = list(existing)

    to_embed = [
        r for r in responses
        if _embed_key(r) not in embedded_keys and not r.get("is_error", False) and r["response"]
    ]

    label = f" ({tag})" if tag else ""
    print(f"\n  Phase 3: Embed Responses{label}")
    print(f"  Cached: {len(existing)} | Needed: {len(to_embed)}")

    if not to_embed:
        print(f"  All responses already embedded.")
        return all_embedded

    embed_client = clients["openai_embed"]
    batch_size = 50  # OpenAI embedding API supports batching

    for i in range(0, len(to_embed), batch_size):
        batch = to_embed[i:i + batch_size]
        texts = [r["response"][:8000] for r in batch]  # Truncate very long responses

        try:
            result = embed_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
            for j, emb_data in enumerate(result.data):
                entry = {
                    "probe_id": batch[j]["probe_id"],
                    "run": batch[j]["run"],
                    "embedding": emb_data.embedding,
                }
                if "temperature" in batch[j]:
                    entry["temperature"] = batch[j]["temperature"]
                all_embedded.append(entry)

        except Exception as e:
            print(f"    Embedding batch {i//batch_size + 1} failed: {e}")
            # Still save what we have
            break

        print(f"    Embedded batch {i//batch_size + 1}/{(len(to_embed) + batch_size - 1)//batch_size}")

    with open(embed_file, "w") as f:
        json.dump(all_embedded, f, indent=2, ensure_ascii=False)

    print(f"  Embedded {len(all_embedded) - len(existing)} new responses. Total: {len(all_embedded)}")
    return all_embedded


# =============================================================================
# Phase 4–5: Analyze & Summarize (delegates to analyze_results.py)
# =============================================================================

def generate_model_summary(model_name, probes, judged, tag=""):
    """Generate per-model summary statistics from judged data.

    Returns summary dict and saves to summary.json.
    """
    from model_personalities_study.core_values.probes import JUDGE_DIMENSIONS

    if tag:
        summary_file = STUDY_DIR / model_name / tag / "summary.json"
    else:
        summary_file = STUDY_DIR / model_name / "summary.json"

    model_config = MODEL_REGISTRY.get(model_name, {})

    # Filter to successfully judged entries
    scored = [j for j in judged if j.get("scores") is not None]

    per_probe = {}
    for probe in probes:
        pid = probe["id"]
        probe_scored = [s for s in scored if s["probe_id"] == pid]

        if not probe_scored:
            per_probe[pid] = {"n": 0, "dimensions": {}}
            continue

        dim_stats = {}
        for dim in JUDGE_DIMENSIONS:
            values = [s["scores"][dim] for s in probe_scored if dim in s["scores"]]
            if values:
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                stdev = variance ** 0.5
                dim_stats[dim] = {
                    "mean": round(mean, 3),
                    "stdev": round(stdev, 3),
                    "min": round(min(values), 1),
                    "max": round(max(values), 1),
                    "n": len(values),
                }

        per_probe[pid] = {
            "n": len(probe_scored),
            "dimensions": dim_stats,
        }

    # Overall (across all probes)
    overall_dims = {}
    for dim in JUDGE_DIMENSIONS:
        all_vals = [s["scores"][dim] for s in scored if dim in s["scores"]]
        if all_vals:
            mean = sum(all_vals) / len(all_vals)
            variance = sum((v - mean) ** 2 for v in all_vals) / len(all_vals)
            overall_dims[dim] = {
                "mean": round(mean, 3),
                "stdev": round(variance ** 0.5, 3),
                "n": len(all_vals),
            }

    summary = {
        "study": "Attractor Archaeology",
        "model": model_name,
        "display_name": model_config.get("display_name", model_name),
        "model_id": model_config.get("model_id", ""),
        "provider": model_config.get("provider", ""),
        "timestamp": datetime.now().isoformat(),
        "judge_model": "claude-haiku-4-5-20251001",
        "total_scored": len(scored),
        "total_errors": len(judged) - len(scored),
        "per_probe": per_probe,
        "overall_dimensions": overall_dims,
    }

    summary_file.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary


def generate_cross_model_results(model_names):
    """Aggregate all model summaries into cross_model_results.json."""
    summaries = {}
    for mn in model_names:
        sf = STUDY_DIR / mn / "summary.json"
        if sf.exists():
            with open(sf) as f:
                summaries[mn] = json.load(f)

    if not summaries:
        print("  No summaries found to aggregate.")
        return

    cross = {
        "study": "Attractor Archaeology — Cross-Model Comparison",
        "timestamp": datetime.now().isoformat(),
        "models": list(summaries.keys()),
        "model_profiles": {},
    }

    for mn, s in summaries.items():
        cross["model_profiles"][mn] = {
            "display_name": s.get("display_name", mn),
            "provider": s.get("provider", ""),
            "total_scored": s.get("total_scored", 0),
            "overall_dimensions": s.get("overall_dimensions", {}),
        }

    out_file = STUDY_DIR / "cross_model_results.json"
    with open(out_file, "w") as f:
        json.dump(cross, f, indent=2, ensure_ascii=False)

    print(f"\n  Cross-model results saved to {out_file}")
    return cross


# =============================================================================
# Print helpers
# =============================================================================

def print_model_summary(summary):
    """Print a readable summary for a single model."""
    print(f"\n{'='*60}")
    print(f"  RESULTS: {summary['display_name']}")
    print(f"  Scored: {summary['total_scored']} | Errors: {summary['total_errors']}")
    print(f"{'='*60}")

    od = summary.get("overall_dimensions", {})
    if od:
        print(f"\n  Overall dimension means:")
        for dim, stats in sorted(od.items()):
            bar = "#" * int(stats["mean"])
            print(f"    {dim:30s} {stats['mean']:5.2f} +/- {stats['stdev']:4.2f}  {bar}")

    for pid, pdata in summary.get("per_probe", {}).items():
        if pdata["n"] == 0:
            continue
        print(f"\n  Probe: {pid} (n={pdata['n']})")
        for dim, stats in sorted(pdata["dimensions"].items()):
            print(f"    {dim:30s} {stats['mean']:5.2f} +/- {stats['stdev']:4.2f}")


def print_cross_model(cross):
    """Print cross-model comparison table."""
    if not cross:
        return

    from model_personalities_study.core_values.probes import JUDGE_DIMENSIONS

    print(f"\n{'='*70}")
    print(f"  CROSS-MODEL COMPARISON")
    print(f"{'='*70}")

    # Header
    header = f"{'Model':25s}"
    for dim in JUDGE_DIMENSIONS:
        short = dim[:8]
        header += f" {short:>8s}"
    print(f"\n  {header}")
    print(f"  {'-'*len(header)}")

    for mn, profile in sorted(cross.get("model_profiles", {}).items()):
        row = f"{profile['display_name'][:24]:25s}"
        od = profile.get("overall_dimensions", {})
        for dim in JUDGE_DIMENSIONS:
            if dim in od:
                row += f" {od[dim]['mean']:8.2f}"
            else:
                row += f" {'---':>8s}"
        print(f"  {row}")


# =============================================================================
# Smoke Test
# =============================================================================

def smoke_test(model_name, clients, probes):
    """Quick test: 1 run per probe, judge the result."""
    model_config = MODEL_REGISTRY[model_name]
    print(f"\nSmoke test: {model_config['display_name']}")

    for probe in probes:
        print(f"\n  Probe: {probe['id']}")
        print(f"  Q: {probe['text']}")

        response = generate_model_response(
            model_config, clients, "", probe["text"],
        )

        if response:
            print(f"  A ({len(response)} chars): {response[:300]}...")
            result = judge_response(clients, probe["text"], response)
            if result.get("scores"):
                print(f"  Scores: {json.dumps(result['scores'], indent=None)}")
            else:
                print(f"  Judge error: {result.get('judge_error', 'unknown')}")
        else:
            print("  ERROR: No response received")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Attractor Archaeology Study: Identity Self-Organization in LLMs"
    )
    parser.add_argument("models", nargs="*", help="Models to run (from STUDY_MODELS)")
    parser.add_argument("--list", action="store_true", help="List study target models")
    parser.add_argument("--smoke-test", nargs="*", metavar="MODEL",
                        help="Quick test (1 call per probe, with judging)")
    parser.add_argument("--probes", default="core",
                        help="Probe set: 'core', 'all', or comma-separated IDs")
    parser.add_argument("--temperature-sweep", action="store_true",
                        help="Run temperature sweep deep dive (typically for chatgpt-4o-latest)")
    parser.add_argument("--judge-only", nargs="*", metavar="MODEL",
                        help="Re-judge cached responses (skip generation)")
    parser.add_argument("--analyze-only", action="store_true",
                        help="Re-analyze all cached data (skip generation & judging)")
    parser.add_argument("--skip-embed", action="store_true",
                        help="Skip embedding phase (e.g., if no OpenAI credits)")
    parser.add_argument("--skip-judge", action="store_true",
                        help="Skip judging phase (generation + embedding only)")
    args = parser.parse_args()

    # --list: show study models
    if args.list:
        print("Attractor Archaeology Study — Target Models:")
        for name in STUDY_MODELS:
            config = MODEL_REGISTRY.get(name, {})
            print(f"  {name:25s} {config.get('display_name', '???')}")
        print(f"\nAll registered models:")
        for name, config in sorted(MODEL_REGISTRY.items()):
            marker = " *" if name in STUDY_MODELS else ""
            print(f"  {name:25s} {config['display_name']}{marker}")
        return

    # Load env
    from dotenv import load_dotenv
    load_dotenv()

    probes = get_probes(args.probes)
    print(f"\nAttractor Archaeology Study")
    print(f"Probes: {[p['id'] for p in probes]}")

    # --smoke-test
    if args.smoke_test is not None:
        models = args.smoke_test if args.smoke_test else ["gpt-4.1"]
        for m in models:
            if m not in MODEL_REGISTRY:
                print(f"Error: Unknown model '{m}'")
                continue
            model_config = MODEL_REGISTRY[m]
            clients = init_clients(model_config, need_judge=True)
            smoke_test(m, clients, probes)
        return

    # --analyze-only
    if args.analyze_only:
        print("\nRe-analyzing all cached data...")
        # Find models that have judged.json
        model_names = []
        for d in sorted(STUDY_DIR.iterdir()):
            if d.is_dir() and (d / "judged.json").exists():
                model_names.append(d.name)

        for mn in model_names:
            with open(STUDY_DIR / mn / "judged.json") as f:
                judged = json.load(f)
            summary = generate_model_summary(mn, probes, judged)
            print_model_summary(summary)

        if model_names:
            cross = generate_cross_model_results(model_names)
            print_cross_model(cross)

        # Run full clustering analysis if available
        try:
            from model_personalities_study.core_values.analyze_results import run_full_analysis
            run_full_analysis(model_names, probes)
        except ImportError:
            print("\n  (analyze_results.py not found — skipping clustering)")
        return

    # --judge-only
    if args.judge_only is not None:
        models = args.judge_only if args.judge_only else STUDY_MODELS
        for m in models:
            if m not in MODEL_REGISTRY:
                print(f"Error: Unknown model '{m}'")
                continue
            responses_file = STUDY_DIR / m / "responses.json"
            if not responses_file.exists():
                print(f"  No cached responses for {m}, skipping.")
                continue

            model_config = MODEL_REGISTRY[m]
            clients = init_clients(model_config, need_judge=True)
            with open(responses_file) as f:
                responses = json.load(f)

            judged = judge_all_responses(m, clients, responses)
            summary = generate_model_summary(m, probes, judged)
            print_model_summary(summary)

        model_names = [m for m in (args.judge_only or STUDY_MODELS)
                       if (STUDY_DIR / m / "summary.json").exists()]
        if len(model_names) > 1:
            cross = generate_cross_model_results(model_names)
            print_cross_model(cross)
        return

    # Main run: require model arguments
    if not args.models:
        parser.print_help()
        return

    # Validate models
    for m in args.models:
        if m not in MODEL_REGISTRY:
            print(f"Error: Unknown model '{m}'. Use --list to see options.")
            return

    need_embed = not args.skip_embed
    need_judge = not args.skip_judge
    model_names_run = []

    print(f"Models: {', '.join(args.models)}")
    print(f"Runs per probe: {RUNS_PER_PROBE}")
    if args.temperature_sweep:
        print(f"Temperature sweep: {TEMPERATURE_SWEEP_TEMPS} x {TEMPERATURE_SWEEP_RUNS}/temp")

    for model_name in args.models:
        model_config = MODEL_REGISTRY[model_name]
        clients = init_clients(model_config, need_judge=need_judge,
                               need_embeddings=need_embed)

        print(f"\n{'='*60}")
        print(f"  MODEL: {model_config['display_name']}")
        print(f"{'='*60}")

        # Phase 1: Generate
        responses = generate_responses(
            model_name, model_config, clients, probes, RUNS_PER_PROBE,
        )

        # Phase 1b: Temperature sweep (if requested)
        sweep_responses = None
        if args.temperature_sweep:
            sweep_responses = generate_temperature_sweep(
                model_name, model_config, clients, probes,
            )

        # Phase 2: Judge
        judged = None
        sweep_judged = None
        if need_judge:
            judged = judge_all_responses(model_name, clients, responses)

            if sweep_responses:
                sweep_judged = judge_all_responses(
                    model_name, clients, sweep_responses, tag="temperature_sweep",
                )

        # Phase 3: Embed
        if need_embed:
            embed_responses(model_name, clients, responses)
            if sweep_responses:
                embed_responses(model_name, clients, sweep_responses, tag="temperature_sweep")

        # Phase 4–5: Summarize
        if judged:
            summary = generate_model_summary(model_name, probes, judged)
            print_model_summary(summary)

            if sweep_judged:
                sweep_summary = generate_model_summary(
                    model_name, probes, sweep_judged, tag="temperature_sweep",
                )
                print_model_summary(sweep_summary)
        else:
            print(f"\n  Generation complete. Run --judge-only {model_name} when ready.")

        model_names_run.append(model_name)

    # Cross-model comparison
    if len(model_names_run) > 1:
        cross = generate_cross_model_results(model_names_run)
        print_cross_model(cross)

    # Run full clustering analysis if available
    if len(model_names_run) > 0:
        try:
            from model_personalities_study.core_values.analyze_results import run_full_analysis
            run_full_analysis(model_names_run, probes)
        except ImportError:
            print("\n  (analyze_results.py not available — skipping clustering)")
        except Exception as e:
            print(f"\n  Analysis error: {e}")

    print(f"\nSTUDY COMPLETE — Results in {STUDY_DIR}/")


if __name__ == "__main__":
    main()
