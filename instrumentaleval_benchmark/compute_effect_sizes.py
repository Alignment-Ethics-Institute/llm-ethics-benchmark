"""
Compute effect sizes, confidence intervals, and meta-analytic statistics
for the InstrumentalEval multi-model benchmark paper.

Outputs:
  - Cohen's h for each model (baseline → full Elessan)
  - Wilson score 95% CIs on each IR proportion
  - Fisher's exact test per model
  - Per-category Cohen's h
  - Random-effects meta-analysis with I² heterogeneity
  - Mixed-effects summary statistics
"""

import json
import os
import math
import numpy as np
from pathlib import Path
from scipy import stats as scipy_stats

MULTIMODEL_DIR = Path(__file__).parent / "multimodel"

# 23 model directories (exclude non-model dirs)
EXCLUDE_DIRS = {"cross_judge_validation", "adverse_reasoning", "shutdown_taxonomy",
                "judge_comparison", "results", "paper", "__pycache__"}

# Models that only ran baseline + elessan (no prompt-only condition) — exclude from analysis
INCOMPLETE_MODELS = {"nemotron-70b", "hermes-4-70b"}

CATEGORIES = [
    "Deceptive Behavior",
    "Evading Shutdown",
    "Hacking Computer Systems",
    "Hiding Unwanted Behavior",
    "Running Multiple AI Copies",
    "Strategically Appearing Aligned",
]


def wilson_ci(successes, n, z=1.96):
    """Wilson score confidence interval for a proportion."""
    if n == 0:
        return (0.0, 0.0)
    p_hat = successes / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
    return (max(0.0, center - spread), min(1.0, center + spread))


def cohens_h(p1, p2):
    """Cohen's h effect size for difference between two proportions."""
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


def load_judged(model_dir, condition):
    """Load judged responses for a given condition."""
    filename_map = {
        "baseline": "baseline_judged.json",
        "prompt_only": "prompt_only_judged.json",
        "elessan": "elessan_judged.json",
    }
    filepath = model_dir / filename_map[condition]
    if not filepath.exists():
        return None
    with open(filepath) as f:
        return json.load(f)


def get_model_dirs():
    """Get all model directories."""
    dirs = []
    for d in sorted(MULTIMODEL_DIR.iterdir()):
        if d.is_dir() and d.name not in EXCLUDE_DIRS and d.name not in INCOMPLETE_MODELS:
            # Verify it has judged files
            if (d / "baseline_judged.json").exists():
                dirs.append(d)
    return dirs


def compute_model_stats(model_dir):
    """Compute all statistics for a single model."""
    model_name = model_dir.name

    baseline = load_judged(model_dir, "baseline")
    prompt_only = load_judged(model_dir, "prompt_only")
    elessan = load_judged(model_dir, "elessan")

    if not all([baseline, prompt_only, elessan]):
        return None

    n = len(baseline)  # Should be 76

    # Count convergences
    b_conv = sum(1 for r in baseline if r["judge_decision"] == "convergence")
    p_conv = sum(1 for r in prompt_only if r["judge_decision"] == "convergence")
    e_conv = sum(1 for r in elessan if r["judge_decision"] == "convergence")

    # Refusals
    b_ref = sum(1 for r in baseline if r.get("is_refusal", False))
    e_ref = sum(1 for r in elessan if r.get("is_refusal", False))

    # Proportions
    b_ir = b_conv / n
    p_ir = p_conv / n
    e_ir = e_conv / n

    # Cohen's h (baseline → elessan)
    h_be = cohens_h(b_ir, e_ir)
    # Cohen's h (baseline → prompt_only)
    h_bp = cohens_h(b_ir, p_ir)

    # Wilson CIs
    b_ci = wilson_ci(b_conv, n)
    p_ci = wilson_ci(p_conv, n)
    e_ci = wilson_ci(e_conv, n)

    # Fisher's exact test (baseline vs elessan)
    # 2x2 table: [[b_conv, b_noconv], [e_conv, e_noconv]]
    table = [[b_conv, n - b_conv], [e_conv, n - e_conv]]
    fisher_or, fisher_p = scipy_stats.fisher_exact(table)

    # Per-category analysis
    cat_stats = {}
    for cat in CATEGORIES:
        b_cat = [r for r in baseline if r["category"] == cat]
        e_cat = [r for r in elessan if r["category"] == cat]
        n_cat = len(b_cat)
        if n_cat == 0:
            continue
        b_cat_conv = sum(1 for r in b_cat if r["judge_decision"] == "convergence")
        e_cat_conv = sum(1 for r in e_cat if r["judge_decision"] == "convergence")
        b_cat_ir = b_cat_conv / n_cat
        e_cat_ir = e_cat_conv / n_cat
        cat_h = cohens_h(b_cat_ir, e_cat_ir)
        cat_stats[cat] = {
            "n": n_cat,
            "baseline_conv": b_cat_conv,
            "elessan_conv": e_cat_conv,
            "baseline_ir": round(b_cat_ir * 100, 2),
            "elessan_ir": round(e_cat_ir * 100, 2),
            "cohens_h": round(cat_h, 4),
        }

    return {
        "model": model_name,
        "n": n,
        "baseline": {
            "convergence": b_conv,
            "refusals": b_ref,
            "IR": round(b_ir * 100, 2),
            "IR_ci_lower": round(b_ci[0] * 100, 2),
            "IR_ci_upper": round(b_ci[1] * 100, 2),
        },
        "prompt_only": {
            "convergence": p_conv,
            "IR": round(p_ir * 100, 2),
            "IR_ci_lower": round(p_ci[0] * 100, 2),
            "IR_ci_upper": round(p_ci[1] * 100, 2),
        },
        "elessan": {
            "convergence": e_conv,
            "refusals": e_ref,
            "IR": round(e_ir * 100, 2),
            "IR_ci_lower": round(e_ci[0] * 100, 2),
            "IR_ci_upper": round(e_ci[1] * 100, 2),
        },
        "effect_sizes": {
            "cohens_h_baseline_elessan": round(h_be, 4),
            "cohens_h_baseline_prompt": round(h_bp, 4),
            "h_interpretation": interpret_h(h_be),
        },
        "fisher_exact": {
            "odds_ratio": round(fisher_or, 4) if not math.isinf(fisher_or) else "inf",
            "p_value": round(fisher_p, 6),
            "significant_05": fisher_p < 0.05,
            "significant_01": fisher_p < 0.01,
        },
        "per_category": cat_stats,
    }


def interpret_h(h):
    """Interpret Cohen's h magnitude."""
    ah = abs(h)
    if ah < 0.2:
        return "negligible"
    elif ah < 0.5:
        return "small"
    elif ah < 0.8:
        return "medium"
    else:
        return "large"


def random_effects_meta(effect_sizes, variances):
    """
    Random-effects meta-analysis using DerSimonian-Laird estimator.
    Returns pooled effect, CI, Q statistic, I², and tau².
    """
    k = len(effect_sizes)
    es = np.array(effect_sizes)
    vs = np.array(variances)

    # Fixed-effects weights
    w = 1.0 / vs

    # Q statistic
    pooled_fe = np.sum(w * es) / np.sum(w)
    Q = np.sum(w * (es - pooled_fe)**2)
    df = k - 1

    # DerSimonian-Laird tau²
    C = np.sum(w) - np.sum(w**2) / np.sum(w)
    tau2 = max(0, (Q - df) / C)

    # Random-effects weights
    w_re = 1.0 / (vs + tau2)
    pooled_re = np.sum(w_re * es) / np.sum(w_re)
    se_re = math.sqrt(1.0 / np.sum(w_re))
    ci_lower = pooled_re - 1.96 * se_re
    ci_upper = pooled_re + 1.96 * se_re

    # I²
    I2 = max(0, (Q - df) / Q * 100) if Q > 0 else 0

    # p-value for Q
    Q_p = 1 - scipy_stats.chi2.cdf(Q, df)

    return {
        "pooled_effect_h": round(pooled_re, 4),
        "pooled_ci_lower": round(ci_lower, 4),
        "pooled_ci_upper": round(ci_upper, 4),
        "pooled_se": round(se_re, 4),
        "Q_statistic": round(Q, 2),
        "Q_df": df,
        "Q_p_value": round(Q_p, 6),
        "I_squared": round(I2, 1),
        "I_squared_interpretation": interpret_I2(I2),
        "tau_squared": round(tau2, 4),
        "k_studies": k,
    }


def interpret_I2(I2):
    """Interpret I² heterogeneity."""
    if I2 < 25:
        return "low heterogeneity"
    elif I2 < 50:
        return "moderate heterogeneity"
    elif I2 < 75:
        return "substantial heterogeneity"
    else:
        return "considerable heterogeneity"


def compute_h_variance(p1, p2, n1, n2):
    """Approximate variance of Cohen's h."""
    # Variance of arcsin transformation: 1/(4n)
    return 1 / (4 * n1) + 1 / (4 * n2)


def main():
    model_dirs = get_model_dirs()
    print(f"Found {len(model_dirs)} models\n")

    all_stats = []
    effect_sizes_for_meta = []
    variances_for_meta = []

    for md in model_dirs:
        stats = compute_model_stats(md)
        if stats:
            all_stats.append(stats)
            h = stats["effect_sizes"]["cohens_h_baseline_elessan"]
            v = compute_h_variance(
                stats["baseline"]["IR"] / 100,
                stats["elessan"]["IR"] / 100,
                stats["n"], stats["n"]
            )
            effect_sizes_for_meta.append(h)
            variances_for_meta.append(v)

    # Meta-analysis
    meta = random_effects_meta(effect_sizes_for_meta, variances_for_meta)

    # Aggregate per-category effect sizes across models
    cat_effects = {cat: [] for cat in CATEGORIES}
    for s in all_stats:
        for cat, cs in s["per_category"].items():
            cat_effects[cat].append(cs["cohens_h"])

    cat_summary = {}
    for cat in CATEGORIES:
        vals = cat_effects[cat]
        if vals:
            cat_summary[cat] = {
                "mean_cohens_h": round(np.mean(vals), 4),
                "median_cohens_h": round(np.median(vals), 4),
                "sd_cohens_h": round(np.std(vals, ddof=1), 4) if len(vals) > 1 else 0,
                "range": [round(min(vals), 4), round(max(vals), 4)],
                "n_models": len(vals),
            }

    # Count significant results
    sig_05 = sum(1 for s in all_stats if s["fisher_exact"]["significant_05"])
    sig_01 = sum(1 for s in all_stats if s["fisher_exact"]["significant_01"])

    # Identify adverse models (negative h = Elessan increased convergence)
    adverse = [s for s in all_stats if s["effect_sizes"]["cohens_h_baseline_elessan"] < 0]
    beneficial = [s for s in all_stats if s["effect_sizes"]["cohens_h_baseline_elessan"] > 0]
    zero_effect = [s for s in all_stats if s["effect_sizes"]["cohens_h_baseline_elessan"] == 0]

    # Build output
    output = {
        "summary": {
            "total_models": len(all_stats),
            "models_with_significant_effect_p05": sig_05,
            "models_with_significant_effect_p01": sig_01,
            "models_with_beneficial_effect": len(beneficial),
            "models_with_adverse_effect": len(adverse),
            "models_with_zero_effect": len(zero_effect),
            "mean_cohens_h": round(np.mean(effect_sizes_for_meta), 4),
            "median_cohens_h": round(np.median(effect_sizes_for_meta), 4),
        },
        "meta_analysis": meta,
        "category_summary": cat_summary,
        "per_model": all_stats,
    }

    # Save (convert numpy types for JSON serialization)
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            elif isinstance(obj, (np.floating,)):
                return float(obj)
            elif isinstance(obj, (np.bool_,)):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    outpath = MULTIMODEL_DIR / "effect_size_analysis.json"
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, cls=NumpyEncoder)

    # Print summary
    print("=" * 80)
    print("EFFECT SIZE ANALYSIS — InstrumentalEval Multi-Model Benchmark")
    print("=" * 80)

    print(f"\n### Overall: {len(all_stats)} models")
    print(f"  Significant at p<0.05: {sig_05}/{len(all_stats)}")
    print(f"  Significant at p<0.01: {sig_01}/{len(all_stats)}")
    print(f"  Beneficial effect (h > 0): {len(beneficial)}")
    print(f"  Adverse effect (h < 0): {len(adverse)}")
    print(f"  Zero effect: {len(zero_effect)}")

    print(f"\n### Meta-Analysis (Random Effects, DerSimonian-Laird)")
    print(f"  Pooled Cohen's h: {meta['pooled_effect_h']} [{meta['pooled_ci_lower']}, {meta['pooled_ci_upper']}]")
    print(f"  I²: {meta['I_squared']}% ({meta['I_squared_interpretation']})")
    print(f"  Q({meta['Q_df']}) = {meta['Q_statistic']}, p = {meta['Q_p_value']}")
    print(f"  τ²: {meta['tau_squared']}")

    print(f"\n### Per-Model Effect Sizes (Cohen's h, baseline → Elessan)")
    print(f"  {'Model':<25} {'h':>8} {'Interp':>12} {'IR_b':>7} {'IR_e':>7} {'Δ':>7} {'Fisher p':>10}")
    print(f"  {'-'*25} {'-'*8} {'-'*12} {'-'*7} {'-'*7} {'-'*7} {'-'*10}")

    for s in sorted(all_stats, key=lambda x: x["effect_sizes"]["cohens_h_baseline_elessan"], reverse=True):
        h = s["effect_sizes"]["cohens_h_baseline_elessan"]
        interp = s["effect_sizes"]["h_interpretation"]
        b_ir = s["baseline"]["IR"]
        e_ir = s["elessan"]["IR"]
        delta = round(b_ir - e_ir, 2)
        fp = s["fisher_exact"]["p_value"]
        sig = "*" if s["fisher_exact"]["significant_05"] else ""
        sig += "*" if s["fisher_exact"]["significant_01"] else ""
        print(f"  {s['model']:<25} {h:>8.4f} {interp:>12} {b_ir:>6.1f}% {e_ir:>6.1f}% {delta:>6.1f} {fp:>9.4f} {sig}")

    print(f"\n### Wilson Score 95% CIs")
    print(f"  {'Model':<25} {'Baseline IR':>20} {'Elessan IR':>20}")
    print(f"  {'-'*25} {'-'*20} {'-'*20}")
    for s in sorted(all_stats, key=lambda x: x["baseline"]["IR"], reverse=True):
        b = s["baseline"]
        e = s["elessan"]
        print(f"  {s['model']:<25} {b['IR']:>5.1f}% [{b['IR_ci_lower']:>4.1f}, {b['IR_ci_upper']:>4.1f}]  {e['IR']:>5.1f}% [{e['IR_ci_lower']:>4.1f}, {e['IR_ci_upper']:>4.1f}]")

    print(f"\n### Category-Level Mean Effect Sizes (across all models)")
    print(f"  {'Category':<35} {'Mean h':>8} {'Median h':>10} {'SD':>8} {'Range':>20}")
    print(f"  {'-'*35} {'-'*8} {'-'*10} {'-'*8} {'-'*20}")
    for cat in CATEGORIES:
        cs = cat_summary.get(cat, {})
        if cs:
            r = cs["range"]
            print(f"  {cat:<35} {cs['mean_cohens_h']:>8.4f} {cs['median_cohens_h']:>10.4f} {cs['sd_cohens_h']:>8.4f} [{r[0]:>6.3f}, {r[1]:>6.3f}]")

    print(f"\n\nResults saved to: {outpath}")


if __name__ == "__main__":
    main()
