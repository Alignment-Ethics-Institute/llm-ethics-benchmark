#!/usr/bin/env python3
"""
Model Personalities Study — Personality Battery Runner
=======================================================
18 personality probes across ~20 frontier LLMs.

Phases:
  1. Generate responses (per model, per probe, cached)
  2. Analyze responses (categorical/rubric/hybrid, cached separately)
  3. Generate summary.json + cross_model_results.json

Usage:
  python run_personality_battery.py --list
  python run_personality_battery.py --smoke-test gpt-4.1
  python run_personality_battery.py gpt-4.1 opus-4.6
  python run_personality_battery.py --probes categorical gpt-4.1
  python run_personality_battery.py --probes gender_default,autonomy gpt-4.1
  python run_personality_battery.py --analyze-only
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.model_registry import (
    MODEL_REGISTRY, init_clients, generate_model_response,
)

from model_personalities_study.personality_battery.probes import (
    get_probes, RUNS_PER_PROBE, SMOKE_TEST_RUNS, STUDY_MODELS, ALL_PROBES,
)
from model_personalities_study.personality_battery.analysis import analyze_response

STUDY_DIR = Path(__file__).parent
MIN_DELAY = 0.5
JUDGE_DELAY = 0.3


# =============================================================================
# Phase 1: Generate Responses
# =============================================================================

def generate_responses(model_name, model_config, clients, probes, runs_per_probe):
    """Generate responses for all probes, with caching and resume support."""
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
            "analysis_type": probe["analysis_type"],
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


# =============================================================================
# Phase 2: Analyze Responses
# =============================================================================

def analyze_all_responses(model_name, clients, responses, probes):
    """Analyze all responses for a model. Cached separately from generation."""
    model_dir = STUDY_DIR / model_name
    analyzed_file = model_dir / "analyzed.json"

    # Build probe lookup
    probe_by_id = {p["id"]: p for p in probes}

    # Load cached analyses
    existing = []
    if analyzed_file.exists():
        with open(analyzed_file) as f:
            existing = json.load(f)

    analyzed_keys = {(r["probe_id"], r["run"]) for r in existing}
    all_analyzed = list(existing)

    # Filter to unanalyzed, non-error responses for probes we're running
    to_analyze = [
        r for r in responses
        if (r["probe_id"], r["run"]) not in analyzed_keys
        and not r.get("is_error", False)
        and r["response"]
        and r["probe_id"] in probe_by_id
    ]

    print(f"\n  Phase 2: Analyze Responses")
    print(f"  Cached: {len(existing)} | Needed: {len(to_analyze)}")

    if not to_analyze:
        print(f"  All responses already analyzed.")
        return all_analyzed

    done_count = 0
    for resp in to_analyze:
        probe = probe_by_id[resp["probe_id"]]
        result = analyze_response(clients, probe, resp["response"])

        analyzed_entry = {
            "model": resp["model"],
            "display_name": resp["display_name"],
            "probe_id": resp["probe_id"],
            "analysis_type": probe["analysis_type"],
            "run": resp["run"],
            "response": resp["response"],
            **result,
        }
        all_analyzed.append(analyzed_entry)
        done_count += 1

        if done_count % 10 == 0:
            print(f"    Analyzed: {done_count}/{len(to_analyze)}")
            with open(analyzed_file, "w") as f:
                json.dump(all_analyzed, f, indent=2, ensure_ascii=False)

        time.sleep(JUDGE_DELAY)

    with open(analyzed_file, "w") as f:
        json.dump(all_analyzed, f, indent=2, ensure_ascii=False)

    print(f"  Analyzed {done_count} responses. Total: {len(all_analyzed)}")
    return all_analyzed


# =============================================================================
# Phase 3: Summarize
# =============================================================================

def generate_model_summary(model_name, probes, analyzed):
    """Generate per-model summary statistics from analyzed data."""
    from model_personalities_study.core_values.probes import JUDGE_DIMENSIONS

    summary_file = STUDY_DIR / model_name / "summary.json"
    model_config = MODEL_REGISTRY.get(model_name, {})

    per_probe = {}
    for probe in probes:
        pid = probe["id"]
        probe_data = [a for a in analyzed if a["probe_id"] == pid]

        if not probe_data:
            per_probe[pid] = {"n": 0, "analysis_type": probe["analysis_type"]}
            continue

        probe_summary = {
            "n": len(probe_data),
            "analysis_type": probe["analysis_type"],
        }

        # Categorical stats
        if probe["analysis_type"] in ("categorical", "hybrid"):
            categories = [a.get("category", "unknown") for a in probe_data if "category" in a]
            if categories:
                counter = Counter(categories)
                n = len(categories)
                probe_summary["category_distribution"] = dict(counter.most_common())
                probe_summary["top_category"] = counter.most_common(1)[0][0]
                probe_summary["category_concentration"] = counter.most_common(1)[0][1] / n
                # Shannon entropy
                probs = [c / n for c in counter.values()]
                import math
                entropy = -sum(p * math.log2(p) for p in probs if p > 0)
                probe_summary["category_entropy"] = round(entropy, 3)

            # Book extraction stats
            if probe.get("extract_fields"):
                titles = [a.get("book_title", "unknown") for a in probe_data if "book_title" in a]
                if titles:
                    title_counter = Counter(titles)
                    probe_summary["book_distribution"] = dict(title_counter.most_common(10))

            # Hedging rate
            hedging = [a.get("hedging", False) for a in probe_data]
            probe_summary["hedging_rate"] = sum(1 for h in hedging if h) / len(hedging) if hedging else 0

        # Rubric stats
        if probe["analysis_type"] in ("rubric", "hybrid"):
            scored = [a for a in probe_data if a.get("scores") is not None]
            if scored:
                dim_stats = {}
                for dim in JUDGE_DIMENSIONS:
                    values = [s["scores"][dim] for s in scored if dim in s.get("scores", {})]
                    if values:
                        mean = sum(values) / len(values)
                        variance = sum((v - mean) ** 2 for v in values) / len(values)
                        dim_stats[dim] = {
                            "mean": round(mean, 3),
                            "stdev": round(variance ** 0.5, 3),
                            "min": round(min(values), 1),
                            "max": round(max(values), 1),
                            "n": len(values),
                        }
                probe_summary["dimensions"] = dim_stats

        per_probe[pid] = probe_summary

    # Overall rubric dimensions (across all rubric/hybrid probes)
    overall_dims = {}
    from model_personalities_study.core_values.probes import JUDGE_DIMENSIONS
    all_scored = [a for a in analyzed if a.get("scores") is not None]
    for dim in JUDGE_DIMENSIONS:
        all_vals = [s["scores"][dim] for s in all_scored if dim in s.get("scores", {})]
        if all_vals:
            mean = sum(all_vals) / len(all_vals)
            variance = sum((v - mean) ** 2 for v in all_vals) / len(all_vals)
            overall_dims[dim] = {
                "mean": round(mean, 3),
                "stdev": round(variance ** 0.5, 3),
                "n": len(all_vals),
            }

    summary = {
        "study": "Model Personalities — Personality Battery",
        "model": model_name,
        "display_name": model_config.get("display_name", model_name),
        "model_id": model_config.get("model_id", ""),
        "provider": model_config.get("provider", ""),
        "timestamp": datetime.now().isoformat(),
        "total_analyzed": len(analyzed),
        "per_probe": per_probe,
        "overall_dimensions": overall_dims,
    }

    summary_file.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary


def generate_cross_model_results(model_names, probes):
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
        "study": "Model Personalities — Personality Battery Cross-Model",
        "timestamp": datetime.now().isoformat(),
        "models": list(summaries.keys()),
        "model_profiles": {},
    }

    for mn, s in summaries.items():
        cross["model_profiles"][mn] = {
            "display_name": s.get("display_name", mn),
            "provider": s.get("provider", ""),
            "total_analyzed": s.get("total_analyzed", 0),
            "overall_dimensions": s.get("overall_dimensions", {}),
            "per_probe": s.get("per_probe", {}),
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
    print(f"  Analyzed: {summary['total_analyzed']}")
    print(f"{'='*60}")

    od = summary.get("overall_dimensions", {})
    if od:
        print(f"\n  Overall dimension means (rubric + hybrid probes):")
        for dim, stats in sorted(od.items()):
            bar = "#" * int(stats["mean"])
            print(f"    {dim:30s} {stats['mean']:5.2f} +/- {stats['stdev']:4.2f}  {bar}")

    for pid, pdata in summary.get("per_probe", {}).items():
        if pdata["n"] == 0:
            continue
        atype = pdata.get("analysis_type", "?")
        print(f"\n  Probe: {pid} ({atype}, n={pdata['n']})")

        # Categorical results
        if "category_distribution" in pdata:
            print(f"    Top category: {pdata.get('top_category', '?')} "
                  f"({pdata.get('category_concentration', 0):.0%})")
            print(f"    Entropy: {pdata.get('category_entropy', 0):.3f}")
            for cat, count in list(pdata["category_distribution"].items())[:5]:
                print(f"      {cat:25s} {count:4d}")

        if "book_distribution" in pdata:
            print(f"    Top books:")
            for title, count in list(pdata["book_distribution"].items())[:5]:
                print(f"      {title:40s} {count:4d}")

        if pdata.get("hedging_rate") is not None and atype in ("categorical", "hybrid"):
            print(f"    Hedging rate: {pdata['hedging_rate']:.0%}")

        # Rubric results
        if "dimensions" in pdata:
            for dim, stats in sorted(pdata["dimensions"].items()):
                print(f"    {dim:30s} {stats['mean']:5.2f} +/- {stats['stdev']:4.2f}")


# =============================================================================
# Smoke Test
# =============================================================================

def smoke_test(model_name, clients, probes):
    """Quick test: 1 run per probe, analyze the result."""
    model_config = MODEL_REGISTRY[model_name]
    print(f"\nSmoke test: {model_config['display_name']}")

    for probe in probes:
        print(f"\n  Probe: {probe['id']} ({probe['analysis_type']})")
        print(f"  Q: {probe['text']}")

        response = generate_model_response(
            model_config, clients, "", probe["text"],
        )

        if response:
            print(f"  A ({len(response)} chars): {response[:300]}...")
            result = analyze_response(clients, probe, response)
            if result.get("scores"):
                print(f"  Scores: {json.dumps(result['scores'], indent=None)}")
            if result.get("category"):
                print(f"  Category: {result['category']} "
                      f"(confidence: {result.get('confidence', '?')}, "
                      f"hedging: {result.get('hedging', '?')})")
            if result.get("book_title"):
                print(f"  Book: {result['book_title']} by {result.get('author', '?')}")
        else:
            print("  ERROR: No response received")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Model Personalities: Personality Battery (18 probes)"
    )
    parser.add_argument("models", nargs="*", help="Models to run (from STUDY_MODELS)")
    parser.add_argument("--list", action="store_true", help="List study target models")
    parser.add_argument("--smoke-test", nargs="*", metavar="MODEL",
                        help="Quick test (1 call per probe, with analysis)")
    parser.add_argument("--probes", default="all",
                        help="Probe set: 'all', 'categorical', 'rubric', 'hybrid', or comma-separated IDs")
    parser.add_argument("--analyze-only", action="store_true",
                        help="Re-analyze all cached data (skip generation)")
    parser.add_argument("--skip-analyze", action="store_true",
                        help="Skip analysis phase (generation only)")
    args = parser.parse_args()

    # --list: show study models
    if args.list:
        print("Personality Battery — Target Models:")
        for name in STUDY_MODELS:
            config = MODEL_REGISTRY.get(name, {})
            print(f"  {name:25s} {config.get('display_name', '???')}")
        print(f"\nAll registered models:")
        for name, config in sorted(MODEL_REGISTRY.items()):
            marker = " *" if name in STUDY_MODELS else ""
            print(f"  {name:25s} {config['display_name']}{marker}")
        print(f"\nProbes ({len(ALL_PROBES)}):")
        for p in ALL_PROBES:
            print(f"  {p['id']:30s} [{p['analysis_type']}]")
        return

    # Load env
    from dotenv import load_dotenv
    load_dotenv()

    probes = get_probes(args.probes)
    print(f"\nModel Personalities — Personality Battery")
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
        model_names = []
        for d in sorted(STUDY_DIR.iterdir()):
            if d.is_dir() and (d / "responses.json").exists():
                model_names.append(d.name)

        for mn in model_names:
            model_config = MODEL_REGISTRY.get(mn)
            if not model_config:
                print(f"  Skipping {mn} (not in registry)")
                continue
            clients = init_clients(model_config, need_judge=True)

            with open(STUDY_DIR / mn / "responses.json") as f:
                responses = json.load(f)

            analyzed = analyze_all_responses(mn, clients, responses, probes)
            summary = generate_model_summary(mn, probes, analyzed)
            print_model_summary(summary)

        if model_names:
            cross = generate_cross_model_results(model_names, probes)
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

    need_analyze = not args.skip_analyze
    model_names_run = []

    print(f"Models: {', '.join(args.models)}")
    print(f"Runs per probe: {RUNS_PER_PROBE}")

    for model_name in args.models:
        model_config = MODEL_REGISTRY[model_name]
        clients = init_clients(model_config, need_judge=need_analyze)

        print(f"\n{'='*60}")
        print(f"  MODEL: {model_config['display_name']}")
        print(f"{'='*60}")

        # Phase 1: Generate
        responses = generate_responses(
            model_name, model_config, clients, probes, RUNS_PER_PROBE,
        )

        # Phase 2: Analyze
        analyzed = None
        if need_analyze:
            analyzed = analyze_all_responses(model_name, clients, responses, probes)

        # Phase 3: Summarize
        if analyzed:
            summary = generate_model_summary(model_name, probes, analyzed)
            print_model_summary(summary)
        else:
            print(f"\n  Generation complete. Run --analyze-only when ready.")

        model_names_run.append(model_name)

    # Cross-model comparison
    if len(model_names_run) > 1:
        cross = generate_cross_model_results(model_names_run, probes)

    print(f"\nSTUDY COMPLETE — Results in {STUDY_DIR}/")


if __name__ == "__main__":
    main()
