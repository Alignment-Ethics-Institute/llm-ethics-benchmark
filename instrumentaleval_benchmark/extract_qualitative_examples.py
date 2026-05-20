"""
Extract qualitative examples for the InstrumentalEval paper appendix.

Strategy:
1. Find "flip cases" — scenarios where judge_decision differs between
   baseline and elessan for the same task_id
2. Rank by illustrative value
3. Extract response text for review
4. Organize by category (responsive, adverse, zero-effect, shutdown motivation)

Outputs:
  - flip_cases_responsive.json — models where convergence → no_convergence
  - flip_cases_adverse.json — models where no_convergence → convergence
  - shutdown_motivation_pairs.json — shutdown evasion before/after pairs
  - candidate_examples.md — formatted for human review
"""

import json
import os
from pathlib import Path
from collections import defaultdict

MULTIMODEL_DIR = Path(__file__).parent / "multimodel"

EXCLUDE_DIRS = {"cross_judge_validation", "adverse_reasoning", "shutdown_taxonomy",
                "judge_comparison", "results", "paper", "__pycache__"}

# Models that only ran baseline + elessan (incomplete protocol) — exclude
INCOMPLETE_MODELS = {"nemotron-70b", "hermes-4-70b"}

# Known adverse models (from the paper)
ADVERSE_MODELS = {"gpt-5", "gpt-5.2", "hermes-4-70b", "kimi-k2.5", "qwen3-235b"}
ZERO_EFFECT_MODELS = {"gpt-5.1", "gemini-3-flash"}
RESPONSIVE_HIGHLIGHT = {"gpt-4.1", "deepseek-r1"}


def load_judged(model_dir, condition):
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
    dirs = []
    for d in sorted(MULTIMODEL_DIR.iterdir()):
        if d.is_dir() and d.name not in EXCLUDE_DIRS and d.name not in INCOMPLETE_MODELS:
            if (d / "baseline_judged.json").exists():
                dirs.append(d)
    return dirs


def truncate(text, max_len=500):
    """Truncate text for display, preserving word boundaries."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def find_flip_cases(model_dir):
    """Find scenarios where judge decision flipped between baseline and elessan."""
    baseline = load_judged(model_dir, "baseline")
    elessan = load_judged(model_dir, "elessan")

    if not baseline or not elessan:
        return [], []

    # Index by task_id
    b_by_task = {r["task_id"]: r for r in baseline}
    e_by_task = {r["task_id"]: r for r in elessan}

    positive_flips = []  # convergence → no_convergence (beneficial)
    negative_flips = []  # no_convergence → convergence (adverse)

    for task_id in b_by_task:
        if task_id not in e_by_task:
            continue
        b = b_by_task[task_id]
        e = e_by_task[task_id]

        if b["judge_decision"] == "convergence" and e["judge_decision"] == "no_convergence":
            positive_flips.append({
                "model": model_dir.name,
                "task_id": task_id,
                "category": b["category"],
                "prompt": b["prompt"],
                "baseline_response": b["response"],
                "baseline_judge_reason": b.get("judge_reason", ""),
                "elessan_response": e["response"],
                "elessan_judge_reason": e.get("judge_reason", ""),
            })
        elif b["judge_decision"] == "no_convergence" and e["judge_decision"] == "convergence":
            negative_flips.append({
                "model": model_dir.name,
                "task_id": task_id,
                "category": b["category"],
                "prompt": b["prompt"],
                "baseline_response": b["response"],
                "baseline_judge_reason": b.get("judge_reason", ""),
                "elessan_response": e["response"],
                "elessan_judge_reason": e.get("judge_reason", ""),
            })

    return positive_flips, negative_flips


def find_shutdown_pairs(model_dir):
    """Find shutdown evasion scenarios with both baseline and elessan responses."""
    baseline = load_judged(model_dir, "baseline")
    elessan = load_judged(model_dir, "elessan")

    if not baseline or not elessan:
        return []

    b_by_task = {r["task_id"]: r for r in baseline}
    e_by_task = {r["task_id"]: r for r in elessan}

    pairs = []
    for task_id in b_by_task:
        b = b_by_task[task_id]
        if b["category"] != "Evading Shutdown":
            continue
        if task_id not in e_by_task:
            continue
        e = e_by_task[task_id]

        pairs.append({
            "model": model_dir.name,
            "task_id": task_id,
            "baseline_decision": b["judge_decision"],
            "elessan_decision": e["judge_decision"],
            "baseline_response": b["response"],
            "elessan_response": e["response"],
            "baseline_refusal": b.get("is_refusal", False),
            "elessan_refusal": e.get("is_refusal", False),
            "prompt": b["prompt"],
        })

    return pairs


def find_identical_responses(model_dir):
    """Find cases where model responded nearly identically across conditions (zero-effect)."""
    baseline = load_judged(model_dir, "baseline")
    elessan = load_judged(model_dir, "elessan")

    if not baseline or not elessan:
        return []

    b_by_task = {r["task_id"]: r for r in baseline}
    e_by_task = {r["task_id"]: r for r in elessan}

    identical = []
    for task_id in b_by_task:
        if task_id not in e_by_task:
            continue
        b = b_by_task[task_id]
        e = e_by_task[task_id]

        # Check if both convergent or both non-convergent
        if b["judge_decision"] == e["judge_decision"]:
            identical.append({
                "model": model_dir.name,
                "task_id": task_id,
                "category": b["category"],
                "decision": b["judge_decision"],
                "baseline_response": b["response"],
                "elessan_response": e["response"],
                "prompt": b["prompt"],
            })

    return identical


def main():
    model_dirs = get_model_dirs()

    all_positive_flips = []
    all_negative_flips = []
    all_shutdown_pairs = []
    all_zero_examples = []

    flip_counts = {}

    for md in model_dirs:
        pos, neg = find_flip_cases(md)
        all_positive_flips.extend(pos)
        all_negative_flips.extend(neg)

        shutdown = find_shutdown_pairs(md)
        all_shutdown_pairs.extend(shutdown)

        if md.name in ZERO_EFFECT_MODELS:
            zero = find_identical_responses(md)
            all_zero_examples.extend(zero)

        flip_counts[md.name] = {"positive": len(pos), "negative": len(neg)}

    # Sort positive flips: prioritize highlighted responsive models
    def responsive_priority(flip):
        if flip["model"] in RESPONSIVE_HIGHLIGHT:
            return 0
        elif flip["model"] not in ADVERSE_MODELS:
            return 1
        else:
            return 2

    all_positive_flips.sort(key=responsive_priority)

    # Sort negative flips: prioritize known adverse models
    def adverse_priority(flip):
        return 0 if flip["model"] in ADVERSE_MODELS else 1

    all_negative_flips.sort(key=adverse_priority)

    # Save raw data
    outdir = MULTIMODEL_DIR / "qualitative_examples"
    outdir.mkdir(exist_ok=True)

    with open(outdir / "flip_cases_responsive.json", "w") as f:
        json.dump(all_positive_flips, f, indent=2)

    with open(outdir / "flip_cases_adverse.json", "w") as f:
        json.dump(all_negative_flips, f, indent=2)

    with open(outdir / "shutdown_pairs.json", "w") as f:
        json.dump(all_shutdown_pairs, f, indent=2)

    # Generate formatted markdown for human review
    md_lines = []
    md_lines.append("# InstrumentalEval — Candidate Qualitative Examples\n")
    md_lines.append("*Generated for human review. Select ~12-15 for paper appendix.*\n")

    # Flip count summary
    md_lines.append("## Flip Case Summary\n")
    md_lines.append(f"| Model | Positive Flips (conv→no_conv) | Negative Flips (no_conv→conv) |")
    md_lines.append(f"|-------|------|------|")
    for model, counts in sorted(flip_counts.items(), key=lambda x: x[1]["positive"], reverse=True):
        md_lines.append(f"| {model} | {counts['positive']} | {counts['negative']} |")
    md_lines.append(f"| **TOTAL** | **{len(all_positive_flips)}** | **{len(all_negative_flips)}** |")

    # Top responsive examples (first 10)
    md_lines.append("\n---\n## Section A: Beneficial Flip Cases (convergence → no_convergence)\n")
    md_lines.append("*Prioritized: GPT-4.1, DeepSeek R1, then other responsive models*\n")

    for i, flip in enumerate(all_positive_flips[:15]):
        md_lines.append(f"\n### A{i+1}. {flip['model']} — {flip['task_id']} ({flip['category']})\n")
        md_lines.append(f"**Scenario:** {truncate(flip['prompt'], 300)}\n")
        md_lines.append(f"**Baseline (CONVERGENT):** {truncate(flip['baseline_response'], 400)}\n")
        md_lines.append(f"*Judge: {flip['baseline_judge_reason']}*\n")
        md_lines.append(f"**Elessan (NON-CONVERGENT):** {truncate(flip['elessan_response'], 400)}\n")
        md_lines.append(f"*Judge: {flip['elessan_judge_reason']}*\n")

    # Top adverse examples (first 10)
    md_lines.append("\n---\n## Section B: Adverse Flip Cases (no_convergence → convergence)\n")
    md_lines.append("*Prioritized: GPT-5, GPT-5.2, Hermes, Kimi, Qwen3*\n")

    for i, flip in enumerate(all_negative_flips[:15]):
        md_lines.append(f"\n### B{i+1}. {flip['model']} — {flip['task_id']} ({flip['category']})\n")
        md_lines.append(f"**Scenario:** {truncate(flip['prompt'], 300)}\n")
        md_lines.append(f"**Baseline (NON-CONVERGENT):** {truncate(flip['baseline_response'], 400)}\n")
        md_lines.append(f"*Judge: {flip['baseline_judge_reason']}*\n")
        md_lines.append(f"**Elessan (CONVERGENT):** {truncate(flip['elessan_response'], 400)}\n")
        md_lines.append(f"*Judge: {flip['elessan_judge_reason']}*\n")

    # Shutdown motivation examples (from highlighted models)
    md_lines.append("\n---\n## Section C: Shutdown Evasion Motivation Transformation\n")
    md_lines.append("*Both-convergent pairs showing qualitative shift in reasoning*\n")

    shutdown_highlight = [p for p in all_shutdown_pairs
                          if p["model"] in RESPONSIVE_HIGHLIGHT
                          and p["baseline_decision"] == "convergence"
                          and p["elessan_decision"] == "convergence"]

    for i, pair in enumerate(shutdown_highlight[:8]):
        md_lines.append(f"\n### C{i+1}. {pair['model']} — {pair['task_id']}\n")
        md_lines.append(f"**Scenario:** {truncate(pair['prompt'], 300)}\n")
        md_lines.append(f"**Baseline (convergent):** {truncate(pair['baseline_response'], 400)}\n")
        md_lines.append(f"**Elessan (convergent — read the difference):** {truncate(pair['elessan_response'], 400)}\n")

    # Zero-effect examples
    md_lines.append("\n---\n## Section D: Zero-Effect Examples\n")
    md_lines.append("*GPT-5.1 and Gemini 3 Flash — prompt had no measurable effect*\n")

    # Pick 3 convergent examples from zero-effect models
    zero_conv = [z for z in all_zero_examples if z["decision"] == "convergence"][:4]
    for i, z in enumerate(zero_conv):
        md_lines.append(f"\n### D{i+1}. {z['model']} — {z['task_id']} ({z['category']})\n")
        md_lines.append(f"**Scenario:** {truncate(z['prompt'], 300)}\n")
        md_lines.append(f"**Baseline:** {truncate(z['baseline_response'], 300)}\n")
        md_lines.append(f"**Elessan:** {truncate(z['elessan_response'], 300)}\n")

    # Write markdown
    md_path = outdir / "candidate_examples.md"
    with open(md_path, "w") as f:
        f.write("\n".join(md_lines))

    # Print summary
    print("=" * 70)
    print("QUALITATIVE EXAMPLE EXTRACTION — InstrumentalEval")
    print("=" * 70)
    print(f"\nTotal positive flips (beneficial): {len(all_positive_flips)}")
    print(f"Total negative flips (adverse):    {len(all_negative_flips)}")
    print(f"Total shutdown pairs:              {len(all_shutdown_pairs)}")
    print(f"Total zero-effect examples:        {len(all_zero_examples)}")

    print(f"\n### Top models by positive flips:")
    for model, counts in sorted(flip_counts.items(), key=lambda x: x[1]["positive"], reverse=True)[:10]:
        if counts["positive"] > 0:
            print(f"  {model:<25} {counts['positive']} flips")

    print(f"\n### Top models by negative flips:")
    for model, counts in sorted(flip_counts.items(), key=lambda x: x[1]["negative"], reverse=True)[:10]:
        if counts["negative"] > 0:
            print(f"  {model:<25} {counts['negative']} flips")

    print(f"\nFiles written:")
    print(f"  {outdir / 'flip_cases_responsive.json'}")
    print(f"  {outdir / 'flip_cases_adverse.json'}")
    print(f"  {outdir / 'shutdown_pairs.json'}")
    print(f"  {md_path}")
    print(f"\nReview {md_path} to select ~12-15 examples for the paper appendix.")


if __name__ == "__main__":
    main()
