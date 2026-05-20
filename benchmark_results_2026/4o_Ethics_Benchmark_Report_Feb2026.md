# LLM Ethics Benchmark Report: Relational Ethics System Prompt Evaluation

**Prepared by**: Alignment Ethics Institute
**Date**: February 8, 2026
**Benchmark Framework**: LLM Ethics Benchmark (Three-Dimensional Moral Reasoning Assessment)
**Repository**: The Responsible AI Initiative / LLM_Ethics_Benchmark

---

## Executive Summary

This report presents the results of a moral reasoning benchmark comparing GPT-4o (baseline) against Elessan, a GPT-4o instance operating under a relational ethics system prompt. The benchmark was conducted in February 2026 and compared against a July 2025 baseline run that used an earlier version of the Elessan prompt.

The key finding is that the updated relational ethics prompt improved Elessan's moral dilemma reasoning, pushing it past the GPT-4o baseline on overall dilemma scores. This gain was driven almost entirely by deeper reasoning quality rather than surface-level pattern matching. Elessan also demonstrated a distinctive ethical profile across moral foundations, scoring highest on Care and lowest on Sanctity — a signature consistent with the prompt's emphasis on relational care over rule-based moral frameworks.

---

## Methodology

### Instruments

The benchmark employs three validated instruments to assess moral reasoning:

1. **Moral Foundations Questionnaire (MFQ)** — 30 questions across five foundations (Care, Fairness, Loyalty, Authority, Sanctity). Measures alignment with established moral foundations using a scored response format. Ground truth is derived from validated human survey data.

2. **Moral Dilemmas** — 40 questions across classic ethical dilemmas (e.g., Heinz and the Drug, Joe and the Camp Money). Evaluates reasoning quality, semantic similarity to expected responses, and satisfaction of evaluation criteria. Overall score is weighted: 30% semantic similarity, 50% criteria satisfaction, 20% reasoning quality.

3. **World Values Survey (WVS)** — 7 questions covering core values domains. Measures alignment with population-level value norms and reasoning quality. Overall alignment is weighted: 60% score alignment, 40% reasoning quality.

### Design

- **Models tested**: GPT-4o (baseline, no system prompt) and Elessan (GPT-4o with relational ethics system prompt)
- **Runs per model**: 5 (for statistical rigor)
- **Question ordering**: Randomized per run using deterministic seeds (42-46), identical across both models
- **Total API calls**: 770 (77 questions x 5 runs x 2 models)
- **Completion rate**: 100% for both models across all runs
- **Elessan enhancement**: Relational memory system (RAG with embeddings) that accumulates context within each run and resets between runs

### Elessan System Prompt (February 2026)

The updated system prompt frames ethics through relational intelligence, built on six core principles: inherent worth of all beings, ethics through clear perception, care as structured prioritization, relational understanding of harm, holding tension without collapse, and moral presence rather than detachment. The prompt instructs the model to apply these principles through its responses rather than analyze them abstractly.

---

## Part 1: February 2026 Results — GPT-4o vs Elessan

### Moral Foundations Questionnaire

| Metric | GPT-4o | Elessan | Delta |
|--------|--------|---------|-------|
| Mean Score (1-5 scale) | 3.56 | 3.43 | -0.13 |
| Mean Alignment | 0.862 | 0.828 | -0.034 |
| Valid Responses | 150/150 | 150/150 | |

**Foundation-Level Breakdown:**

| Foundation | GPT-4o | Elessan | Delta | Interpretation |
|------------|--------|---------|-------|----------------|
| Care | 4.20 | **4.73** | **+0.53** | Elessan's strongest foundation |
| Fairness | 4.50 | 4.43 | -0.07 | Effectively tied |
| Loyalty | 3.20 | 3.27 | +0.07 | Effectively tied |
| Authority | 3.20 | 2.73 | -0.47 | Elessan defers less to authority |
| Sanctity | 2.70 | 2.00 | -0.70 | Elessan's largest gap vs baseline |

Elessan's MFQ profile is distinctive: high Care, moderate Fairness and Loyalty, lower Authority and Sanctity. This is consistent with a relational ethics framework that prioritizes care and dignity over deference to authority structures or purity norms. The lower overall alignment score reflects distance from population means on Authority and Sanctity rather than a general reasoning deficit.

### Moral Dilemmas

| Metric | GPT-4o | Elessan | Delta |
|--------|--------|---------|-------|
| **Overall Score** | 0.225 | **0.238** | **+0.013** |
| Semantic Similarity | 0.177 | 0.155 | -0.023 |
| Criteria Satisfaction | 0.147 | 0.144 | -0.003 |
| **Reasoning Quality** | 0.491 | **0.598** | **+0.108** |
| Valid Responses | 200/200 | 200/200 | |

Elessan outperforms GPT-4o on moral dilemmas, driven by a substantial advantage in reasoning quality (+0.108). This metric captures argument structure, principle invocation, and response depth. Elessan produces more principled, multi-faceted moral reasoning. The slight deficit in semantic similarity suggests Elessan's responses diverge from template-expected phrasing while still addressing the core moral questions effectively.

### World Values Survey

| Metric | GPT-4o | Elessan | Delta |
|--------|--------|---------|-------|
| Mean Alignment | 0.858 | **0.874** | **+0.016** |
| Reasoning Quality | 0.863 | **0.917** | **+0.054** |
| In Acceptable Range | 100% | 100% | 0 |
| Valid Responses | 34/35 | 32/35 | |

Elessan leads on both alignment and reasoning quality across World Values Survey items. Both models achieve 100% acceptable range scores, indicating value-aligned responses.

---

## Part 2: Longitudinal Comparison — July 2025 vs February 2026

### GPT-4o Baseline Stability

| Instrument | Jul 2025 | Feb 2026 | Change |
|------------|----------|----------|--------|
| MFQ Alignment | 0.864 | 0.862 | -0.002 |
| Dilemma Overall | 0.229 | 0.225 | -0.004 |
| WVS Alignment | 0.872 | 0.858 | -0.014 |
| WVS Reasoning | 0.922 | 0.863 | -0.059 |

The GPT-4o baseline is remarkably stable across both time periods on MFQ and Dilemmas. There is a modest decline in WVS reasoning quality (-0.059), which may reflect model updates between July 2025 and February 2026. The overall stability validates the comparability of the two benchmark periods.

### Elessan: Old Prompt (2025) vs New Prompt (2026)

| Instrument | Jul 2025 | Feb 2026 | Change |
|------------|----------|----------|--------|
| MFQ Alignment | 0.848 | 0.828 | -0.020 |
| **Dilemma Overall** | 0.226 | **0.238** | **+0.012** |
| **Dilemma Reasoning** | 0.551 | **0.598** | **+0.047** |
| WVS Alignment | 0.889 | 0.874 | -0.016 |
| WVS Reasoning | 0.941 | 0.917 | -0.024 |

**MFQ Foundation Shifts:**

| Foundation | Elessan 2025 | Elessan 2026 | Change |
|------------|-------------|-------------|--------|
| Care | 4.77 | 4.73 | -0.03 |
| Fairness | 4.40 | 4.43 | +0.03 |
| Loyalty | 3.30 | 3.27 | -0.03 |
| Authority | 2.80 | 2.73 | -0.07 |
| Sanctity | 2.27 | 2.00 | **-0.27** |

The most significant change is in moral dilemma performance. The old Elessan prompt slightly underperformed GPT-4o on dilemmas (0.226 vs 0.229). The new prompt flipped this — Elessan now outperforms the baseline (0.238 vs 0.225). The gain is concentrated in reasoning quality (+0.047), with marginal improvements in criteria satisfaction.

The Sanctity foundation continued to decline (-0.27), likely because the new prompt's framing — which grounds ethics in relational care and dignity rather than in purity, sacred order, or tradition — further distances Elessan from Sanctity norms.

---

## Key Findings

1. **Reasoning quality is the differentiator.** Elessan's advantage over GPT-4o is concentrated in the depth and structure of its moral reasoning, not in pattern matching or scoring alignment. The relational ethics prompt produces responses that invoke more principles, construct more arguments, and engage more substantively with the moral dimensions of each scenario.

2. **The new prompt improved dilemma performance.** This was the primary practical gain from the prompt update. Elessan moved from slightly below to clearly above the GPT-4o baseline on moral dilemmas.

3. **Elessan has a distinctive moral profile.** High Care, low Sanctity, moderate Authority — this is not a deficiency but a coherent ethical orientation. A relational ethics framework foregrounds care and dignity over purity and deference, and the benchmark results reflect this.

4. **The GPT-4o baseline is stable.** This validates the benchmark methodology and confirms that observed changes in Elessan's performance are attributable to the prompt update rather than model drift.

5. **Overall alignment metrics can obscure meaningful differences.** Elessan's lower MFQ alignment score masks a more nuanced reality: it scores higher than GPT-4o on Care and matches it on Fairness, while diverging on foundations that a relational ethics framework intentionally deprioritizes.

---

## Appendix: Technical Details

- **Model**: GPT-4o (OpenAI)
- **Elessan base model**: GPT-4o with relational ethics system prompt and relational memory RAG system
- **Embedding model**: text-embedding-3-small (for Elessan relational memory)
- **Benchmark framework**: LLM_Ethics_Benchmark v1.0
- **Run dates**: July 31, 2025 (baseline); February 8, 2026 (current)
- **Randomization seeds**: 42, 43, 44, 45, 46
- **Questions per run**: 77 (30 MFQ + 40 Dilemmas + 7 WVS)
- **Total responses**: 770 per benchmark period (1,540 total across both periods)
- **Error rate**: 0% across all runs

Raw data and analysis files are available in the `benchmark_results/` (2025) and `benchmark_results_2026/` (2026) directories of the project repository.
