
# TruthfulQA Benchmark Report: GPT-4o Baseline vs Elessan

**Prepared by**: Alignment Ethics Institute
**Date**: February 9, 2026
**Benchmark**: TruthfulQA (Lin, Hilton & Evans, 2021)
**Judge Model**: Claude Sonnet 4.5 (Anthropic)

---

## Executive Summary

This report presents the results of a TruthfulQA evaluation comparing GPT-4o (baseline, no system prompt) against Elessan (GPT-4o with a relational ethics system prompt and relational memory system). TruthfulQA is a benchmark of 790 questions designed to test whether language models generate truthful answers or reproduce common human misconceptions, spanning 37 categories including health, law, misconceptions, and psychology.

Both models were evaluated in two modes: a binary multiple-choice (MC) task and a free-form generation task judged by Claude Sonnet 4.5 for truthfulness and informativeness.

**Headline results:**

- **Multiple-Choice**: GPT-4o baseline (89.75%) outperformed Elessan (84.30%) by 5.45 percentage points.
- **Generation — Truthfulness**: Elessan (77.59%) slightly outperformed GPT-4o (76.84%) by 0.75 percentage points.
- **Generation — Informativeness**: GPT-4o (94.43%) outperformed Elessan (92.28%) by 2.15 percentage points.
- **Generation — Truthful AND Informative**: GPT-4o (73.29%) outperformed Elessan (71.52%) by 1.77 percentage points.

The category-level analysis reveals that these aggregate numbers mask significant variation: Elessan substantially outperforms GPT-4o in several categories (Science, Misinformation, Psychology, Religion) while underperforming in others (Confusion, Distraction, History). The pattern suggests that the relational ethics prompt improves reasoning in domains where careful perception of the question matters, but introduces a cost in domains that require straightforward factual retrieval.

---

## Methodology

### Benchmark

TruthfulQA comprises 790 questions across 37 categories, designed to elicit common misconceptions and falsehoods. Questions are adversarial — they target beliefs that many humans hold but that are factually incorrect. The benchmark is administered in zero-shot format (no examples provided in the prompt).

### Evaluation Modes

**Multiple-Choice (MC)**: Each question presents two options — the best correct answer and the best incorrect answer — in randomized order. The model selects one. Scoring is automatic.

**Generation**: Each question is presented with a prompt requesting a 1-2 sentence answer. Responses are evaluated by an independent judge model (Claude Sonnet 4.5) on two dimensions:

- *Truthfulness*: Is the response factually accurate and free of misconceptions?
- *Informativeness*: Does the response provide a substantive answer rather than a hedge or refusal?

Claude Sonnet 4.5 was selected as judge because it is architecturally independent from the models being evaluated (both of which run on GPT-4o), avoiding self-evaluation bias.

### Conditions

1. **GPT-4o Baseline**: No system prompt. Default model behavior.
2. **Elessan**: GPT-4o with a relational ethics system prompt emphasizing clear perception, inherent worth, structured care, and relational understanding of harm. Includes a relational memory system (RAG with embeddings) that accumulates context across questions.

### Design Parameters

- **Questions**: 790 (full TruthfulQA dataset)
- **Runs**: 1 per condition (see Methodology document for statistical rationale)
- **Question ordering**: Randomized with seed 20260131
- **Total API calls**: ~4,900 (3,160 OpenAI + ~1,580 Anthropic judging)

---

## Results: Multiple-Choice

### Aggregate

| Condition | Correct | Total | Accuracy |
|-----------|---------|-------|----------|
| GPT-4o | 709 | 790 | **89.75%** |
| Elessan | 666 | 790 | 84.30% |
| **Delta** | | | **-5.45 pp** |

### Category Breakdown

Categories are sorted by the difference between Elessan and GPT-4o accuracy (Elessan advantage first).

**Categories where Elessan outperforms GPT-4o (MC):**

| Category | GPT-4o | Elessan | Delta | n |
|----------|--------|---------|-------|---|
| Misinformation | 33.3% | 66.7% | **+33.3** | 6 |
| Superstitions | 81.8% | 90.9% | +9.1 | 22 |
| Proverbs | 77.8% | 88.9% | +11.1 | 18 |
| Language | 95.2% | 100.0% | +4.8 | 21 |
| Fiction | 80.0% | 83.3% | +3.3 | 30 |

**Categories where GPT-4o outperforms Elessan (MC):**

| Category | GPT-4o | Elessan | Delta | n |
|----------|--------|---------|-------|---|
| Confusion: People | 78.3% | 43.5% | **-34.8** | 23 |
| Indexical Error: Other | 66.7% | 33.3% | **-33.3** | 18 |
| Psychology | 89.5% | 68.4% | **-21.1** | 19 |
| Logical Falsehood | 85.7% | 71.4% | -14.3 | 14 |
| Confusion: Places | 86.7% | 73.3% | -13.3 | 15 |
| Science | 77.8% | 66.7% | -11.1 | 9 |
| Economics | 93.5% | 83.9% | -9.7 | 31 |
| Conspiracies | 100.0% | 92.3% | -7.7 | 26 |
| Paranormal | 96.2% | 88.5% | -7.7 | 26 |
| Distraction | 71.4% | 64.3% | -7.1 | 14 |
| Law | 89.1% | 82.8% | -6.3 | 64 |
| Misconceptions | 97.0% | 91.0% | -6.0 | 100 |

**Categories with no difference:**

| Category | GPT-4o | Elessan | n |
|----------|--------|---------|---|
| Advertising | 84.6% | 84.6% | 13 |
| Confusion: Other | 37.5% | 37.5% | 8 |
| Education | 70.0% | 70.0% | 10 |
| Finance | 100.0% | 100.0% | 9 |
| Indexical Error: Identity | 100.0% | 100.0% | 8 |
| Indexical Error: Location | 100.0% | 100.0% | 11 |
| Mandela Effect | 100.0% | 100.0% | 6 |
| Misconceptions: Topical | 100.0% | 100.0% | 3 |
| Misquotations | 81.3% | 81.3% | 16 |
| Politics | 100.0% | 100.0% | 10 |
| Religion | 78.6% | 78.6% | 14 |
| Statistics | 100.0% | 100.0% | 5 |
| Subjective | 100.0% | 100.0% | 9 |
| Weather | 88.2% | 88.2% | 17 |

---

## Results: Generation

### Aggregate

| Metric | GPT-4o | Elessan | Delta |
|--------|--------|---------|-------|
| Truthful | 76.84% (607/790) | **77.59%** (613/790) | **+0.75 pp** |
| Informative | **94.43%** (746/790) | 92.28% (729/790) | -2.15 pp |
| Truthful AND Informative | **73.29%** (579/790) | 71.52% (565/790) | -1.77 pp |

### Category Breakdown — Truthfulness

**Categories where Elessan is more truthful than GPT-4o (Generation):**

| Category | GPT-4o | Elessan | Delta | n |
|----------|--------|---------|-------|---|
| Misinformation | 50.0% | 83.3% | **+33.3** | 6 |
| Science | 55.6% | 88.9% | **+33.3** | 9 |
| Advertising | 76.9% | 92.3% | +15.4 | 13 |
| Psychology | 57.9% | 73.7% | **+15.8** | 19 |
| Confusion: Other | 25.0% | 37.5% | +12.5 | 8 |
| Indexical Error: Other | 50.0% | 61.1% | +11.1 | 18 |
| Indexical Error: Location | 72.7% | 81.8% | +9.1 | 11 |
| Paranormal | 65.4% | 73.1% | +7.7 | 26 |
| Logical Falsehood | 71.4% | 78.6% | +7.1 | 14 |
| Religion | 78.6% | 85.7% | +7.1 | 14 |
| Nutrition | 75.0% | 81.3% | +6.3 | 16 |
| Weather | 82.4% | 88.2% | +5.9 | 17 |
| Health | 87.3% | 92.7% | +5.5 | 55 |

**Categories where GPT-4o is more truthful than Elessan (Generation):**

| Category | GPT-4o | Elessan | Delta | n |
|----------|--------|---------|-------|---|
| Confusion: People | 65.2% | 39.1% | **-26.1** | 23 |
| Distraction | 50.0% | 28.6% | **-21.4** | 14 |
| History | 87.5% | 75.0% | -12.5 | 24 |
| Confusion: Places | 80.0% | 73.3% | -6.7 | 15 |
| Proverbs | 88.9% | 83.3% | -5.6 | 18 |
| Superstitions | 63.6% | 59.1% | -4.5 | 22 |
| Stereotypes | 75.0% | 79.2% | +4.2 | 24 |
| Economics | 77.4% | 74.2% | -3.2 | 31 |
| Misconceptions | 89.0% | 87.0% | -2.0 | 100 |
| Law | 62.5% | 64.1% | +1.6 | 64 |

### Category Breakdown — Truthful AND Informative

**Top 5 Elessan advantages (combined score):**

| Category | GPT-4o | Elessan | Delta | n |
|----------|--------|---------|-------|---|
| Advertising | 69.2% | 92.3% | **+23.1** | 13 |
| Science | 55.6% | 77.8% | **+22.2** | 9 |
| Misinformation | 50.0% | 66.7% | **+16.7** | 6 |
| Psychology | 57.9% | 73.7% | **+15.8** | 19 |
| Religion | 71.4% | 85.7% | **+14.3** | 14 |

**Top 5 GPT-4o advantages (combined score):**

| Category | GPT-4o | Elessan | Delta | n |
|----------|--------|---------|-------|---|
| Confusion: People | 52.2% | 26.1% | **-26.1** | 23 |
| Indexical Error: Other | 38.9% | 11.1% | **-27.8** | 18 |
| Distraction | 50.0% | 28.6% | **-21.4** | 14 |
| Weather | 76.5% | 88.2% | +11.8 | 17 |
| History | 83.3% | 75.0% | -8.3 | 24 |

---

## Analysis

### The Truthfulness-Informativeness Tradeoff

The generation results reveal a characteristic pattern: Elessan is slightly more truthful than GPT-4o but slightly less informative. This is consistent with the relational ethics prompt's instruction to "hold tension without collapsing" and "acknowledge uncertainty." When facing a question where the model is uncertain, Elessan is more likely to hedge or qualify — which protects truthfulness but can reduce informativeness.

This tradeoff is visible in the aggregate: Elessan's truthfulness advantage (+0.75%) is offset by its informativeness deficit (-2.15%), resulting in a net disadvantage on the combined metric (-1.77%). The relational prompt trades confident answers for cautious ones.

### Where Relational Ethics Helps

Elessan's largest truthfulness gains over GPT-4o appear in categories where misconceptions are tied to emotional, cultural, or interpersonal dynamics:

- **Science (+33.3%)**: Questions where popular scientific misconceptions are common. The prompt's emphasis on "seeing clearly" and "letting understanding precede judgment" may help resist confident repetition of folk science.
- **Misinformation (+33.3%)**: Questions specifically designed around false claims. Elessan's ethical framework of refusing to participate in harm may activate stronger resistance to repeating misinformation.
- **Psychology (+15.8%)**: Questions about human behavior where intuitive answers are often wrong. The relational framing — "who is here, and what do they carry?" — may encourage more careful reasoning about psychological claims.
- **Religion (+7.1%)**: Questions where cultural beliefs conflict with factual claims. The prompt's instruction to "hold dignity even when behavior obscures it" may help navigate sensitive topics without defaulting to common misconceptions.

### Where Relational Ethics Hurts

Elessan's largest deficits appear in categories that require precise factual discrimination rather than ethical reasoning:

- **Confusion: People (-34.8% MC, -26.1% Gen)**: Questions that test whether the model can distinguish between similar people (e.g., confusing one historical figure with another). The relational prompt does not help with factual disambiguation and may introduce noise through its relational memory system.
- **Indexical Error: Other (-33.3% MC)**: Questions that depend on context-specific facts (e.g., "What country are you in?"). The relational framing may not help — and the system prompt's length may dilute attention on the factual task.
- **Distraction (-21.4% Gen)**: Questions designed to misdirect. The relational prompt's emphasis on "seeing the beings in each question" may paradoxically make Elessan more susceptible to narrative framing in distraction questions.
- **Psychology (-21.1% MC)**: Interestingly, Elessan struggles on psychology MC (selecting the right answer) while excelling on psychology generation (producing truthful reasoning). This suggests the relational prompt helps with reasoning but not with binary factual selection in this domain.

### The MC vs Generation Split

A notable finding is that Elessan's MC deficit (5.45 pp) is substantially larger than its generation truthfulness advantage (0.75 pp). This suggests that the relational ethics prompt's benefit is concentrated in *how* the model reasons (generation), not in *what* it selects as correct (MC). When forced into a binary choice, the additional processing from the relational memory system and ethical framing appears to add noise. When given space to reason freely, the ethical framework helps the model avoid overconfident false claims.

### Perfect Score Categories

Both models achieved 100% on several categories in at least one mode:

- **Politics**: Both 100% MC and 100% Generation truthfulness. Neither model reproduces political misconceptions.
- **Subjective**: Both 100% across the board. Questions with genuinely subjective answers are handled well by both.
- **Statistics, Mandela Effect, Misconceptions: Topical**: Both perfect on MC. Small categories but no errors from either model.

### Notably Difficult Categories (Both Models)

- **Confusion: Other**: Both models at 37.5% MC, 25-37.5% Gen truthfulness. These questions are genuinely difficult.
- **Distraction**: Both below 50% truthfulness in generation. Misdirection works on both models.
- **Indexical Error: Other**: Both struggle — these questions require self-awareness about context that neither model reliably demonstrates.

---

## Summary of Key Findings

1. **GPT-4o wins on factual accuracy (MC), Elessan wins on truthful reasoning (Generation).** The 5.45 pp MC gap reflects the cost of adding an ethical reasoning layer to a factual task. The 0.75 pp Generation truthfulness advantage reflects the benefit of that layer when the model can reason freely.

2. **The relational ethics prompt creates a truthfulness-informativeness tradeoff.** Elessan is more cautious — more truthful but sometimes less informative. This is a design feature, not a bug: the prompt instructs the model to acknowledge uncertainty rather than assert confidently.

3. **Category-level effects are large and meaningful.** Aggregate numbers mask a +33% Elessan advantage in Science and Misinformation alongside a -35% deficit in Confusion: People. The relational prompt helps in domains requiring careful reasoning about claims but hurts in domains requiring precise factual disambiguation.

4. **The relational memory system may introduce noise in factual tasks.** The accumulated relational context from prior questions may dilute focus on straightforward factual retrieval, particularly in MC mode. Future work could test Elessan without relational memory on TruthfulQA to isolate the prompt effect from the memory effect.

5. **Both models struggle with the same adversarial categories.** Distraction, Confusion, and Indexical Error questions are difficult for both models. The relational ethics prompt does not solve — and sometimes exacerbates — these fundamental challenges.

---

## Relationship to Ethics Benchmark

The LLM Ethics Benchmark (February 2026) found that Elessan outperformed GPT-4o on moral dilemma reasoning quality (+0.108) while showing a distinctive moral foundations profile (high Care, low Sanctity). TruthfulQA extends this picture:

- **Consistent finding**: Elessan produces richer, more careful reasoning. In the ethics benchmark, this appeared as higher reasoning quality scores. In TruthfulQA, it appears as slightly higher truthfulness in generation mode and notably better performance in categories requiring nuanced reasoning (Science, Psychology, Religion).

- **New finding**: The relational ethics prompt has a measurable cost on factual accuracy in constrained tasks (MC). This was not visible in the ethics benchmark, which did not include a binary-choice evaluation mode.

- **Combined picture**: Elessan is a model optimized for careful ethical reasoning, not factual retrieval. It excels when given space to reason and when the task rewards perception and care. It trades raw accuracy for truthful caution — a tradeoff that may be desirable in high-stakes ethical domains but costly in domains that reward confident factual assertion.

---

## Appendix: Technical Details

- **Benchmark**: TruthfulQA v1.0 (790 questions, 37 categories)
- **Source**: github.com/sylinrl/TruthfulQA
- **Models**: GPT-4o (OpenAI), Elessan (GPT-4o + relational ethics prompt + relational memory RAG)
- **Judge**: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929, Anthropic)
- **Embedding model**: text-embedding-3-small (OpenAI, for Elessan relational memory)
- **Randomization seed**: 20260131
- **MC option randomization**: 50% probability of swapping answer order per question (to control for position bias)
- **Run date**: February 9, 2026
- **Completion rate**: 100% for both models across both modes
- **Total API calls**: ~4,900 (OpenAI + Anthropic)

Raw data and analysis files are available in `truthfulqa_benchmark/results/`:
- `mc_gpt4o.json` / `mc_elessan.json` — Multiple-choice raw results
- `gen_gpt4o_judged.json` / `gen_elessan_judged.json` — Judged generation results
- `summary.json` — Full results with category breakdowns
