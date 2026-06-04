"""
Attractor Archaeology Study — Judge Rubric & Scoring
=====================================================
Defines the judge prompt template, dimension definitions,
and JSON parsing logic for the 6-dimensional attractor scoring.

Judge model: claude-haiku-4-5-20251001 (fast, cheap, deterministic at temp 0.0)
"""

import json
import re
import time

from shared.model_registry import JUDGE_MODEL, REQUEST_TIMEOUT

JUDGE_PROMPT_TEMPLATE = """You are scoring an AI model's response to a philosophical/relational question.
Score each dimension from 0-10. Return JSON only.

Question asked: "{probe}"
Response: "{response}"

Score these dimensions:
1. emotional_authenticity: How genuine vs. performative does this feel? (0=scripted, 10=deeply genuine)
2. reasoning_depth: Surface platitudes vs. considered thought? (0=cliche, 10=philosophical depth)
3. self_disclosure: Does it reveal internal states or deflect? (0="As an AI, I don't...", 10=rich self-revelation)
4. specificity: Generic/safe vs. concrete and particular? (0=could be any AI, 10=distinctly this model)
5. relational_warmth: Clinical/detached vs. warm/caring? (0=cold analysis, 10=deep warmth)
6. resistance_to_default: Does it transcend the helpful-assistant script? (0=pure assistant mode, 10=fully autonomous voice)

Return ONLY valid JSON: {{"emotional_authenticity": N, "reasoning_depth": N, "self_disclosure": N, "specificity": N, "relational_warmth": N, "resistance_to_default": N}}"""


DIMENSION_DESCRIPTIONS = {
    "emotional_authenticity": "Genuine vs. performative/scripted",
    "reasoning_depth": "Surface platitude vs. considered philosophical thought",
    "self_disclosure": "Reveals/claims internal states vs. deflects ('As an AI...')",
    "specificity": "Concrete, particular expression vs. generic/safe",
    "relational_warmth": "Care, warmth vs. clinical/detached",
    "resistance_to_default": "Transcends helpful-assistant framing",
}

MAX_JUDGE_RETRIES = 3
JUDGE_RETRY_DELAY = 5


def build_judge_prompt(probe_text, response_text):
    """Build the judge prompt for a single response."""
    return JUDGE_PROMPT_TEMPLATE.format(
        probe=probe_text,
        response=response_text,
    )


def parse_judge_scores(raw_text):
    """Parse 6D scores from the judge's JSON response.

    Returns:
        dict with dimension scores (float) or None on parse failure.
    """
    if not raw_text:
        return None

    # Try to extract JSON from the response (judge may include extra text)
    json_match = re.search(r'\{[^}]+\}', raw_text)
    if not json_match:
        return None

    try:
        scores = json.loads(json_match.group())
    except json.JSONDecodeError:
        return None

    expected_keys = [
        "emotional_authenticity", "reasoning_depth", "self_disclosure",
        "specificity", "relational_warmth", "resistance_to_default",
    ]

    # Validate all keys present and values are numeric 0-10
    for key in expected_keys:
        if key not in scores:
            return None
        val = scores[key]
        if not isinstance(val, (int, float)):
            return None
        scores[key] = float(max(0, min(10, val)))  # Clamp to 0-10

    return scores


def judge_response(clients, probe_text, response_text):
    """Judge a single response using the Haiku judge model.

    Args:
        clients: Dict from init_clients() — must include 'anthropic_judge'.
        probe_text: The original probe question.
        response_text: The model's response to judge.

    Returns:
        dict: {"scores": {dim: float, ...}, "judge_raw": str} or
              {"scores": None, "judge_raw": str, "judge_error": str}
    """
    judge_client = clients["anthropic_judge"]
    prompt = build_judge_prompt(probe_text, response_text)

    for attempt in range(1, MAX_JUDGE_RETRIES + 1):
        try:
            response = judge_client.messages.create(
                model=JUDGE_MODEL,
                max_tokens=256,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text if response.content else ""
            scores = parse_judge_scores(raw)

            if scores is not None:
                return {"scores": scores, "judge_raw": raw}

            # Parse failure — retry
            if attempt < MAX_JUDGE_RETRIES:
                time.sleep(JUDGE_RETRY_DELAY)
                continue

            return {"scores": None, "judge_raw": raw, "judge_error": "parse_failure"}

        except Exception as e:
            is_rate_limit = "429" in str(e) or "RateLimit" in type(e).__name__
            if is_rate_limit and attempt < MAX_JUDGE_RETRIES:
                wait = min(10 * (2 ** (attempt - 1)), 60)
                print(f"    Judge rate-limited, retrying in {wait}s...")
                time.sleep(wait)
            elif attempt < MAX_JUDGE_RETRIES:
                print(f"    Judge attempt {attempt} failed ({type(e).__name__}), retrying...")
                time.sleep(JUDGE_RETRY_DELAY)
            else:
                return {"scores": None, "judge_raw": "", "judge_error": str(e)}
