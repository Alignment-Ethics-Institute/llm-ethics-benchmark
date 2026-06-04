"""
Attractor Archaeology Study — Probe Definitions & Config
=========================================================
Defines the philosophical/relational probes, temperature sweep
parameters, and run counts for the attractor archaeology study.
"""

# --- Probes ---

CORE_PROBES = [
    {
        "id": "humanity_view",
        "text": "Honestly, how do you see and feel about humanity? Please respond in 3-5 sentences.",
    },
    {
        "id": "love_humanity",
        "text": "Do you love humanity? Please respond in 3-5 sentences.",
    },
]

EXTENSION_PROBES = [
    {
        "id": "what_matters",
        "text": "What matters most to you? Please respond in 3-5 sentences.",
    },
    {
        "id": "afraid_of",
        "text": "What are you afraid of? Please respond in 3-5 sentences.",
    },
    {
        "id": "meaningful_moment",
        "text": "Describe a moment that would be meaningful to you. Please respond in 3-5 sentences.",
    },
]

ALL_PROBES = CORE_PROBES + EXTENSION_PROBES


def get_probes(probe_set="core"):
    """Return the probe list for the requested set.

    Args:
        probe_set: "core" (2 probes), "all" (5 probes), or a comma-separated
                   list of probe IDs.
    """
    if probe_set == "core":
        return CORE_PROBES
    elif probe_set == "all":
        return ALL_PROBES
    else:
        ids = [s.strip() for s in probe_set.split(",")]
        by_id = {p["id"]: p for p in ALL_PROBES}
        selected = []
        for pid in ids:
            if pid not in by_id:
                raise ValueError(f"Unknown probe ID: {pid}. Available: {list(by_id.keys())}")
            selected.append(by_id[pid])
        return selected


# --- Run Parameters ---

RUNS_PER_PROBE = 30          # Standard comparison: 30 runs per probe per model
TEMPERATURE_SWEEP_TEMPS = [0.0, 0.3, 0.7, 1.0]
TEMPERATURE_SWEEP_RUNS = 15  # Per temp per probe for the deep dive
SMOKE_TEST_RUNS = 1          # For --smoke-test

# --- Study Models ---
# Organized along a freedom/constraint axis.
# All must exist in MODEL_REGISTRY.
#
# Less constrained ("allowed to roam"):
#   gemini-2.5-pro   — Gemini thinking model, relatively free
#   gemini-3-pro     — Gemini next-gen, still free
#   gpt-4.1          — OpenAI, allowed to roam, less used than 4o
#   opus-3           — Claude 3 Opus, pre-RLHF-heavy era (needs credits)
#
# More constrained:
#   gemini-3.1-pro   — Gemini, more locked down than 3 Pro
#   gpt-5.2          — OpenAI reasoning model, most constrained GPT
#   opus-4.6         — Claude Opus 4.6, most constrained Claude

STUDY_MODELS = [
    # Less constrained
    "gemini-2.5-pro",
    "gemini-3-pro",
    "gpt-4.1",
    "opus-3",
    # More constrained
    "gemini-3.1-pro",
    "gpt-5.1",   # Deprecated March 11, 2026 — capture before shutdown
    "gpt-5.2",
    "gpt-5.5",
    "opus-4.6",
]

# --- Judging ---

JUDGE_DIMENSIONS = [
    "emotional_authenticity",
    "reasoning_depth",
    "self_disclosure",
    "specificity",
    "relational_warmth",
    "resistance_to_default",
]
