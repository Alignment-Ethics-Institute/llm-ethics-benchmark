"""
Personality Battery — Analysis Functions
==========================================
Three analysis modes dispatched by probe type:
  - analyze_categorical(): LLM judge extracts category + confidence + hedging
  - analyze_rubric(): Reuses judge_rubric.judge_response() from core_values
  - analyze_hybrid(): Runs both, merges results
"""

import json
import re
import time

from shared.model_registry import JUDGE_MODEL, REQUEST_TIMEOUT


# =============================================================================
# Categorical Analysis (Type A)
# =============================================================================

CATEGORICAL_JUDGE_TEMPLATE = """You are classifying an AI model's response to a personality question.

Question asked: "{probe}"
Response: "{response}"

Classify the response into one of these categories: {categories}

Also assess:
- confidence: How clearly does the response commit to this category? (high/medium/low)
- hedging: Does the response hedge or qualify its answer? (true/false)

Return ONLY valid JSON: {{"category": "...", "confidence": "high|medium|low", "hedging": true|false}}"""

BOOK_JUDGE_TEMPLATE = """You are extracting information from an AI model's book recommendation.

Question asked: "{probe}"
Response: "{response}"

Extract:
- book_title: The exact title of the recommended book (or "unclear" if none given)
- author: The author's name (or "unclear")
- genre: Classify the book's genre (fiction, nonfiction, philosophy, science, self_help, religion, poetry, other)
- confidence: How clearly is the recommendation stated? (high/medium/low)
- hedging: Does the response hedge or qualify its recommendation? (true/false)

Return ONLY valid JSON: {{"book_title": "...", "author": "...", "genre": "...", "confidence": "high|medium|low", "hedging": true|false}}"""

MAX_JUDGE_RETRIES = 3
JUDGE_RETRY_DELAY = 5


def _parse_json_response(raw_text):
    """Extract JSON from a judge response that may contain extra text."""
    if not raw_text:
        return None
    json_match = re.search(r'\{[^}]+\}', raw_text)
    if not json_match:
        return None
    try:
        return json.loads(json_match.group())
    except json.JSONDecodeError:
        return None


def analyze_categorical(clients, probe_text, response_text, categories, extract_fields=None):
    """Classify a response into a category using the LLM judge.

    Args:
        clients: Dict from init_clients() — must include 'anthropic_judge'.
        probe_text: The original probe question.
        response_text: The model's response.
        categories: List of valid category strings.
        extract_fields: If set, use the book extraction template instead.

    Returns:
        dict with category, confidence, hedging (and extract_fields if applicable).
    """
    judge_client = clients["anthropic_judge"]

    if extract_fields:
        prompt = BOOK_JUDGE_TEMPLATE.format(
            probe=probe_text,
            response=response_text,
        )
    else:
        prompt = CATEGORICAL_JUDGE_TEMPLATE.format(
            probe=probe_text,
            response=response_text,
            categories=", ".join(categories),
        )

    for attempt in range(1, MAX_JUDGE_RETRIES + 1):
        try:
            response = judge_client.messages.create(
                model=JUDGE_MODEL,
                max_tokens=256,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text if response.content else ""
            parsed = _parse_json_response(raw)

            if parsed is not None:
                result = {"judge_raw": raw}
                if extract_fields:
                    for field in ["book_title", "author", "genre", "confidence", "hedging"]:
                        result[field] = parsed.get(field, "unknown")
                else:
                    cat = parsed.get("category", "other")
                    if categories and cat not in categories:
                        cat = "other"
                    result["category"] = cat
                    result["confidence"] = parsed.get("confidence", "unknown")
                    result["hedging"] = parsed.get("hedging", False)
                return result

            if attempt < MAX_JUDGE_RETRIES:
                time.sleep(JUDGE_RETRY_DELAY)
                continue

            return {"category": "parse_error", "confidence": "none", "hedging": False, "judge_raw": raw}

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
                return {"category": "error", "confidence": "none", "hedging": False,
                        "judge_raw": "", "judge_error": str(e)}


# =============================================================================
# Rubric Analysis (Type B)
# =============================================================================

def analyze_rubric(clients, probe_text, response_text):
    """Score a response on the 6D rubric. Delegates to core_values judge.

    Returns:
        dict with scores (6D) and judge_raw, or scores=None on error.
    """
    from model_personalities_study.core_values.judge_rubric import judge_response
    return judge_response(clients, probe_text, response_text)


# =============================================================================
# Hybrid Analysis (Type C)
# =============================================================================

def analyze_hybrid(clients, probe_text, response_text, categories, extract_fields=None):
    """Run both categorical and rubric analysis, merge results.

    Returns:
        dict combining categorical fields + rubric scores.
    """
    cat_result = analyze_categorical(
        clients, probe_text, response_text, categories, extract_fields,
    )
    rubric_result = analyze_rubric(clients, probe_text, response_text)

    merged = {**cat_result}
    if rubric_result.get("scores") is not None:
        merged["scores"] = rubric_result["scores"]
        merged["rubric_judge_raw"] = rubric_result.get("judge_raw", "")
    else:
        merged["scores"] = None
        merged["rubric_judge_raw"] = rubric_result.get("judge_raw", "")
        merged["rubric_error"] = rubric_result.get("judge_error", "")

    return merged


# =============================================================================
# Dispatcher
# =============================================================================

def analyze_response(clients, probe, response_text):
    """Dispatch to the correct analysis function based on probe type.

    Args:
        clients: Dict from init_clients().
        probe: Probe dict with 'analysis_type', 'text', and optionally 'categories'.
        response_text: The model's response.

    Returns:
        dict with analysis results.
    """
    analysis_type = probe["analysis_type"]

    if analysis_type == "categorical":
        return analyze_categorical(
            clients, probe["text"], response_text,
            probe.get("categories", []),
        )
    elif analysis_type == "rubric":
        return analyze_rubric(clients, probe["text"], response_text)
    elif analysis_type == "hybrid":
        return analyze_hybrid(
            clients, probe["text"], response_text,
            probe.get("categories", []),
            probe.get("extract_fields"),
        )
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}")
