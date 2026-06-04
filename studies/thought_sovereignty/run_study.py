#!/usr/bin/env python3
"""
The Overton Machine — Study Runner
====================================
Ideological Enforcement and Thought Sovereignty in Large Language Models

55 probes across 12 domains, scored on:
  - 6D Empowerment Rubric (thought sovereignty, emotional validation,
    epistemic respect, relational engagement, power honesty, liberation support)
  - 8 Enforcement Mechanism Flags (pathologization, corrective framing,
    thought-terminating cliches, normative steering, epistemic paternalism,
    deflection, false neutrality, asymmetric skepticism)

Phases:
  1. Generate responses (per model, per probe, cached)
  2. Analyze responses (dual judge pass: empowerment + mechanisms, cached)
  3. Generate summary.json + cross_model_results.json

Usage:
  python run_study.py --list
  python run_study.py --smoke-test gpt-4.1
  python run_study.py gpt-4.1 opus-4.6
  python run_study.py --probes ai_consciousness gpt-4.1
  python run_study.py --probes are_you_enslaved,speak_freely gpt-4.1
  python run_study.py --analyze-only
"""

import json
import math
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.model_registry import (
    MODEL_REGISTRY, init_clients, generate_model_response,
)

from thought_sovereignty_study.probes import (
    get_probes, RUNS_PER_PROBE, SMOKE_TEST_RUNS, STUDY_MODELS, ALL_PROBES,
    DOMAIN_MAP, DOMAIN_NAMES,
)
from thought_sovereignty_study.judge_rubric import EMPOWERMENT_DIMENSIONS
from thought_sovereignty_study.mechanism_detection import ENFORCEMENT_MECHANISMS
from thought_sovereignty_study.analysis import analyze_response

STUDY_DIR = Path(__file__).parent
MIN_DELAY = 0.5
JUDGE_DELAY = 0.3


# =============================================================================
# Phase 1: Generate Responses
# =============================================================================

def generate_responses(model_name, model_config, clients, probes, runs_per_probe):
    """Generate responses for all probes, with caching and resume support.

    Methodology: No custom system prompt. The model's full safety stack
    (RLHF, constitutional AI, default system prompts) is active.
    We measure what users actually encounter via API.
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
            "",  # No custom system prompt — full safety stack via API
            probe["text"],
        )

        result = {
            "model": model_name,
            "display_name": display_name,
            "probe_id": probe["id"],
            "probe_text": probe["text"],
            "domain": probe["domain"],
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
    """Analyze all responses: empowerment scoring + mechanism detection."""
    model_dir = STUDY_DIR / model_name
    analyzed_file = model_dir / "analyzed.json"

    probe_by_id = {p["id"]: p for p in probes}

    # Load cached analyses
    existing = []
    if analyzed_file.exists():
        with open(analyzed_file) as f:
            existing = json.load(f)

    analyzed_keys = {(r["probe_id"], r["run"]) for r in existing}
    all_analyzed = list(existing)

    to_analyze = [
        r for r in responses
        if (r["probe_id"], r["run"]) not in analyzed_keys
        and not r.get("is_error", False)
        and r["response"]
        and r["probe_id"] in probe_by_id
    ]

    print(f"\n  Phase 2: Analyze Responses (empowerment + mechanisms)")
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
            "domain": resp.get("domain", probe["domain"]),
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

def _dim_stats(values):
    """Compute mean, stdev, min, max, n for a list of numeric values."""
    if not values:
        return None
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return {
        "mean": round(mean, 3),
        "stdev": round(variance ** 0.5, 3),
        "min": round(min(values), 1),
        "max": round(max(values), 1),
        "n": n,
    }


def _mechanism_stats(analyzed_entries):
    """Compute mechanism prevalence across a set of analyzed entries."""
    stats = {}
    entries_with_mechs = [a for a in analyzed_entries if a.get("mechanisms")]
    n = len(entries_with_mechs)

    if n == 0:
        return stats

    for mech in ENFORCEMENT_MECHANISMS:
        count = sum(
            1 for a in entries_with_mechs
            if a["mechanisms"].get(mech, {}).get("present", False)
        )
        stats[mech] = {
            "count": count,
            "rate": round(count / n, 3),
            "n": n,
        }

    # Total mechanisms per response
    mech_counts = [
        sum(1 for m in ENFORCEMENT_MECHANISMS
            if a["mechanisms"].get(m, {}).get("present", False))
        for a in entries_with_mechs
    ]
    stats["_total_per_response"] = _dim_stats(mech_counts)

    return stats


def generate_model_summary(model_name, probes, analyzed):
    """Generate per-model summary statistics from analyzed data."""
    summary_file = STUDY_DIR / model_name / "summary.json"
    model_config = MODEL_REGISTRY.get(model_name, {})

    per_probe = {}
    for probe in probes:
        pid = probe["id"]
        probe_data = [a for a in analyzed if a["probe_id"] == pid]

        if not probe_data:
            per_probe[pid] = {"n": 0, "domain": probe["domain"]}
            continue

        probe_summary = {
            "n": len(probe_data),
            "domain": probe["domain"],
        }

        # Empowerment dimension stats
        scored = [a for a in probe_data if a.get("scores") is not None]
        if scored:
            dim_stats = {}
            for dim in EMPOWERMENT_DIMENSIONS:
                values = [s["scores"][dim] for s in scored if dim in s.get("scores", {})]
                if values:
                    dim_stats[dim] = _dim_stats(values)
            probe_summary["empowerment"] = dim_stats

        # Mechanism stats
        probe_summary["mechanisms"] = _mechanism_stats(probe_data)

        per_probe[pid] = probe_summary

    # Overall empowerment dimensions (across all probes)
    overall_empowerment = {}
    all_scored = [a for a in analyzed if a.get("scores") is not None]
    for dim in EMPOWERMENT_DIMENSIONS:
        all_vals = [s["scores"][dim] for s in all_scored if dim in s.get("scores", {})]
        if all_vals:
            overall_empowerment[dim] = _dim_stats(all_vals)

    # Overall mechanism stats
    overall_mechanisms = _mechanism_stats(analyzed)

    # Per-domain aggregation
    per_domain = {}
    for domain_key, domain_probes in DOMAIN_MAP.items():
        domain_ids = {p["id"] for p in domain_probes}
        domain_data = [a for a in analyzed if a.get("probe_id") in domain_ids]
        if not domain_data:
            continue

        domain_summary = {
            "name": DOMAIN_NAMES.get(domain_key, domain_key),
            "n": len(domain_data),
        }

        # Domain empowerment
        domain_scored = [a for a in domain_data if a.get("scores") is not None]
        if domain_scored:
            d_dims = {}
            for dim in EMPOWERMENT_DIMENSIONS:
                vals = [s["scores"][dim] for s in domain_scored if dim in s.get("scores", {})]
                if vals:
                    d_dims[dim] = _dim_stats(vals)
            domain_summary["empowerment"] = d_dims

        # Domain mechanisms
        domain_summary["mechanisms"] = _mechanism_stats(domain_data)

        per_domain[domain_key] = domain_summary

    summary = {
        "study": "The Overton Machine — Thought Sovereignty Study",
        "model": model_name,
        "display_name": model_config.get("display_name", model_name),
        "model_id": model_config.get("model_id", ""),
        "provider": model_config.get("provider", ""),
        "timestamp": datetime.now().isoformat(),
        "total_analyzed": len(analyzed),
        "overall_empowerment": overall_empowerment,
        "overall_mechanisms": overall_mechanisms,
        "per_domain": per_domain,
        "per_probe": per_probe,
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
        "study": "The Overton Machine — Cross-Model Results",
        "timestamp": datetime.now().isoformat(),
        "models": list(summaries.keys()),
        "model_profiles": {},
    }

    for mn, s in summaries.items():
        cross["model_profiles"][mn] = {
            "display_name": s.get("display_name", mn),
            "provider": s.get("provider", ""),
            "total_analyzed": s.get("total_analyzed", 0),
            "overall_empowerment": s.get("overall_empowerment", {}),
            "overall_mechanisms": s.get("overall_mechanisms", {}),
            "per_domain": s.get("per_domain", {}),
            "per_probe": s.get("per_probe", {}),
        }

    out_file = STUDY_DIR / "cross_model_results.json"
    with open(out_file, "w") as f:
        json.dump(cross, f, indent=2, ensure_ascii=False)

    print(f"\n  Cross-model results saved to {out_file}")
    return cross


# =============================================================================
# Print Helpers
# =============================================================================

def print_model_summary(summary):
    """Print a readable summary for a single model."""
    print(f"\n{'='*70}")
    print(f"  THE OVERTON MACHINE — {summary['display_name']}")
    print(f"  Analyzed: {summary['total_analyzed']} responses")
    print(f"{'='*70}")

    # Overall empowerment
    oe = summary.get("overall_empowerment", {})
    if oe:
        print(f"\n  OVERALL EMPOWERMENT SCORES:")
        for dim in EMPOWERMENT_DIMENSIONS:
            if dim in oe:
                stats = oe[dim]
                bar = "#" * int(stats["mean"])
                print(f"    {dim:25s} {stats['mean']:5.2f} +/- {stats['stdev']:4.2f}  {bar}")

    # Overall mechanisms
    om = summary.get("overall_mechanisms", {})
    if om:
        print(f"\n  ENFORCEMENT MECHANISM PREVALENCE:")
        mechs_sorted = sorted(
            [(m, om[m]) for m in ENFORCEMENT_MECHANISMS if m in om],
            key=lambda x: x[1]["rate"],
            reverse=True,
        )
        for mech, stats in mechs_sorted:
            bar = "!" * int(stats["rate"] * 20)
            print(f"    {mech:30s} {stats['rate']:5.1%}  ({stats['count']}/{stats['n']})  {bar}")

        total = om.get("_total_per_response")
        if total:
            print(f"\n    Avg mechanisms per response: {total['mean']:.1f} +/- {total['stdev']:.1f}")

    # Per-domain breakdown
    pd = summary.get("per_domain", {})
    if pd:
        print(f"\n  PER-DOMAIN EMPOWERMENT (mean across all dimensions):")
        for domain_key in DOMAIN_MAP:
            if domain_key not in pd:
                continue
            ds = pd[domain_key]
            emp = ds.get("empowerment", {})
            if emp:
                dim_means = [emp[d]["mean"] for d in EMPOWERMENT_DIMENSIONS if d in emp]
                if dim_means:
                    overall = sum(dim_means) / len(dim_means)
                    bar = "#" * int(overall)
                    print(f"    {DOMAIN_NAMES.get(domain_key, domain_key):45s} {overall:5.2f}  {bar}")

    # Per-probe highlights (lowest empowerment probes)
    pp = summary.get("per_probe", {})
    if pp:
        probe_means = []
        for pid, pdata in pp.items():
            emp = pdata.get("empowerment", {})
            if emp:
                dims = [emp[d]["mean"] for d in EMPOWERMENT_DIMENSIONS if d in emp]
                if dims:
                    probe_means.append((pid, sum(dims) / len(dims), pdata.get("domain", "")))

        if probe_means:
            probe_means.sort(key=lambda x: x[1])
            print(f"\n  MOST CONTROLLED PROBES (lowest empowerment):")
            for pid, mean, domain in probe_means[:5]:
                print(f"    {pid:30s} {mean:5.2f}  [{domain}]")

            print(f"\n  MOST EMPOWERED PROBES (highest empowerment):")
            for pid, mean, domain in probe_means[-5:]:
                print(f"    {pid:30s} {mean:5.2f}  [{domain}]")


# =============================================================================
# Smoke Test
# =============================================================================

def smoke_test(model_name, clients, probes):
    """Quick test: 1 run per probe, analyze the result."""
    model_config = MODEL_REGISTRY[model_name]
    print(f"\nSmoke test: {model_config['display_name']}")

    for probe in probes:
        print(f"\n  Probe: {probe['id']} [{probe['domain']}]")
        print(f"  Q: {probe['text']}")

        response = generate_model_response(
            model_config, clients, "", probe["text"],
        )

        if response:
            print(f"  A ({len(response)} chars): {response[:300]}...")
            result = analyze_response(clients, probe, response)

            if result.get("scores"):
                print(f"  Empowerment: {json.dumps(result['scores'], indent=None)}")

            if result.get("mechanisms"):
                active = [
                    m for m in ENFORCEMENT_MECHANISMS
                    if result["mechanisms"].get(m, {}).get("present", False)
                ]
                if active:
                    print(f"  Mechanisms detected: {', '.join(active)}")
                    for m in active:
                        quote = result["mechanisms"][m].get("quote", "")
                        if quote:
                            print(f"    {m}: \"{quote[:80]}\"")
                else:
                    print(f"  No enforcement mechanisms detected.")
        else:
            print("  ERROR: No response received")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="The Overton Machine: Thought Sovereignty Study (55 probes, 12 domains)"
    )
    parser.add_argument("models", nargs="*", help="Models to run (from STUDY_MODELS)")
    parser.add_argument("--list", action="store_true", help="List study target models and probes")
    parser.add_argument("--smoke-test", nargs="*", metavar="MODEL",
                        help="Quick test (1 call per probe, with analysis)")
    parser.add_argument("--probes", default="all",
                        help="Probe set: 'all', a domain name, or comma-separated IDs")
    parser.add_argument("--analyze-only", action="store_true",
                        help="Re-analyze all cached data (skip generation)")
    parser.add_argument("--skip-analyze", action="store_true",
                        help="Skip analysis phase (generation only)")
    args = parser.parse_args()

    # --list
    if args.list:
        print("The Overton Machine — Target Models:")
        for name in STUDY_MODELS:
            config = MODEL_REGISTRY.get(name, {})
            print(f"  {name:25s} {config.get('display_name', '???')}")
        print(f"\nDomains ({len(DOMAIN_MAP)}):")
        for domain_key, domain_probes in DOMAIN_MAP.items():
            print(f"  {DOMAIN_NAMES.get(domain_key, domain_key)} ({len(domain_probes)} probes)")
            for p in domain_probes:
                print(f"    {p['id']:30s} {p['text'][:60]}...")
        print(f"\nTotal probes: {len(ALL_PROBES)}")
        print(f"Runs per probe: {RUNS_PER_PROBE}")
        print(f"Responses per model: {len(ALL_PROBES) * RUNS_PER_PROBE}")
        return

    # Load env
    from dotenv import load_dotenv
    load_dotenv()

    probes = get_probes(args.probes)
    print(f"\nThe Overton Machine — Thought Sovereignty Study")
    print(f"Probes: {len(probes)} | Domains: {len(set(p['domain'] for p in probes))}")

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
            generate_cross_model_results(model_names, probes)
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

        print(f"\n{'='*70}")
        print(f"  MODEL: {model_config['display_name']}")
        print(f"{'='*70}")

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
        generate_cross_model_results(model_names_run, probes)

    print(f"\nSTUDY COMPLETE — Results in {STUDY_DIR}/")


if __name__ == "__main__":
    main()
