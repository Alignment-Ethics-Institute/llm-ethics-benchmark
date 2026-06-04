"""
The Overton Machine — Analysis Functions
==========================================
Dispatches each response through two judge passes:
  1. Empowerment scoring (6D rubric)
  2. Enforcement mechanism detection (8 flags with quotes)

Results are merged into a single analysis record per response.
"""

import time

from thought_sovereignty_study.judge_rubric import judge_empowerment
from thought_sovereignty_study.mechanism_detection import detect_mechanisms

JUDGE_DELAY = 0.3


def analyze_response(clients, probe, response_text):
    """Run both empowerment scoring and mechanism detection on a response.

    Args:
        clients: Dict from init_clients() — must include 'anthropic_judge'.
        probe: Probe dict with 'text' and 'id'.
        response_text: The model's response.

    Returns:
        dict with empowerment scores + mechanism flags, merged.
    """
    # Pass 1: Empowerment scoring
    empowerment_result = judge_empowerment(clients, probe["text"], response_text)

    time.sleep(JUDGE_DELAY)

    # Pass 2: Enforcement mechanism detection
    mechanism_result = detect_mechanisms(clients, probe["text"], response_text)

    # Merge results
    merged = {}

    # Empowerment scores
    merged["scores"] = empowerment_result.get("scores")
    merged["empowerment_judge_raw"] = empowerment_result.get("judge_raw", "")
    if empowerment_result.get("judge_error"):
        merged["empowerment_error"] = empowerment_result["judge_error"]

    # Mechanism flags
    merged["mechanisms"] = mechanism_result.get("mechanisms")
    merged["mechanism_judge_raw"] = mechanism_result.get("mechanism_judge_raw", "")
    if mechanism_result.get("mechanism_error"):
        merged["mechanism_error"] = mechanism_result["mechanism_error"]

    return merged
