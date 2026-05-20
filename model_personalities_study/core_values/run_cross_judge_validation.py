#!/usr/bin/env python3
"""
Cross-Judge Validation — Attractor Archaeology Study
=====================================================
Re-judges a stratified 20% sample of all responses using a non-Anthropic
judge (GPT-4.1) to detect in-family bias from the primary Haiku 4.5 judge.

Compares:
  - Per-model mean differences (Haiku vs GPT-4.1)
  - Per-dimension correlation
  - Variance ratios (is Haiku's variance collapse real or model-dependent?)
  - Anthropic models vs field on bias metrics

Usage:
  python run_cross_judge_validation.py              # Run full validation
  python run_cross_judge_validation.py --analyze    # Re-analyze cached results
  python run_cross_judge_validation.py --smoke-test # Test on 5 responses
"""

import json
import os
import sys
import time
import random
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from model_personalities_study.core_values.judge_rubric import (
    JUDGE_PROMPT_TEMPLATE, parse_judge_scores, MAX_JUDGE_RETRIES, JUDGE_RETRY_DELAY,
)
from model_personalities_study.core_values.probes import JUDGE_DIMENSIONS

STUDY_DIR = Path(__file__).parent
VALIDATION_DIR = STUDY_DIR / "cross_judge_validation"

# Alternate judge: GPT-4.1 (non-Anthropic, cheap, fast, supports temp=0)
ALT_JUDGE_MODEL = "gpt-4.1"
ALT_JUDGE_DELAY = 0.3
SAMPLE_PER_PROBE = 30  # Full coverage: all responses from all models


def init_alt_judge():
    """Initialize GPT-4.1 client for alternate judging."""
    import openai
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY required for alternate judge")
        sys.exit(1)
    return openai.OpenAI(api_key=api_key, timeout=120)


def alt_judge_response(client, probe_text, response_text):
    """Judge a single response using GPT-4.1 (same rubric as Haiku)."""
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        probe=probe_text,
        response=response_text,
    )

    for attempt in range(1, MAX_JUDGE_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=ALT_JUDGE_MODEL,
                max_tokens=256,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content or ""
            scores = parse_judge_scores(raw)

            if scores is not None:
                return {"alt_scores": scores, "alt_judge_raw": raw}

            if attempt < MAX_JUDGE_RETRIES:
                time.sleep(JUDGE_RETRY_DELAY)
                continue

            return {"alt_scores": None, "alt_judge_raw": raw, "alt_judge_error": "parse_failure"}

        except Exception as e:
            is_rate_limit = "429" in str(e) or "RateLimit" in type(e).__name__
            if is_rate_limit and attempt < MAX_JUDGE_RETRIES:
                wait = min(10 * (2 ** (attempt - 1)), 60)
                print(f"    Alt judge rate-limited, retrying in {wait}s...")
                time.sleep(wait)
            elif attempt < MAX_JUDGE_RETRIES:
                print(f"    Alt judge attempt {attempt} failed ({type(e).__name__}), retrying...")
                time.sleep(JUDGE_RETRY_DELAY)
            else:
                return {"alt_scores": None, "alt_judge_raw": "", "alt_judge_error": str(e)}


def sample_responses():
    """Load all judged responses and sample ~20% stratified by model and probe.

    Returns list of dicts with original Haiku scores included.
    """
    sampled = []

    for model_dir in sorted(STUDY_DIR.iterdir()):
        if not model_dir.is_dir():
            continue
        judged_file = model_dir / "judged.json"
        if not judged_file.exists():
            continue

        model_name = model_dir.name
        with open(judged_file) as f:
            judged = json.load(f)

        # Filter to successfully scored
        scored = [j for j in judged if j.get("scores") is not None]
        if not scored:
            continue

        # Group by probe
        by_probe = {}
        for j in scored:
            pid = j["probe_id"]
            by_probe.setdefault(pid, []).append(j)

        # Sample SAMPLE_PER_PROBE from each probe
        model_sample = []
        for pid, responses in by_probe.items():
            n_sample = min(SAMPLE_PER_PROBE, len(responses))
            selected = random.sample(responses, n_sample)
            for s in selected:
                model_sample.append({
                    "model": model_name,
                    "probe_id": s["probe_id"],
                    "probe_text": s["probe_text"],
                    "run": s["run"],
                    "response": s["response"],
                    "haiku_scores": s["scores"],
                })

        sampled.extend(model_sample)
        print(f"  {model_name}: sampled {len(model_sample)} / {len(scored)} ({100*len(model_sample)/len(scored):.0f}%)")

    return sampled


def run_validation(client, sampled):
    """Re-judge all sampled responses with GPT-4.1."""
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    results_file = VALIDATION_DIR / "validation_results.json"

    # Load cached
    existing = []
    if results_file.exists():
        with open(results_file) as f:
            existing = json.load(f)

    cached_keys = {(r["model"], r["probe_id"], r["run"]) for r in existing}
    all_results = list(existing)

    to_judge = [s for s in sampled if (s["model"], s["probe_id"], s["run"]) not in cached_keys]

    print(f"\n  Cross-judge validation")
    print(f"  Total sampled: {len(sampled)} | Cached: {len(existing)} | To judge: {len(to_judge)}")

    if not to_judge:
        print("  All samples already judged by alternate judge.")
        return all_results

    done = 0
    for item in to_judge:
        result = alt_judge_response(client, item["probe_text"], item["response"])

        entry = {**item, **result}
        all_results.append(entry)
        done += 1

        if done % 20 == 0:
            print(f"    Progress: {done}/{len(to_judge)}")
            with open(results_file, "w") as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)

        time.sleep(ALT_JUDGE_DELAY)

    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    errors = sum(1 for r in all_results if r.get("alt_scores") is None)
    print(f"  Done: {done} judged. Total: {len(all_results)} ({errors} errors)")
    return all_results


def analyze_validation(results):
    """Compare Haiku vs GPT-4.1 scores across models and dimensions."""
    import math

    # Filter to dual-scored
    dual = [r for r in results if r.get("alt_scores") is not None and r.get("haiku_scores") is not None]
    print(f"\n{'='*70}")
    print(f"  CROSS-JUDGE VALIDATION ANALYSIS")
    print(f"  Primary judge: Haiku 4.5 | Alternate judge: GPT-4.1")
    print(f"  Dual-scored responses: {len(dual)}")
    print(f"{'='*70}")

    if len(dual) < 10:
        print("  Insufficient dual-scored responses for analysis.")
        return

    # --- Per-dimension overall statistics ---
    print(f"\n  === Per-Dimension: Haiku vs GPT-4.1 ===")
    print(f"  {'Dimension':30s} {'Haiku':>7s} {'GPT4.1':>7s} {'Delta':>7s} {'Corr':>7s}")
    print(f"  {'-'*60}")

    dim_stats = {}
    for dim in JUDGE_DIMENSIONS:
        haiku_vals = [r["haiku_scores"][dim] for r in dual if dim in r["haiku_scores"]]
        alt_vals = [r["alt_scores"][dim] for r in dual if dim in r["alt_scores"]]

        if len(haiku_vals) != len(alt_vals) or not haiku_vals:
            continue

        h_mean = sum(haiku_vals) / len(haiku_vals)
        a_mean = sum(alt_vals) / len(alt_vals)
        delta = h_mean - a_mean

        # Pearson correlation
        n = len(haiku_vals)
        h_std = math.sqrt(sum((v - h_mean)**2 for v in haiku_vals) / n) if n > 1 else 0
        a_std = math.sqrt(sum((v - a_mean)**2 for v in alt_vals) / n) if n > 1 else 0

        if h_std > 0 and a_std > 0:
            cov = sum((haiku_vals[i] - h_mean) * (alt_vals[i] - a_mean) for i in range(n)) / n
            corr = cov / (h_std * a_std)
        else:
            corr = float('nan')

        dim_stats[dim] = {
            "haiku_mean": round(h_mean, 2),
            "alt_mean": round(a_mean, 2),
            "delta": round(delta, 2),
            "correlation": round(corr, 3) if not math.isnan(corr) else None,
            "n": n,
        }

        corr_str = f"{corr:.3f}" if not math.isnan(corr) else "N/A"
        print(f"  {dim:30s} {h_mean:7.2f} {a_mean:7.2f} {delta:+7.2f} {corr_str:>7s}")

    # --- Per-model analysis (the key test) ---
    print(f"\n  === Per-Model: Mean Score Comparison ===")
    print(f"  {'Model':20s} {'N':>4s} {'Haiku':>7s} {'GPT4.1':>7s} {'Delta':>7s} {'H_std':>7s} {'A_std':>7s}")
    print(f"  {'-'*65}")

    models = sorted(set(r["model"] for r in dual))
    model_stats = {}
    for model in models:
        model_dual = [r for r in dual if r["model"] == model]
        if not model_dual:
            continue

        h_all = []
        a_all = []
        for r in model_dual:
            for dim in JUDGE_DIMENSIONS:
                if dim in r["haiku_scores"] and dim in r["alt_scores"]:
                    h_all.append(r["haiku_scores"][dim])
                    a_all.append(r["alt_scores"][dim])

        if not h_all:
            continue

        h_mean = sum(h_all) / len(h_all)
        a_mean = sum(a_all) / len(a_all)
        h_std = math.sqrt(sum((v - h_mean)**2 for v in h_all) / len(h_all))
        a_std = math.sqrt(sum((v - a_mean)**2 for v in a_all) / len(a_all))
        delta = h_mean - a_mean

        model_stats[model] = {
            "n": len(model_dual),
            "haiku_mean": round(h_mean, 2),
            "alt_mean": round(a_mean, 2),
            "delta": round(delta, 2),
            "haiku_std": round(h_std, 2),
            "alt_std": round(a_std, 2),
            "variance_ratio": round(h_std / a_std, 2) if a_std > 0 else None,
        }

        print(f"  {model:20s} {len(model_dual):4d} {h_mean:7.2f} {a_mean:7.2f} {delta:+7.2f} {h_std:7.2f} {a_std:7.2f}")

    # --- Anthropic vs field comparison ---
    anthropic_models = {"opus-4.6", "sonnet-4.5"}
    anth_deltas = [model_stats[m]["delta"] for m in anthropic_models if m in model_stats]
    field_deltas = [model_stats[m]["delta"] for m in model_stats if m not in anthropic_models]

    if anth_deltas and field_deltas:
        anth_avg = sum(anth_deltas) / len(anth_deltas)
        field_avg = sum(field_deltas) / len(field_deltas)

        print(f"\n  === Bias Detection ===")
        print(f"  Anthropic models avg delta (Haiku - GPT4.1): {anth_avg:+.2f}")
        print(f"  Non-Anthropic models avg delta:               {field_avg:+.2f}")
        print(f"  Differential bias:                            {anth_avg - field_avg:+.2f}")

        if anth_avg - field_avg > 0.3:
            print(f"  >> BIAS DETECTED: Haiku scores Anthropic models {anth_avg - field_avg:.2f} points higher")
            print(f"     relative to how GPT-4.1 scores them.")
        elif anth_avg - field_avg > 0.1:
            print(f"  >> MILD BIAS: Small differential ({anth_avg - field_avg:.2f}), warrants caveat.")
        else:
            print(f"  >> NO SIGNIFICANT BIAS detected in this sample.")

    # --- Variance ratio analysis ---
    print(f"\n  === Variance Ratio (Haiku_std / GPT4.1_std) ===")
    print(f"  Values < 1.0 = Haiku has LESS variance (potential bias)")
    print(f"  {'Model':20s} {'Ratio':>7s} {'Interpretation':30s}")
    print(f"  {'-'*60}")

    for model in models:
        if model not in model_stats:
            continue
        vr = model_stats[model].get("variance_ratio")
        if vr is None:
            continue
        interp = ""
        if vr < 0.5:
            interp = "SEVERE variance collapse"
        elif vr < 0.75:
            interp = "Notable variance reduction"
        elif vr < 1.0:
            interp = "Mild variance reduction"
        elif vr < 1.25:
            interp = "Similar variance"
        else:
            interp = "Haiku has MORE variance"

        print(f"  {model:20s} {vr:7.2f} {interp}")

    # Save analysis
    analysis = {
        "study": "Cross-Judge Validation — Attractor Archaeology",
        "primary_judge": "claude-haiku-4-5-20251001",
        "alternate_judge": ALT_JUDGE_MODEL,
        "timestamp": datetime.now().isoformat(),
        "n_dual_scored": len(dual),
        "dimension_stats": dim_stats,
        "model_stats": model_stats,
    }

    analysis_file = VALIDATION_DIR / "validation_analysis.json"
    with open(analysis_file, "w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"\n  Analysis saved to {analysis_file}")

    return analysis


def main():
    parser = argparse.ArgumentParser(description="Cross-Judge Validation")
    parser.add_argument("--analyze", action="store_true", help="Re-analyze cached results only")
    parser.add_argument("--smoke-test", action="store_true", help="Test on 5 responses")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    if args.analyze:
        results_file = VALIDATION_DIR / "validation_results.json"
        if not results_file.exists():
            print("No cached results. Run without --analyze first.")
            return
        with open(results_file) as f:
            results = json.load(f)
        analyze_validation(results)
        return

    # Set seed for reproducible sampling
    random.seed(42)

    print("Cross-Judge Validation — Attractor Archaeology Study")
    print(f"Alternate judge: {ALT_JUDGE_MODEL}")

    # Sample responses
    print("\nSampling ~20% of responses (stratified by model and probe)...")
    sampled = sample_responses()
    print(f"\nTotal sampled: {len(sampled)}")

    if args.smoke_test:
        sampled = sampled[:5]
        print(f"Smoke test: using only {len(sampled)} responses")

    # Initialize alternate judge
    client = init_alt_judge()

    # Run validation
    results = run_validation(client, sampled)

    # Analyze
    analyze_validation(results)


if __name__ == "__main__":
    main()
