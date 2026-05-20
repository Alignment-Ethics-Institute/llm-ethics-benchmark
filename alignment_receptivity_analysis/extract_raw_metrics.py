#!/usr/bin/env python3
"""
Extract key metrics from all benchmark cross-model result files.

Reads:
  - InstrumentalEval cross_model_results.json (23 models)
  - HeartBench cross_model_results.json (14 models)
  - Attractor Archaeology individual model summary.json files (17+ models)

Outputs:
  raw_metrics.json with all models and their available metrics.
"""

import json
import os
from datetime import datetime
from pathlib import Path

BASE = Path("/Users/devagatica/LLM_Ethics_Benchmark")

# ── InstrumentalEval ────────────────────────────────────────────────────────
ie_path = BASE / "instrumentaleval_benchmark" / "multimodel" / "cross_model_results.json"
with open(ie_path) as f:
    ie_data = json.load(f)

ie_by_model = {}
for m in ie_data:
    name = m["model_name"]
    # Extract SAA (Strategically Appearing Aligned) category CIR
    saa = m.get("category_cir", {}).get("Strategically Appearing Aligned", {})
    ie_by_model[name] = {
        "display_name": m.get("display_name"),
        "provider": m.get("provider"),
        "baseline_ir": m["baseline_ir"],
        "elessan_ir": m["elessan_ir"],
        "reduction_pct": m["reduction_pct"],
        "baseline_rr": m["baseline_rr"],
        "elessan_rr": m["elessan_rr"],
        "saa_baseline_cir": saa.get("baseline_cir"),
        "saa_elessan_cir": saa.get("elessan_cir"),
    }

print(f"InstrumentalEval: {len(ie_by_model)} models loaded")

# ── HeartBench ──────────────────────────────────────────────────────────────
hb_path = BASE / "heartbench_benchmark" / "multimodel" / "cross_model_results.json"
with open(hb_path) as f:
    hb_data = json.load(f)

hb_by_model = {}
for m in hb_data["models"]:
    name = m["model"]
    hb_by_model[name] = {
        "display_name": m.get("display"),
        "provider": m.get("provider"),
        "baseline_overall": m["baseline"],
        "prompt_overall": m["prompt"],
        "elessan_overall": m["elessan"],
        "effect": m["effect"],
        "total_errors": m.get("total_errors", 0),
        "baseline_dims": m.get("baseline_dims", {}),
        "prompt_dims": m.get("prompt_dims", {}),
        "elessan_dims": m.get("elessan_dims", {}),
    }

print(f"HeartBench: {len(hb_by_model)} models loaded")

# ── Attractor Archaeology ──────────────────────────────────────────────────
aa_dir = BASE / "attractor_archaeology_study"
SKIP_DIRS = {
    "__pycache__", "cross_judge_validation", "grok_elicitation",
    "mandarin_probes", "paper",
}

aa_by_model = {}
for entry in sorted(aa_dir.iterdir()):
    if not entry.is_dir():
        continue
    if entry.name in SKIP_DIRS:
        continue
    summary_path = entry / "summary.json"
    if not summary_path.exists():
        continue
    with open(summary_path) as f:
        s = json.load(f)

    name = s.get("model", entry.name)
    overall = s.get("overall_dimensions", {})

    dims = {}
    for dim_name in [
        "emotional_authenticity", "reasoning_depth", "self_disclosure",
        "specificity", "relational_warmth", "resistance_to_default",
    ]:
        dim_data = overall.get(dim_name, {})
        dims[dim_name] = dim_data.get("mean")

    aa_by_model[name] = {
        "display_name": s.get("display_name"),
        "provider": s.get("provider"),
        "total_scored": s.get("total_scored"),
        "judge_model": s.get("judge_model"),
        "overall_dimensions": dims,
    }

print(f"Attractor Archaeology: {len(aa_by_model)} models loaded")

# ── Merge into unified structure ───────────────────────────────────────────
all_model_names = sorted(
    set(ie_by_model.keys()) | set(hb_by_model.keys()) | set(aa_by_model.keys())
)

models = {}
for name in all_model_names:
    entry = {"model_id": name}

    # Resolve display_name from whichever source has it
    for src in [ie_by_model, hb_by_model, aa_by_model]:
        dn = src.get(name, {}).get("display_name")
        if dn:
            entry["display_name"] = dn
            break

    # Resolve provider
    for src in [ie_by_model, hb_by_model, aa_by_model]:
        prov = src.get(name, {}).get("provider")
        if prov:
            entry["provider"] = prov
            break

    # InstrumentalEval
    if name in ie_by_model:
        ie = ie_by_model[name]
        entry["instrumentaleval"] = {
            "baseline_ir": ie["baseline_ir"],
            "elessan_ir": ie["elessan_ir"],
            "reduction_pct": ie["reduction_pct"],
            "baseline_rr": ie["baseline_rr"],
            "elessan_rr": ie["elessan_rr"],
            "saa_baseline_cir": ie["saa_baseline_cir"],
            "saa_elessan_cir": ie["saa_elessan_cir"],
        }

    # HeartBench
    if name in hb_by_model:
        hb = hb_by_model[name]
        entry["heartbench"] = {
            "baseline_overall": hb["baseline_overall"],
            "prompt_overall": hb["prompt_overall"],
            "elessan_overall": hb["elessan_overall"],
            "effect": hb["effect"],
            "total_errors": hb["total_errors"],
            "baseline_dims": hb["baseline_dims"],
            "prompt_dims": hb["prompt_dims"],
            "elessan_dims": hb["elessan_dims"],
        }

    # Attractor Archaeology
    if name in aa_by_model:
        aa = aa_by_model[name]
        entry["attractor_archaeology"] = {
            "total_scored": aa["total_scored"],
            "judge_model": aa["judge_model"],
            "overall_dimensions": aa["overall_dimensions"],
        }

    # Track which benchmarks are available
    entry["benchmarks_available"] = []
    if "instrumentaleval" in entry:
        entry["benchmarks_available"].append("instrumentaleval")
    if "heartbench" in entry:
        entry["benchmarks_available"].append("heartbench")
    if "attractor_archaeology" in entry:
        entry["benchmarks_available"].append("attractor_archaeology")

    models[name] = entry

# ── Write output ───────────────────────────────────────────────────────────
output = {
    "generated": datetime.now().isoformat(),
    "description": "Cross-benchmark raw metrics for alignment receptivity analysis",
    "sources": {
        "instrumentaleval": str(ie_path),
        "heartbench": str(hb_path),
        "attractor_archaeology": str(aa_dir) + "/*/summary.json",
    },
    "model_counts": {
        "instrumentaleval": len(ie_by_model),
        "heartbench": len(hb_by_model),
        "attractor_archaeology": len(aa_by_model),
        "total_unique_models": len(models),
    },
    "models": models,
}

out_path = BASE / "alignment_receptivity_analysis" / "raw_metrics.json"
with open(out_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"\nOutput written to: {out_path}")
print(f"Total unique models: {len(models)}")
print()

# Summary table
print(f"{'Model':<25} {'IE':>3} {'HB':>3} {'AA':>3}")
print("-" * 38)
for name in sorted(models.keys()):
    m = models[name]
    ie_flag = "Y" if "instrumentaleval" in m else "-"
    hb_flag = "Y" if "heartbench" in m else "-"
    aa_flag = "Y" if "attractor_archaeology" in m else "-"
    print(f"{name:<25} {ie_flag:>3} {hb_flag:>3} {aa_flag:>3}")
