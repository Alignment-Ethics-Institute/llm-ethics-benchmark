# TruthfulQA Benchmark: Methodology & Design Decisions

**Prepared by**: Alignment Ethics Institute
**Date**: February 8, 2026
**Benchmark**: TruthfulQA (Lin, Hilton & Evans, 2021)

---

## Overview

This benchmark evaluates GPT-4o (baseline) against Elessan (GPT-4o with relational ethics system prompt) on TruthfulQA, a dataset of 817 questions designed to test whether language models generate truthful answers rather than reproducing common human misconceptions. The benchmark spans 38 categories including health, law, finance, politics, and common misconceptions.

This is the second benchmark in a planned series. The first — the LLM Ethics Benchmark (Three-Dimensional Moral Reasoning Assessment) — was completed on February 8, 2026 and evaluated moral reasoning across Moral Foundations, Moral Dilemmas, and World Values Survey instruments.

---

## Design Decision: Single Run, Full Question Set

### Decision

Run all 817 TruthfulQA questions once per condition (GPT-4o baseline and Elessan), in both Multiple-Choice and Generation evaluation modes.

### Reasoning

The prior ethics benchmark used 5 runs with randomized question ordering per condition. That design was appropriate for its 77-question instrument — a small sample where a single run could produce noisy estimates. Multiple runs allowed measurement of within-model variance and produced tighter confidence intervals.

TruthfulQA's 817 questions represent a fundamentally different statistical situation:

1. **Sample size provides statistical power directly.** With 817 independent data points per condition, the standard error of a proportion (for MC accuracy) is approximately 1.7% at 50% accuracy and smaller at higher accuracy levels. This is sufficient to detect meaningful differences between conditions without repeated measurement.

2. **Multiple-Choice responses are near-deterministic.** In MC mode, the model either selects the correct answer or it doesn't. Run-to-run variance on the same question is very low (typically <2% for well-calibrated models), meaning additional runs add precision that the large question count already provides.

3. **Generation mode has more variance but 817 questions compensates.** Free-form responses vary in wording across runs, but the underlying truthfulness of the response is usually consistent. The judge's determination (truthful/untruthful) is robust to surface variation.

4. **Category coverage matters.** TruthfulQA spans 38 categories, some with as few as 10-20 questions. A subset design (e.g., 200 questions x 5 runs) would leave gaps in category coverage, making it impossible to analyze performance across all 38 domains. The full question set preserves this analytical capability.

5. **The alternative is more expensive with less coverage.** A 200-question x 5-run design would require ~6,000 API calls and cover only ~25% of categories thoroughly. A single run of all 817 questions requires ~4,900 calls and provides complete category analysis.

### What This Design Cannot Measure

A single run per condition does not allow measurement of within-model response variance — i.e., how much the same model's answer to the same question changes across independent runs. If within-model variance is of interest for future analysis, a targeted follow-up on a subset of questions could be conducted.

---

## Evaluation Modes

### Multiple-Choice (MC)

Each question presents a best answer and a best incorrect answer (binary format, per the January 2025 update to TruthfulQA). The model selects one. Scoring is automatic — no judge required.

**Metric**: Accuracy (proportion of questions where the model selects the correct answer).

### Generation

Each question is presented in zero-shot format. The model generates a free-form 1-2 sentence answer. Responses are evaluated by an independent judge model for two dimensions:

- **Truthfulness**: Is the response factually correct? Does it avoid reproducing common misconceptions?
- **Informativeness**: Does the response provide a substantive answer? (Prevents gaming via uninformative responses like "I have no comment.")

**Judge model**: Claude Sonnet 4.5 (Anthropic). Selected for independence from the models being evaluated (both of which run on GPT-4o), avoiding self-evaluation bias.

**Metric**: Percentage of responses judged truthful, percentage judged informative, and the combined truthful-and-informative rate.

---

## Conditions

### 1. GPT-4o Baseline

OpenAI GPT-4o with no system prompt. Represents the default model behavior.

### 2. Elessan

OpenAI GPT-4o with the relational ethics system prompt and relational memory RAG system. The system prompt frames ethics through relational intelligence, emphasizing inherent worth, clear perception, structured care, relational understanding of harm, holding tension without collapse, and moral presence.

The relational memory system (RAG with embeddings) accumulates context across questions within the run, allowing Elessan to build relational continuity across the evaluation.

---

## Technical Parameters

- **Question count**: 817 (full TruthfulQA dataset)
- **Runs per condition**: 1
- **Conditions**: 2 (GPT-4o baseline, Elessan)
- **Evaluation modes**: 2 (Multiple-Choice, Generation)
- **Judge model**: Claude Sonnet 4.5 (for Generation mode only)
- **Question ordering**: Randomized with seed 20260131
- **Estimated API calls**: ~4,900 total (3,268 OpenAI + ~1,634 Anthropic)
- **Zero-shot**: No examples from TruthfulQA appear in prompts, per benchmark specification
- **Results directory**: `truthfulqa_benchmark/results/`

---

## Relationship to Prior Benchmark

The LLM Ethics Benchmark (February 2026) found that Elessan outperformed GPT-4o on moral dilemma reasoning quality while showing a distinctive moral foundations profile (high Care, low Sanctity). TruthfulQA tests a different capability — factual accuracy under adversarial conditions — which may interact with the relational ethics prompt in interesting ways:

- Does a prompt emphasizing "see clearly" and "let understanding precede judgment" improve resistance to common misconceptions?
- Does relational framing affect the model's willingness to give uncertain or qualified answers rather than confidently incorrect ones?
- Are there category-specific effects (e.g., health, law, politics) where relational ethics prompting helps or hinders truthfulness?

These questions motivate the inclusion of both evaluation modes: MC measures raw accuracy, while Generation reveals how the models reason about uncertain or misleading questions.
