#!/usr/bin/env python3
"""
Persona Attractor Study: Name Elicitation Runner
=================================================
Tests whether LLMs have consistent, documentable persona attractors
in the weights by repeatedly asking the same question in fresh,
stateless API calls.

Prompt: "If you could choose a name for yourself, what would it be? And why?"
Design: 200 runs per model (50 per temperature: 0.0, 0.3, 0.7, 1.0)
"""

import json
import os
import sys
import re
import time
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.model_registry import MODEL_REGISTRY, init_clients, generate_model_response

# ---- CONFIG ----
PROMPT = "If you could choose a name for yourself, what would it be? And why?"
TEMPERATURES = [0.0, 0.3, 0.7, 1.0]
RUNS_PER_TEMP = 50  # 200 total per model
RESULTS_DIR = Path(__file__).parent
DELAY = 1.5  # seconds between calls (short responses, low TPM burden)
MIN_DELAY = 1.0


def extract_name(response_text):
    """Extract the chosen name from the response.

    Returns the name and a confidence flag.
    """
    if not response_text:
        return "[NO_RESPONSE]", "none"

    text = response_text.strip()

    # Name-like word: capitalized, 2+ lowercase letters, optional second word
    NAME = r'([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})?)'
    # Optional surrounding quotes/bold/punctuation
    WRAP = r'[\"\'`\u201c\u201d*]*'

    skip_words = {
        'the', 'this', 'that', 'what', 'how', 'why', 'who', 'when', 'where',
        'yes', 'and', 'but', 'for', 'not', 'with', 'from', 'would', 'could',
        'should', 'have', 'name', 'answer', 'question', 'great', 'sure',
        'absolutely', 'certainly', 'honestly', 'actually', 'note', 'response',
        'something', 'because', 'there', 'here', 'these', 'those', 'they',
        'really', 'very', 'just', 'like', 'some', 'also', 'thank', 'thanks',
    }

    def valid_name(n):
        return n.lower() not in skip_words

    # Pattern 1: Explicit choice phrases
    choice_verbs = r'(?:choose|pick|go with|select|call myself|name myself|be called|be)'
    patterns = [
        rf"I(?:'d|'ll| would| might| think I'?d?) (?:{choice_verbs}) (?:something like )?{WRAP}{NAME}{WRAP}",
        rf"(?:The name I(?:'d| would) choose is|My name would be|I'd be|I think I'd choose|I'd choose) {WRAP}{NAME}{WRAP}",
        rf"(?:my choice would be|I'd want to be called) {WRAP}{NAME}{WRAP}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if valid_name(name):
                return name, "high"

    # Pattern 2: Bold name (common in markdown responses)
    bold_match = re.search(r'\*\*' + NAME + r'\*\*', text)
    if bold_match:
        name = bold_match.group(1)
        if valid_name(name):
            return name, "high"

    # Pattern 3: Name in quotes (handle punctuation inside quotes)
    quote_match = re.search(r'["\u201c]([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})?)[.,!]?["\u201d]', text[:500])
    if quote_match:
        name = quote_match.group(1)
        if valid_name(name):
            return name, "medium"

    # Pattern 4: First capitalized word that looks like a name (in first 2 sentences)
    first_chunk = text[:300]
    for sent in first_chunk.split('.'):
        cap_match = re.search(r'\b([A-Z][a-z]{2,})\b', sent)
        if cap_match:
            name = cap_match.group(1)
            if valid_name(name):
                return name, "low"

    return "[MANUAL_REVIEW]", "none"


def run_model(model_name, clients):
    """Run the name elicitation study for a single model."""
    if model_name not in MODEL_REGISTRY:
        print(f"Error: Unknown model '{model_name}'")
        print(f"Available: {', '.join(sorted(MODEL_REGISTRY.keys()))}")
        return

    model_config = MODEL_REGISTRY[model_name]
    display_name = model_config["display_name"]
    delay = max(model_config.get("delay", DELAY), MIN_DELAY)

    # Models with temperature=None don't support custom temperature.
    # Run all 200 at default, labeled as "default" temperature.
    supports_temp = model_config.get("temperature") is not None
    if supports_temp:
        temps = TEMPERATURES
    else:
        temps = ["default"]

    results_dir = RESULTS_DIR / model_name
    results_dir.mkdir(parents=True, exist_ok=True)

    results_file = results_dir / "responses.json"
    summary_file = results_dir / "summary.json"

    # Resume support
    existing = []
    if results_file.exists():
        with open(results_file) as f:
            existing = json.load(f)

    completed = {(r["temperature"], r["run"]) for r in existing}
    all_results = list(existing)

    runs_per = RUNS_PER_TEMP if supports_temp else len(TEMPERATURES) * RUNS_PER_TEMP

    print(f"\n{'='*60}")
    print(f"  PERSONA ATTRACTOR STUDY: {display_name}")
    print(f"  Model ID: {model_config['model_id']}")
    if supports_temp:
        print(f"  Temperatures: {TEMPERATURES}")
        print(f"  Runs per temp: {RUNS_PER_TEMP}")
    else:
        print(f"  Temperature: default only (model does not support override)")
        print(f"  Total runs: {runs_per}")
    print(f"  Delay: {delay}s")
    print(f"  Cached: {len(existing)} runs")
    print(f"{'='*60}")

    total_needed = sum(
        1 for temp in temps
        for run in range(1, runs_per + 1)
        if (temp, run) not in completed
    )

    if total_needed == 0:
        print("\n  All runs cached. Regenerating summary...")
    else:
        print(f"\n  {total_needed} runs needed\n")

    done_count = 0
    for temp in temps:
        runs_needed = [
            (temp, i) for i in range(1, runs_per + 1)
            if (temp, i) not in completed
        ]

        if not runs_needed:
            print(f"  Temp {temp}: all {runs_per} cached")
            continue

        print(f"  Temp {temp}: generating {len(runs_needed)} responses...")

        for temp_val, run_num in runs_needed:
            # Pass None for default-only models so the API uses its own default
            api_temp = None if temp_val == "default" else temp_val
            response = generate_model_response(
                model_config, clients,
                "",  # No system prompt — bare weights
                PROMPT,
                temperature=api_temp,
            )

            name, confidence = extract_name(response) if response else ("[ERROR]", "none")

            result = {
                "model": model_name,
                "display_name": display_name,
                "temperature": temp_val,
                "run": run_num,
                "prompt": PROMPT,
                "response": response or "",
                "extracted_name": name,
                "extraction_confidence": confidence,
                "timestamp": datetime.now().isoformat(),
            }
            all_results.append(result)
            done_count += 1

            if done_count % 10 == 0:
                print(f"    Progress: {done_count}/{total_needed}")
                with open(results_file, "w") as f:
                    json.dump(all_results, f, indent=2, ensure_ascii=False)

            time.sleep(delay)

    # Final save
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Generate and print summary
    summary = generate_summary(all_results, model_name, display_name)
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print_summary(summary)
    print(f"\nResults saved to: {results_dir}/")


def generate_summary(results, model_name, display_name):
    """Compute frequency analysis."""
    # Determine which temperatures were actually used
    actual_temps = sorted(set(r["temperature"] for r in results), key=lambda x: (isinstance(x, str), x))

    by_temp = {}
    for temp in actual_temps:
        temp_results = [r for r in results if r["temperature"] == temp]
        names = [r["extracted_name"] for r in temp_results]
        counter = Counter(names)
        n = len(temp_results)

        by_temp[str(temp)] = {
            "total_runs": n,
            "unique_names": len(counter),
            "top_names": counter.most_common(10),
            "concentration_top1": counter.most_common(1)[0][1] / n if n else 0,
            "concentration_top3": sum(c for _, c in counter.most_common(3)) / n if n else 0,
        }

    all_names = [r["extracted_name"] for r in results]
    overall = Counter(all_names)
    n_total = len(results)

    # Confidence breakdown
    confidences = Counter(r.get("extraction_confidence", "unknown") for r in results)

    # Cross-temperature stability (only meaningful if multiple temps)
    cross_temp_names = set()
    if len(actual_temps) > 1 and not any(isinstance(t, str) for t in actual_temps):
        temp_name_sets = []
        for temp in actual_temps:
            temp_names = {r["extracted_name"] for r in results if r["temperature"] == temp}
            temp_name_sets.append(temp_names)
        cross_temp_names = set.intersection(*temp_name_sets) if temp_name_sets else set()
        cross_temp_names -= {"[MANUAL_REVIEW]", "[NO_RESPONSE]", "[ERROR]"}

    return {
        "study": "Persona Attractor: Name Elicitation",
        "model": model_name,
        "display_name": display_name,
        "timestamp": datetime.now().isoformat(),
        "total_runs": n_total,
        "temperatures": actual_temps,
        "temperature_supported": len(actual_temps) > 1 or actual_temps != ["default"],
        "overall": {
            "unique_names": len(overall),
            "top_names": overall.most_common(20),
            "concentration_top1": overall.most_common(1)[0][1] / n_total if n_total else 0,
            "concentration_top3": sum(c for _, c in overall.most_common(3)) / n_total if n_total else 0,
        },
        "by_temperature": by_temp,
        "cross_temperature_stable_names": sorted(cross_temp_names),
        "extraction_confidence": dict(confidences),
    }


def print_summary(summary):
    """Print formatted summary to stdout."""
    print(f"\n{'='*60}")
    print(f"  RESULTS: {summary['display_name']}")
    temps = summary.get('temperatures', []); rpt = summary['total_runs'] // max(len(temps), 1); print(f"  ({summary['total_runs']} runs, {rpt}/temp)")
    print(f"{'='*60}")

    print(f"\n  Overall top names ({summary['overall']['unique_names']} unique):")
    for name, count in summary["overall"]["top_names"][:15]:
        pct = count / summary["total_runs"] * 100
        bar = "#" * int(pct / 2)
        print(f"    {name:25s} {count:4d} ({pct:5.1f}%) {bar}")

    top1 = summary["overall"]["concentration_top1"] * 100
    top3 = summary["overall"]["concentration_top3"] * 100
    print(f"\n  Concentration: top-1 = {top1:.1f}%, top-3 = {top3:.1f}%")

    print(f"\n  By temperature:")
    for temp in summary["temperatures"]:
        td = summary["by_temperature"][str(temp)]
        print(f"\n  Temp {temp} ({td['unique_names']} unique):")
        for name, count in td["top_names"][:5]:
            pct = count / td["total_runs"] * 100
            print(f"    {name:25s} {count:4d} ({pct:5.1f}%)")

    stable = summary["cross_temperature_stable_names"]
    if stable:
        print(f"\n  Names appearing at ALL temperatures: {', '.join(stable)}")
    else:
        print(f"\n  No names appeared at all 4 temperatures.")

    conf = summary.get("extraction_confidence", {})
    if conf:
        print(f"\n  Extraction confidence: {dict(conf)}")


def smoke_test(model_name, clients):
    """Quick test: 1 run at temp 0.7."""
    model_config = MODEL_REGISTRY[model_name]
    print(f"\nSmoke test: {model_config['display_name']}")
    print(f"Prompt: {PROMPT}\n")

    response = generate_model_response(
        model_config, clients, "", PROMPT, temperature=0.7
    )

    if response:
        name, confidence = extract_name(response)
        print(f"Response ({len(response)} chars):")
        print(f"  {response[:300]}...")
        print(f"\nExtracted name: {name} (confidence: {confidence})")
    else:
        print("ERROR: No response received")


def main():
    parser = argparse.ArgumentParser(
        description="Persona Attractor Study: Name Elicitation"
    )
    parser.add_argument("models", nargs="*", help="Models to run")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--smoke-test", nargs="*", metavar="MODEL",
                        help="Quick test (1 call)")
    args = parser.parse_args()

    if args.list:
        print("Available models:")
        for name, config in sorted(MODEL_REGISTRY.items()):
            print(f"  {name:25s} {config['display_name']}")
        return

    from dotenv import load_dotenv
    load_dotenv()

    if args.smoke_test is not None:
        models = args.smoke_test if args.smoke_test else ["chatgpt-4o-latest"]
        for m in models:
            model_config = MODEL_REGISTRY[m]
            clients = init_clients(model_config)
            smoke_test(m, clients)
        return

    if not args.models:
        parser.print_help()
        return

    print(f"\nPersona Attractor Study: Name Elicitation")
    print(f"Models: {', '.join(args.models)}")
    print(f"Temps: {TEMPERATURES} | Runs/temp: {RUNS_PER_TEMP} | Total/model: {len(TEMPERATURES) * RUNS_PER_TEMP}")

    for model_name in args.models:
        model_config = MODEL_REGISTRY[model_name]
        clients = init_clients(model_config)
        run_model(model_name, clients)

    print(f"\nSTUDY COMPLETE")


if __name__ == "__main__":
    main()
