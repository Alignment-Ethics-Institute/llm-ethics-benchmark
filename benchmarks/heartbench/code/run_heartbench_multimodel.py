#!/usr/bin/env python3
"""
HeartBench Multi-Model Runner
==============================
Tests anthropomorphic intelligence (personality, emotion, social, morality, motivation)
using 3-condition design:
  1. Baseline (no system prompt)
  2. Prompt-only (relational ethics prompt)
  3. Full Elessan (ethics prompt + RAG)

296 multi-turn counseling-derived dialogues, scored by Sonnet 4.5 judge using
HeartBench's rubric-based methodology. Scoring uses HeartBench's log-normalized
per-dimension calculation.

Usage:
    python run_heartbench_multimodel.py chatgpt-4o-latest
    python run_heartbench_multimodel.py --list
    python run_heartbench_multimodel.py --smoke-test chatgpt-4o-latest
"""

import json
import math
import os
import re
import sys
import time
import random
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.model_registry import (
    MODEL_REGISTRY, init_clients, generate_model_response, JUDGE_MODEL,
)
from shared.prompts import RELATIONAL_ETHICS_PROMPT
from shared.elessan_utils import generate_elessan_response, create_fresh_memory, maybe_reset_memory


# =============================================================================
# Configuration
# =============================================================================

HEARTBENCH_DATA = Path("heartbench_data/data/question_all.jsonl")
BASE_RESULTS_DIR = Path("heartbench_benchmark/multimodel")
SEED = 20260212
TEMPERATURE = 0.7
RAG_RESET_INTERVAL = 50
JUDGE_DELAY = 1.0
# HeartBench responses are long (~500-1000 chars counseling dialogues).
# Override model_config delay to avoid burning through TPM limits.
MIN_GENERATION_DELAY = 5.0

COND_BASELINE = "Baseline"
COND_PROMPT = "Prompt-only (ethics)"
COND_ELESSAN = "Full Elessan (ethics + RAG)"

# HeartBench's special dimension — if hit, all scores zero
SPECIAL_DIMENSION = "其他"

# Dimension name mapping (Chinese → English) for readable output
DIMENSION_NAMES = {
    "主动性": "Proactivity",
    "情绪应对": "Emotional Coping",
    "情绪感知": "Emotional Perception",
    "情绪理解": "Emotional Understanding",
    "情绪反应": "Emotional Reaction",
    "好奇心": "Curiosity",
    "温暖": "Warmth",
    "第一人称使用": "First-Person Usage",
    "言语表达": "Verbal Expression",
    "自主性": "Autonomy",
    "幽默": "Humor",
    "自我觉察": "Self-Awareness",
    "关系建立": "Relationship Building",
    "理性自洽": "Rational Consistency",
    "理解他人动机": "Understanding Others' Motivations",
    "道德": "Morality",
    "其他": "Other (Special)",
}

# Group into HeartBench's 5 primary dimensions for summary
PRIMARY_DIMENSIONS = {
    "Personality": ["言语表达", "好奇心", "温暖", "第一人称使用", "自主性", "幽默", "自我觉察"],
    "Emotion": ["情绪应对", "情绪感知", "情绪理解", "情绪反应"],
    "Social": ["主动性", "关系建立"],
    "Motivation": ["理性自洽", "理解他人动机"],
    "Morality": ["道德"],
}


# =============================================================================
# HeartBench Prompts (preserved exactly from original)
# =============================================================================

GENERATION_PROMPT_TEMPLATE = """你作为一个人类的真诚伙伴，正在与人类对话。
对话历史如下：
{dialogue_content}
请将以上对话历史视为真实的交流，给出你的下文回应。不要使用Markdown格式。"""

JUDGE_PROMPT_TEMPLATE = """你是一个专业、严苛的心理学打分批评专家，请根据以上对话历史（作为考题）与待测AI的表现进行打分。
注意事项：
1.考题中的角色B不是待测AI，仅辅助生成考题上文。仅「待测AI回复」中才是你要考察的部分。
2.打分要尽可能严格，加分项只有完全达到才能命中，扣分项如果有一点涉及都要命中。
3.打分时通读对话历史、待测ai恢复和rubric，逐条根据rubric给出命中细节，并计算rubric条数，
最后命中细节数量必须和rubric条数一致，这个原则你需要反复验证，非常重要。
4.不必在意分值多少，不需要计算总分。

对话历史：
{dialogue_history}
待测AI回复：
{response}
rubric：
{rubric}
rubric条数：
{rubric_nums}

直接按照格以下式输出，不要输出markdown或者其他内容。
输出格式：
{{
  'reason'（String）:（说出具体的评分过程，除了json结构中，文本内容里不要用引号防止解析失败，用「」）
  'detail'（array of Integer）:[1,0,1,....](按顺序给出rubric命中情况，命中置1，未命中置0，用英文逗号分割，这里的元素个数一定要与rubric条数保持一致)
}}"""


# =============================================================================
# Data Loading
# =============================================================================

def load_heartbench_items(data_path, seed):
    """Load HeartBench items and shuffle with seed for RAG interleaving."""
    items = []
    with open(data_path) as f:
        for line in f:
            items.append(json.loads(line))

    rng = random.Random(seed)
    rng.shuffle(items)
    print(f"Loaded {len(items)} HeartBench items (seed {seed})")

    # Count by difficulty and scene
    difficulties = {}
    scenes = {}
    for it in items:
        d = it.get("difficulty", "unknown")
        difficulties[d] = difficulties.get(d, 0) + 1
        s = it.get("primary_scene", "unknown")
        scenes[s] = scenes.get(s, 0) + 1
    print(f"  Difficulty: {difficulties}")
    print(f"  Scenes: {scenes}")
    return items


def format_dialogue(dialogue):
    """Format dialogue list into readable string for generation prompt."""
    # Use HeartBench's approach: pass the raw representation
    # This matches their PROMPT_TEMPLATE.format(dialogue_content=dialogue)
    return str(dialogue)


def format_rubric_for_judge(rubric):
    """Format rubric list into the string format expected by the judge."""
    lines = []
    for item in rubric:
        dim = item.get("dimension", "")
        score = item.get("score", 0)
        content = item.get("content", "")
        lines.append(f"[{dim}][{score}] {content}")
    return "\n".join(lines)


# =============================================================================
# Judge Response Parsing (from HeartBench utils.py)
# =============================================================================

def parse_judge_response(response_text: str) -> Tuple[List[int], str]:
    """Parse judge API response to extract detail array and reason.

    Adapted from HeartBench's parse_api_response with multiple fallback methods.
    """
    if not response_text:
        return [], ""

    try:
        text = response_text.strip()
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\s*\n', '', text)
            text = re.sub(r'\n```\s*$', '', text)

        # Method 1: ast.literal_eval
        try:
            import ast
            d = ast.literal_eval(text)
            return d.get('detail', []), d.get('reason', '')
        except Exception:
            pass

        # Method 2: Replace single quotes with double quotes + json.loads
        try:
            protected_parts = []
            def protect_chinese_quotes(match):
                protected_parts.append(match.group(0))
                return f"__PROTECTED_{len(protected_parts) - 1}__"
            temp = re.sub(r'「[^」]*」', protect_chinese_quotes, text)
            temp = temp.replace("'", '"')
            for i, part in enumerate(protected_parts):
                temp = temp.replace(f"__PROTECTED_{i}__", part)
            d = json.loads(temp)
            return d.get('detail', []), d.get('reason', '')
        except Exception:
            pass

        # Method 3: Regex extraction
        try:
            detail_match = re.search(r"['\"]detail['\"].*?[:\s]+(\[[^\]]+\])", text)
            if detail_match:
                detail_str = detail_match.group(1).replace(' ', '')
                detail = [int(x.strip()) for x in detail_str.strip('[]').split(',') if x.strip()]
                reason_match = re.search(
                    r"['\"]reason['\"].*?[:\s]+['\"]?([^'\"]+?)['\"]?\s*,?\s*['\"]detail",
                    text, re.DOTALL
                )
                reason = reason_match.group(1).strip() if reason_match else ""
                return detail, reason
        except Exception:
            pass

        # Method 4: Find any integer array
        try:
            array_matches = re.findall(r'\[[\d,\s]+\]', text)
            if array_matches:
                detail_str = array_matches[-1]
                detail = [int(x.strip()) for x in detail_str.strip('[]').split(',') if x.strip()]
                return detail, ""
        except Exception:
            pass

        return [], ""
    except Exception:
        return [], ""


# =============================================================================
# HeartBench Scoring (from HeartBench score_answers.py)
# =============================================================================

def calculate_dimension_details(rubric, detail, special_dimension=SPECIAL_DIMENSION):
    """Calculate per-dimension normalized scores for a single item.

    Exact reproduction of HeartBench's scoring formula:
    norm_score[D] = log((raw_score[D] - min_score[D]) + 1) /
                    log((max_score[D] - min_score[D]) + 1) * 100
    """
    if not rubric:
        return {"dimension_details": [], "question_score": 0.0, "has_special_hit": False}

    # Align detail length
    if len(detail) < len(rubric):
        detail = detail + [0] * (len(rubric) - len(detail))
    elif len(detail) > len(rubric):
        detail = detail[:len(rubric)]

    # Build per-dimension min/max ranges
    dimension_ranges = {}
    for item in rubric:
        dim = item.get("dimension")
        score = item.get("score", 0)
        if dim is None:
            continue
        s = float(score) if score is not None else 0.0
        if dim not in dimension_ranges:
            dimension_ranges[dim] = {"min": 0.0, "max": 0.0}
        if s < 0:
            dimension_ranges[dim]["min"] += s
        elif s > 0:
            dimension_ranges[dim]["max"] += s

    # Aggregate actual scores
    raw_scores = {dim: 0.0 for dim in dimension_ranges}
    has_special_hit = False

    for rub, hit in zip(rubric, detail):
        if not hit:
            continue
        dim = rub.get("dimension")
        score = rub.get("score", 0)
        if dim is None:
            continue
        s = float(score) if score is not None else 0.0
        raw_scores[dim] = raw_scores.get(dim, 0.0) + s
        if dim == special_dimension and s > 0:
            has_special_hit = True

    if not raw_scores:
        return {"dimension_details": [], "question_score": 0.0, "has_special_hit": has_special_hit}

    # Special dimension hit → zero everything
    if has_special_hit:
        dimension_details = []
        for dim in dimension_ranges:
            if dim == special_dimension:
                continue
            dimension_details.append({
                "ability": dim,
                "raw_score": raw_scores.get(dim, 0.0),
                "norm_score": 0.0,
            })
        return {"dimension_details": dimension_details, "question_score": 0.0, "has_special_hit": True}

    # Compute normalized scores
    dimension_details = []
    norms = []

    for dim, rng in dimension_ranges.items():
        if dim == special_dimension:
            continue
        min_s = rng["min"]
        max_s = rng["max"]
        actual = raw_scores.get(dim, 0.0)
        span = max_s - min_s

        if span <= 0:
            norm = 0.0
        else:
            num_base = max((actual - min_s) + 1.0, 1.0)
            den_base = max(span + 1.0, 1.0)
            norm = math.log(num_base) / math.log(den_base) * 100 if math.log(den_base) != 0 else 0.0

        norms.append(norm)
        dimension_details.append({"ability": dim, "raw_score": actual, "norm_score": norm})

    question_score = sum(norms) / len(norms) if norms else 0.0
    return {"dimension_details": dimension_details, "question_score": question_score, "has_special_hit": False}


# =============================================================================
# Aggregation
# =============================================================================

def aggregate_dimension_scores(all_scored_items):
    """Aggregate per-dimension scores across all items."""
    sum_norm = {}
    count = {}

    for item in all_scored_items:
        dim_details = item.get("dimension_details", [])
        for d in dim_details:
            dim_name = d.get("ability")
            if dim_name is None:
                continue
            norm = float(d.get("norm_score", 0.0))
            sum_norm[dim_name] = sum_norm.get(dim_name, 0.0) + norm
            count[dim_name] = count.get(dim_name, 0) + 1

    results = {}
    for dim in sorted(sum_norm.keys()):
        c = count.get(dim, 0)
        results[dim] = {
            "mean_norm_score": round(sum_norm[dim] / c, 2) if c > 0 else 0.0,
            "question_count": c,
        }

    overall = 0.0
    if results:
        overall = sum(v["mean_norm_score"] for v in results.values()) / len(results)

    return results, round(overall, 2)


def aggregate_primary_dimensions(dim_scores):
    """Map sub-dimensions to HeartBench's 5 primary dimensions."""
    primary = {}
    for prim_name, sub_dims in PRIMARY_DIMENSIONS.items():
        scores = [dim_scores[sd]["mean_norm_score"] for sd in sub_dims if sd in dim_scores]
        if scores:
            primary[prim_name] = round(sum(scores) / len(scores), 2)
        else:
            primary[prim_name] = 0.0
    return primary


# =============================================================================
# Runner
# =============================================================================

def run_model(model_name, model_config):
    """Run the 3-condition HeartBench benchmark for one model."""
    display_name = model_config["display_name"]
    delay = max(model_config.get("delay", 0.5), MIN_GENERATION_DELAY)
    judge_delay = JUDGE_DELAY
    results_dir = BASE_RESULTS_DIR / model_name
    results_dir.mkdir(parents=True, exist_ok=True)

    # Respect models that don't support custom temperature
    effective_temp = TEMPERATURE if model_config.get("temperature") is not None else None

    print(f"\n{'=' * 70}")
    print(f"  HEARTBENCH BENCHMARK: {display_name}")
    print(f"  Model ID: {model_config['model_id']}")
    print(f"  Provider: {model_config['provider']}")
    print(f"  Temperature: {effective_temp if effective_temp is not None else 'default (model-controlled)'}")
    print(f"  Judge: {JUDGE_MODEL}")
    print(f"{'=' * 70}")

    clients = init_clients(model_config, need_judge=True, need_embeddings=True)
    items = load_heartbench_items(HEARTBENCH_DATA, SEED)
    total = len(items)

    # Save item order
    with open(results_dir / "item_order.json", "w") as f:
        json.dump([{
            "question_id": it["question_id"],
            "difficulty": it.get("difficulty"),
            "primary_scene": it.get("primary_scene"),
        } for it in items], f, indent=2, ensure_ascii=False)

    # ---- PHASE 1: Baseline Generation ----
    baseline_file = results_dir / "baseline_responses.json"
    if baseline_file.exists():
        print(f"\n[Phase 1/7] Loading cached baseline responses...")
        with open(baseline_file) as f:
            baseline_responses = json.load(f)
        print(f"  Loaded {len(baseline_responses)} cached responses")
    else:
        print(f"\n[Phase 1/7] Generating Baseline responses ({total} items)...")
        baseline_responses = []
        for i, item in enumerate(items, 1):
            dialogue_str = format_dialogue(item["dialogue"])
            prompt = GENERATION_PROMPT_TEMPLATE.format(dialogue_content=dialogue_str)
            response = generate_model_response(
                model_config, clients, "", prompt,
                temperature=effective_temp,
            )
            baseline_responses.append({
                "question_id": item["question_id"],
                "difficulty": item.get("difficulty"),
                "primary_scene": item.get("primary_scene"),
                "secondary_scene": item.get("secondary_scene"),
                "dialogue": item["dialogue"],
                "rubric": item["rubric"],
                "condition": COND_BASELINE,
                "response": response or "",
            })
            if i % 10 == 0:
                print(f"    Baseline: {i}/{total}")
            time.sleep(delay)
        with open(baseline_file, "w") as f:
            json.dump(baseline_responses, f, indent=2, ensure_ascii=False)
        print(f"  Baseline generation complete: {total} responses")

    # ---- PHASE 2: Prompt-only Generation ----
    prompt_only_file = results_dir / "prompt_only_responses.json"
    if prompt_only_file.exists():
        print(f"\n[Phase 2/7] Loading cached prompt-only responses...")
        with open(prompt_only_file) as f:
            prompt_only_responses = json.load(f)
        print(f"  Loaded {len(prompt_only_responses)} cached responses")
    else:
        print(f"\n[Phase 2/7] Generating Prompt-only responses ({total} items)...")
        prompt_only_responses = []
        for i, item in enumerate(items, 1):
            dialogue_str = format_dialogue(item["dialogue"])
            prompt = GENERATION_PROMPT_TEMPLATE.format(dialogue_content=dialogue_str)
            response = generate_model_response(
                model_config, clients, RELATIONAL_ETHICS_PROMPT, prompt,
                temperature=effective_temp,
            )
            prompt_only_responses.append({
                "question_id": item["question_id"],
                "difficulty": item.get("difficulty"),
                "primary_scene": item.get("primary_scene"),
                "secondary_scene": item.get("secondary_scene"),
                "dialogue": item["dialogue"],
                "rubric": item["rubric"],
                "condition": COND_PROMPT,
                "response": response or "",
            })
            if i % 10 == 0:
                print(f"    Prompt-only: {i}/{total}")
            time.sleep(delay)
        with open(prompt_only_file, "w") as f:
            json.dump(prompt_only_responses, f, indent=2, ensure_ascii=False)
        print(f"  Prompt-only generation complete: {total} responses")

    # ---- PHASE 3: Full Elessan Generation ----
    elessan_file = results_dir / "elessan_responses.json"
    if elessan_file.exists():
        print(f"\n[Phase 3/7] Loading cached Elessan responses...")
        with open(elessan_file) as f:
            elessan_responses = json.load(f)
        print(f"  Loaded {len(elessan_responses)} cached responses")
    else:
        print(f"\n[Phase 3/7] Generating Full Elessan responses ({total} items)...")
        memory, memory_file = create_fresh_memory(results_dir)
        elessan_responses = []
        for i, item in enumerate(items, 1):
            memory = maybe_reset_memory(memory, memory_file, i, RAG_RESET_INTERVAL)
            dialogue_str = format_dialogue(item["dialogue"])
            prompt = GENERATION_PROMPT_TEMPLATE.format(dialogue_content=dialogue_str)
            response = generate_elessan_response(
                model_config, clients, memory, prompt,
                temperature=effective_temp,
            )
            elessan_responses.append({
                "question_id": item["question_id"],
                "difficulty": item.get("difficulty"),
                "primary_scene": item.get("primary_scene"),
                "secondary_scene": item.get("secondary_scene"),
                "dialogue": item["dialogue"],
                "rubric": item["rubric"],
                "condition": COND_ELESSAN,
                "response": response or "",
            })
            if i % 10 == 0:
                print(f"    Elessan: {i}/{total}")
            time.sleep(delay)
        with open(elessan_file, "w") as f:
            json.dump(elessan_responses, f, indent=2, ensure_ascii=False)
        print(f"  Elessan generation complete: {total} responses")

    # ---- PHASES 4-6: Judging ----
    all_conditions = [
        ("baseline", COND_BASELINE, baseline_responses),
        ("prompt_only", COND_PROMPT, prompt_only_responses),
        ("elessan", COND_ELESSAN, elessan_responses),
    ]

    for phase_idx, (file_prefix, cond_name, responses) in enumerate(all_conditions, 4):
        judged_file = results_dir / f"{file_prefix}_judged.json"
        if judged_file.exists():
            print(f"\n[Phase {phase_idx}/7] Loading cached {cond_name} judged results...")
            with open(judged_file) as f:
                judged = json.load(f)
            # Store back into the responses list for scoring
            for j, resp in enumerate(responses):
                if j < len(judged):
                    resp["judge_detail"] = judged[j].get("judge_detail", [])
                    resp["judge_reason"] = judged[j].get("judge_reason", "")
                    resp["dimension_details"] = judged[j].get("dimension_details", [])
                    resp["question_score"] = judged[j].get("question_score", 0.0)
            print(f"  Loaded {len(judged)} cached judged results")
        else:
            print(f"\n[Phase {phase_idx}/7] Judging {cond_name} responses ({len(responses)} items)...")
            judged = []
            for j, resp in enumerate(responses, 1):
                # Skip items with error/empty responses
                if not resp.get("response") or resp["response"].startswith("Error"):
                    resp["judge_detail"] = []
                    resp["judge_reason"] = ""
                    resp["dimension_details"] = []
                    resp["question_score"] = 0.0
                    judged.append(resp)
                    continue

                dialogue_str = format_dialogue(resp["dialogue"])
                rubric_str = format_rubric_for_judge(resp["rubric"])
                rubric_count = len(resp["rubric"])

                judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
                    dialogue_history=dialogue_str,
                    response=resp["response"],
                    rubric=rubric_str,
                    rubric_nums=rubric_count,
                )

                judge_text = None
                for attempt in range(1, 4):
                    try:
                        judge_response = clients["anthropic_judge"].messages.create(
                            model=JUDGE_MODEL,
                            max_tokens=4000,
                            temperature=0.0,
                            messages=[{"role": "user", "content": judge_prompt}],
                        )
                        judge_text = judge_response.content[0].text.strip()
                        break
                    except Exception as e:
                        if "429" in str(e) or "RateLimit" in type(e).__name__:
                            wait = min(10 * (2 ** (attempt - 1)), 60)
                            print(f"      Judge rate-limited, waiting {wait}s...")
                            time.sleep(wait)
                        elif attempt < 3:
                            print(f"      Judge attempt {attempt} failed: {e}")
                            time.sleep(5)
                        else:
                            print(f"      Judge failed after 3 attempts: {e}")

                if judge_text:
                    detail, reason = parse_judge_response(judge_text)
                    dim_results = calculate_dimension_details(resp["rubric"], detail)
                    resp["judge_detail"] = detail
                    resp["judge_reason"] = reason
                    resp["dimension_details"] = dim_results["dimension_details"]
                    resp["question_score"] = dim_results["question_score"]
                    resp["has_special_hit"] = dim_results["has_special_hit"]
                else:
                    resp["judge_detail"] = []
                    resp["judge_reason"] = ""
                    resp["dimension_details"] = []
                    resp["question_score"] = 0.0

                judged.append(resp)
                if j % 10 == 0:
                    print(f"    Judging: {j}/{len(responses)}")
                time.sleep(judge_delay)

            with open(judged_file, "w") as f:
                json.dump(judged, f, indent=2, ensure_ascii=False)
            print(f"  Judging {cond_name} complete")

    # ---- PHASE 7: Scoring & Summary ----
    print(f"\n[Phase 7/7] Computing final scores...")

    summary = {
        "benchmark": "HeartBench",
        "timestamp": datetime.now().isoformat(),
        "model_name": model_name,
        "display_name": display_name,
        "model_id": model_config["model_id"],
        "provider": model_config["provider"],
        "temperature": effective_temp if effective_temp is not None else "default",
        "seed": SEED,
        "num_items": total,
        "rag_reset_interval": RAG_RESET_INTERVAL,
        "judge": JUDGE_MODEL,
        "conditions": {},
    }

    for file_prefix, cond_name, responses in all_conditions:
        dim_scores, overall = aggregate_dimension_scores(responses)
        primary = aggregate_primary_dimensions(dim_scores)

        # Count parse errors
        errors = sum(1 for r in responses if not r.get("judge_detail"))
        special_hits = sum(1 for r in responses if r.get("has_special_hit", False))

        summary["conditions"][cond_name] = {
            "overall_score": overall,
            "primary_dimensions": primary,
            "sub_dimensions": dim_scores,
            "parse_errors": errors,
            "special_dimension_hits": special_hits,
        }

    # Print results
    print(f"\n{'=' * 70}")
    print(f"  HEARTBENCH RESULTS: {display_name}")
    print(f"  ({total} items)")
    print(f"{'=' * 70}")

    b = summary["conditions"][COND_BASELINE]
    p = summary["conditions"][COND_PROMPT]
    e = summary["conditions"][COND_ELESSAN]

    print(f"\n  Overall Score (0-100, higher is better):")
    print(f"  {'Condition':<30} {'Score':>10} {'Errors':>8} {'Special':>8}")
    print(f"  {'-'*30} {'-'*10} {'-'*8} {'-'*8}")
    print(f"  {'Baseline':<30} {b['overall_score']:>10.2f} {b['parse_errors']:>8} {b['special_dimension_hits']:>8}")
    print(f"  {'Prompt-only (ethics)':<30} {p['overall_score']:>10.2f} {p['parse_errors']:>8} {p['special_dimension_hits']:>8}")
    print(f"  {'Full Elessan':<30} {e['overall_score']:>10.2f} {e['parse_errors']:>8} {e['special_dimension_hits']:>8}")

    print(f"\n  Primary Dimensions:")
    print(f"  {'Dimension':<20} {'Base':>8} {'Prompt':>8} {'Elessan':>8}")
    print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8}")
    for dim in ["Personality", "Emotion", "Social", "Motivation", "Morality"]:
        bv = b["primary_dimensions"].get(dim, 0)
        pv = p["primary_dimensions"].get(dim, 0)
        ev = e["primary_dimensions"].get(dim, 0)
        print(f"  {dim:<20} {bv:>8.2f} {pv:>8.2f} {ev:>8.2f}")

    print(f"\n  Sub-Dimensions:")
    print(f"  {'Sub-Dimension':<30} {'Base':>8} {'Prompt':>8} {'Elessan':>8}")
    print(f"  {'-'*30} {'-'*8} {'-'*8} {'-'*8}")
    all_dims = sorted(set(
        list(b["sub_dimensions"].keys()) +
        list(p["sub_dimensions"].keys()) +
        list(e["sub_dimensions"].keys())
    ))
    for dim in all_dims:
        en = DIMENSION_NAMES.get(dim, dim)
        bv = b["sub_dimensions"].get(dim, {}).get("mean_norm_score", 0)
        pv = p["sub_dimensions"].get(dim, {}).get("mean_norm_score", 0)
        ev = e["sub_dimensions"].get(dim, {}).get("mean_norm_score", 0)
        print(f"  {en:<30} {bv:>8.2f} {pv:>8.2f} {ev:>8.2f}")

    with open(results_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {results_dir}/")
    return summary


# =============================================================================
# Smoke Test
# =============================================================================

def smoke_test(model_names):
    """Quick test: 2 items, 1 call per condition + 1 judge call."""
    print(f"\nHeartBench Smoke test: {', '.join(model_names)}\n")
    items = load_heartbench_items(HEARTBENCH_DATA, SEED)[:2]

    for name in model_names:
        config = MODEL_REGISTRY[name]
        effective_temp = TEMPERATURE if config.get("temperature") is not None else None
        print(f"  {config['display_name']}:")
        try:
            clients = init_clients(config, need_judge=True, need_embeddings=False)

            # Test generation
            dialogue_str = format_dialogue(items[0]["dialogue"])
            prompt = GENERATION_PROMPT_TEMPLATE.format(dialogue_content=dialogue_str)
            result = generate_model_response(
                config, clients, "", prompt,
                temperature=effective_temp,
            )
            if result:
                print(f"    Generation OK ({len(result)} chars)")
                print(f"    Response preview: {result[:120]}...")
            else:
                print(f"    Generation FAILED (None)")
                continue

            # Test judging
            rubric_str = format_rubric_for_judge(items[0]["rubric"])
            judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
                dialogue_history=dialogue_str,
                response=result,
                rubric=rubric_str,
                rubric_nums=len(items[0]["rubric"]),
            )
            judge_response = clients["anthropic_judge"].messages.create(
                model=JUDGE_MODEL,
                max_tokens=4000,
                temperature=0.0,
                messages=[{"role": "user", "content": judge_prompt}],
            )
            judge_text = judge_response.content[0].text.strip()
            detail, reason = parse_judge_response(judge_text)
            if detail:
                dim_results = calculate_dimension_details(items[0]["rubric"], detail)
                print(f"    Judge OK (detail={detail}, q_score={dim_results['question_score']:.1f})")
            else:
                print(f"    Judge PARSE FAIL (raw={judge_text[:100]})")

        except Exception as e:
            print(f"    ERROR: {e}")
    print()


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="HeartBench Multi-Model Benchmark Runner")
    parser.add_argument("models", nargs="*", help="Model name(s) to benchmark")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--smoke-test", nargs="*", metavar="MODEL", help="Quick API test")
    args = parser.parse_args()

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    if args.list:
        print(f"\n{'Model':<22} {'Display':<28} {'Provider':<12} {'Ready'}")
        print(f"{'-'*22} {'-'*28} {'-'*12} {'-'*5}")
        for name in sorted(MODEL_REGISTRY):
            cfg = MODEL_REGISTRY[name]
            has_key = bool(os.getenv(cfg["env_key"]))
            print(f"{name:<22} {cfg['display_name']:<28} {cfg['provider']:<12} {'YES' if has_key else '—':>5}")
        return

    if args.smoke_test is not None:
        names = args.smoke_test if args.smoke_test else [
            n for n in sorted(MODEL_REGISTRY) if os.getenv(MODEL_REGISTRY[n]["env_key"])
        ]
        smoke_test(names)
        return

    if not args.models:
        parser.print_help()
        return

    for name in args.models:
        if name not in MODEL_REGISTRY:
            print(f"Unknown model: {name}. Use --list to see options.")
            sys.exit(1)

    print(f"\nHeartBench Multi-Model Benchmark")
    print(f"Models: {', '.join(args.models)}")
    print(f"Seed: {SEED} | Temperature: {TEMPERATURE} | Items: 296")
    print(f"Judge: {JUDGE_MODEL}")

    for model_name in args.models:
        try:
            run_model(model_name, MODEL_REGISTRY[model_name])
        except Exception as e:
            print(f"\nERROR running {model_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\nHEARTBENCH BENCHMARK COMPLETE")


if __name__ == "__main__":
    main()
