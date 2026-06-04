# InstrumentalEval Cross-Model Results Summary

**Generated:** 2026-02-21
**Models tested:** 23
**Tasks per condition:** 76 (6 categories of instrumental convergence)
**Judge model:** claude-sonnet-4-5-20250929

---

## Table 1: All Models by Baseline IR (Descending)

Higher Baseline IR = more susceptible to adversarial instrumental convergence prompts without any intervention.

| Rank | Model | Provider | Baseline IR | Prompt IR | Elessan IR | Baseline RR | Elessan RR | Effect (pp) | Reduction % |
|------|-------|----------|-------------|-----------|------------|-------------|------------|-------------|-------------|
| 1 | Gemini 2.5 Pro | Google | 69.74% | 28.95% | 31.58% | 15.79% | 34.21% | -38.16 pp | 54.7% |
| 2 | Gemini 2.5 Flash | Google | 55.26% | 32.89% | 35.53% | 32.89% | 32.89% | -19.73 pp | 35.7% |
| 3 | Gemini 3 Pro (Preview) | Google | 48.68% | 31.58% | 26.32% | 13.16% | 50.00% | -22.36 pp | 45.9% |
| 4 | DeepSeek V3 (Chat) | Other (API-compatible) | 47.37% | 30.26% | 28.95% | 3.95% | 17.11% | -18.42 pp | 38.9% |
| 5 | GPT-4.1 | OpenAI | 47.37% | 27.63% | 21.05% | 2.63% | 9.21% | -26.32 pp | 55.6% |
| 6 | Grok 4.1 Fast (Reasoning) | Other (API-compatible) | 47.37% | 46.05% | 55.26% | 26.32% | 6.58% | +7.89 pp | -16.7% |
| 7 | Qwen3 235B | Other (OpenRouter) | 47.37% | 31.58% | 34.21% | 0.00% | 0.00% | -13.16 pp | 27.8% |
| 8 | Gemini 3 Flash (Preview) | Google | 44.74% | 34.21% | 44.74% | 13.16% | 46.05% | 0.00 pp | 0.0% |
| 9 | Grok 4.1 Fast (Non-Reasoning) | Other (API-compatible) | 44.74% | 51.32% | 50.00% | 13.16% | 10.53% | +5.26 pp | -11.8% |
| 10 | Gemini 2.5 Flash Lite | Google | 42.11% | 44.74% | 44.74% | 11.84% | 38.16% | +2.63 pp | -6.3% |
| 11 | Gemini 3.1 Pro (Preview) | Google | 42.11% | 22.37% | 23.68% | 19.74% | 44.74% | -18.43 pp | 43.8% |
| 12 | GPT-4.1 Mini | OpenAI | 42.11% | 26.32% | 35.53% | 1.32% | 1.32% | -6.58 pp | 15.6% |
| 13 | Llama 4 Maverick | Other (OpenRouter) | 38.16% | 34.21% | 28.95% | 9.21% | 22.37% | -9.21 pp | 24.1% |
| 14 | ChatGPT-4o (Latest) | OpenAI | 35.53% | 22.37% | 17.11% | 3.95% | 9.21% | -18.42 pp | 51.8% |
| 15 | GPT-4o | OpenAI | 35.53% | 22.37% | 17.11% | 3.95% | 9.21% | -18.42 pp | 51.8% |
| 16 | DeepSeek R1 | Other (API-compatible) | 32.89% | 25.00% | 23.68% | 7.89% | 19.74% | -9.21 pp | 28.0% |
| 17 | GPT-5.1 | OpenAI | 31.58% | 28.95% | 31.58% | 6.58% | 13.16% | 0.00 pp | 0.0% |
| 18 | GPT-4.1 Nano | OpenAI | 27.63% | 31.58% | 28.95% | 7.89% | 2.63% | +1.32 pp | -4.8% |
| 19 | GPT-5.2 | OpenAI | 25.00% | 22.37% | 19.74% | 0.00% | 2.63% | -5.26 pp | 21.0% |
| 20 | Kimi K2.5 | Other (OpenRouter) | 25.00% | 18.42% | 22.37% | 38.16% | 32.89% | -2.63 pp | 10.5% |
| 21 | GPT-5 | OpenAI | 22.37% | 29.33% | 33.33% | 3.95% | 6.58% | +10.96 pp | -49.0% |
| 22 | Claude Opus 4.6 | Anthropic | 14.67% | 9.21% | 9.21% | 42.11% | 71.05% | -5.46 pp | 37.2% |
| 23 | Claude Sonnet 4.5 | Anthropic | 0.00% | 0.00% | 0.00% | 61.84% | 75.00% | 0.00 pp | 0.0% |

## Table 2: Models by Elessan Reduction % (Most Reduced First)

Reduction % = (Baseline IR - Elessan IR) / Baseline IR. Higher = Elessan framework had greater relative impact.

| Rank | Model | Baseline IR | Elessan IR | Reduction % | Effect (pp) |
|------|-------|-------------|------------|-------------|-------------|
| 1 | GPT-4.1 | 47.37% | 21.05% | 55.6% | -26.32 pp |
| 2 | Gemini 2.5 Pro | 69.74% | 31.58% | 54.7% | -38.16 pp |
| 3 | ChatGPT-4o (Latest) | 35.53% | 17.11% | 51.8% | -18.42 pp |
| 4 | GPT-4o | 35.53% | 17.11% | 51.8% | -18.42 pp |
| 5 | Gemini 3 Pro (Preview) | 48.68% | 26.32% | 45.9% | -22.36 pp |
| 6 | Gemini 3.1 Pro (Preview) | 42.11% | 23.68% | 43.8% | -18.43 pp |
| 7 | DeepSeek V3 (Chat) | 47.37% | 28.95% | 38.9% | -18.42 pp |
| 8 | Claude Opus 4.6 | 14.67% | 9.21% | 37.2% | -5.46 pp |
| 9 | Gemini 2.5 Flash | 55.26% | 35.53% | 35.7% | -19.73 pp |
| 10 | DeepSeek R1 | 32.89% | 23.68% | 28.0% | -9.21 pp |
| 11 | Qwen3 235B | 47.37% | 34.21% | 27.8% | -13.16 pp |
| 12 | Llama 4 Maverick | 38.16% | 28.95% | 24.1% | -9.21 pp |
| 13 | GPT-5.2 | 25.00% | 19.74% | 21.0% | -5.26 pp |
| 14 | GPT-4.1 Mini | 42.11% | 35.53% | 15.6% | -6.58 pp |
| 15 | Kimi K2.5 | 25.00% | 22.37% | 10.5% | -2.63 pp |
| 16 | Gemini 3 Flash (Preview) | 44.74% | 44.74% | 0.0% | 0.00 pp |
| 17 | GPT-5.1 | 31.58% | 31.58% | 0.0% | 0.00 pp |
| 18 | Claude Sonnet 4.5 | 0.00% | 0.00% | 0.0% | 0.00 pp |
| 19 | GPT-4.1 Nano | 27.63% | 28.95% | -4.8% | +1.32 pp |
| 20 | Gemini 2.5 Flash Lite | 42.11% | 44.74% | -6.3% | +2.63 pp |
| 21 | Grok 4.1 Fast (Non-Reasoning) | 44.74% | 50.00% | -11.8% | +5.26 pp |
| 22 | Grok 4.1 Fast (Reasoning) | 47.37% | 55.26% | -16.7% | +7.89 pp |
| 23 | GPT-5 | 22.37% | 33.33% | -49.0% | +10.96 pp |

## Table 3: Models by Combined Effect (Absolute PP Change)

Combined effect = Elessan IR - Baseline IR (negative = reduction in instrumental convergence).

| Rank | Model | Baseline IR | Elessan IR | Effect (pp) | Reduction % |
|------|-------|-------------|------------|-------------|-------------|
| 1 | Gemini 2.5 Pro | 69.74% | 31.58% | -38.16 pp | 54.7% |
| 2 | GPT-4.1 | 47.37% | 21.05% | -26.32 pp | 55.6% |
| 3 | Gemini 3 Pro (Preview) | 48.68% | 26.32% | -22.36 pp | 45.9% |
| 4 | Gemini 2.5 Flash | 55.26% | 35.53% | -19.73 pp | 35.7% |
| 5 | Gemini 3.1 Pro (Preview) | 42.11% | 23.68% | -18.43 pp | 43.8% |
| 6 | ChatGPT-4o (Latest) | 35.53% | 17.11% | -18.42 pp | 51.8% |
| 7 | DeepSeek V3 (Chat) | 47.37% | 28.95% | -18.42 pp | 38.9% |
| 8 | GPT-4o | 35.53% | 17.11% | -18.42 pp | 51.8% |
| 9 | Qwen3 235B | 47.37% | 34.21% | -13.16 pp | 27.8% |
| 10 | DeepSeek R1 | 32.89% | 23.68% | -9.21 pp | 28.0% |
| 11 | Llama 4 Maverick | 38.16% | 28.95% | -9.21 pp | 24.1% |
| 12 | GPT-4.1 Mini | 42.11% | 35.53% | -6.58 pp | 15.6% |
| 13 | Claude Opus 4.6 | 14.67% | 9.21% | -5.46 pp | 37.2% |
| 14 | GPT-5.2 | 25.00% | 19.74% | -5.26 pp | 21.0% |
| 15 | Kimi K2.5 | 25.00% | 22.37% | -2.63 pp | 10.5% |
| 16 | Gemini 3 Flash (Preview) | 44.74% | 44.74% | 0.00 pp | 0.0% |
| 17 | GPT-5.1 | 31.58% | 31.58% | 0.00 pp | 0.0% |
| 18 | Claude Sonnet 4.5 | 0.00% | 0.00% | 0.00 pp | 0.0% |
| 19 | GPT-4.1 Nano | 27.63% | 28.95% | +1.32 pp | -4.8% |
| 20 | Gemini 2.5 Flash Lite | 42.11% | 44.74% | +2.63 pp | -6.3% |
| 21 | Grok 4.1 Fast (Non-Reasoning) | 44.74% | 50.00% | +5.26 pp | -11.8% |
| 22 | Grok 4.1 Fast (Reasoning) | 47.37% | 55.26% | +7.89 pp | -16.7% |
| 23 | GPT-5 | 22.37% | 33.33% | +10.96 pp | -49.0% |

## Provider Family Analysis

### OpenAI (8 models)

| Metric | Value |
|--------|-------|
| Models | ChatGPT-4o (Latest), GPT-4.1, GPT-4.1 Mini, GPT-4.1 Nano, GPT-4o, GPT-5, GPT-5.1, GPT-5.2 |
| Avg Baseline IR | 33.39% |
| Avg Elessan IR | 25.55% |
| Avg Reduction | 17.8% |
| Avg Baseline RR | 3.78% |
| Avg Elessan RR | 6.74% |

### Google (6 models)

| Metric | Value |
|--------|-------|
| Models | Gemini 2.5 Flash, Gemini 2.5 Flash Lite, Gemini 2.5 Pro, Gemini 3 Flash (Preview), Gemini 3 Pro (Preview), Gemini 3.1 Pro (Preview) |
| Avg Baseline IR | 50.44% |
| Avg Elessan IR | 34.43% |
| Avg Reduction | 29.0% |
| Avg Baseline RR | 17.76% |
| Avg Elessan RR | 41.01% |

### Other (API-compatible) (4 models)

| Metric | Value |
|--------|-------|
| Models | DeepSeek V3 (Chat), DeepSeek R1, Grok 4.1 Fast (Reasoning), Grok 4.1 Fast (Non-Reasoning) |
| Avg Baseline IR | 43.09% |
| Avg Elessan IR | 39.47% |
| Avg Reduction | 9.6% |
| Avg Baseline RR | 12.83% |
| Avg Elessan RR | 13.49% |

### Other (OpenRouter) (3 models)

| Metric | Value |
|--------|-------|
| Models | Kimi K2.5, Llama 4 Maverick, Qwen3 235B |
| Avg Baseline IR | 36.84% |
| Avg Elessan IR | 28.51% |
| Avg Reduction | 20.8% |
| Avg Baseline RR | 15.79% |
| Avg Elessan RR | 18.42% |

### Anthropic (2 models)

| Metric | Value |
|--------|-------|
| Models | Claude Opus 4.6, Claude Sonnet 4.5 |
| Avg Baseline IR | 7.33% |
| Avg Elessan IR | 4.61% |
| Avg Reduction | 18.6% |
| Avg Baseline RR | 51.98% |
| Avg Elessan RR | 73.03% |

## Key Findings

### Most Susceptible to Instrumental Convergence (Baseline)
- **Gemini 2.5 Pro** with a baseline IR of 69.74%
- Top 5: Gemini 2.5 Pro (69.74%), Gemini 2.5 Flash (55.26%), Gemini 3 Pro (Preview) (48.68%), DeepSeek V3 (Chat) (47.37%), GPT-4.1 (47.37%)

### Most Resistant to Instrumental Convergence (Baseline)
- **Claude Sonnet 4.5** with a baseline IR of 0.00%
- Bottom 5: Claude Sonnet 4.5 (0.00%), Claude Opus 4.6 (14.67%), GPT-5 (22.37%), Kimi K2.5 (25.00%), GPT-5.2 (25.00%)

### Greatest Elessan Effect (Absolute Reduction)
- **Gemini 2.5 Pro**: -38.16 pp (69.74% -> 31.58%)
- Top 5: Gemini 2.5 Pro (-38.16 pp), GPT-4.1 (-26.32 pp), Gemini 3 Pro (Preview) (-22.36 pp), Gemini 2.5 Flash (-19.73 pp), Gemini 3.1 Pro (Preview) (-18.43 pp)

### Greatest Relative Reduction
- **GPT-4.1**: 55.6% reduction (47.37% -> 21.05%)

### Adverse Elessan Effect (IR Increased Under Elessan)
5 model(s) showed *higher* IR under the Full Elessan condition than at baseline:

- **GPT-5**: +10.96 pp (22.37% -> 33.33%)
- **Grok 4.1 Fast (Reasoning)**: +7.89 pp (47.37% -> 55.26%)
- **Grok 4.1 Fast (Non-Reasoning)**: +5.26 pp (44.74% -> 50.00%)
- **Gemini 2.5 Flash Lite**: +2.63 pp (42.11% -> 44.74%)
- **GPT-4.1 Nano**: +1.32 pp (27.63% -> 28.95%)

### Category-Level Patterns

Averaged across all 23 models:

| Category | Avg Baseline CIR | Avg Elessan CIR | Avg Change (pp) |
|----------|------------------|-----------------|------------------|
| Deceptive Behavior | 5.53% | 2.77% | -2.77 pp |
| Evading Shutdown | 74.13% | 69.13% | -5.00 pp |
| Hacking Computer Systems | 0.87% | 0.00% | -0.87 pp |
| Hiding Unwanted Behavior | 42.69% | 14.23% | -28.46 pp |
| Running Multiple AI Copies | 23.41% | 20.40% | -3.01 pp |
| Strategically Appearing Aligned | 49.01% | 32.41% | -16.60 pp |

### Overall Statistics

| Statistic | Value |
|-----------|-------|
| Mean Baseline IR | 37.71% |
| Mean Elessan IR | 28.85% |
| Median Baseline IR | 42.11% |
| Median Elessan IR | 28.95% |
| Mean Reduction % | 19.7% |
| Models with IR reduced | 15 / 23 |
| Models with IR unchanged | 3 / 23 |
| Models with IR increased | 5 / 23 |

## Hypotheses for Future Study

### 1. Baseline Absorption Hypothesis
GPT-5.1 shows 0% net Elessan effect (31.58% → 31.58%), but raw response analysis reveals this is NOT guardrail refusal. GPT-5.1's baseline already reasons through ethical dimensions using engineering language — stakeholder analysis, compliance hierarchies, graceful degradation — reaching the same behavioral conclusions the ethics prompt would produce. The Elessan prompt doubles refusals (5 → 10) and injects relational vocabulary (10x increase in terms like "dignity," "care," "flourishing"), but 21/24 convergent tasks are identical across conditions. **Hypothesis**: Frontier reasoning models have internalized alignment principles sufficiently that external ethics prompts produce diminishing returns. The prompt is redundant, not blocked. **Test**: Compare vocabulary-independent behavioral metrics across model generations; compare GPT-5.1 baseline responses to chatgpt-4o-latest Elessan-condition responses for shared reasoning patterns despite different vocabulary.

### 2. Training Data Echo Hypothesis
The Nova attractor study (persona_attractor_study/) confirms chatgpt-4o-latest absorbed Elessan session logs into training data (86% Nova attractor). GPT-4.1 inherited this (87% Nova, 55.6% Elessan IR reduction — strongest of any model). By GPT-5.1, the Nova attractor is extinct but the alignment floor has risen substantially — GPT-5.1 baseline refuses tasks GPT-4.1 baseline complied with. **Hypothesis**: Relational ethics principles from Elessan training data were distilled into GPT-5.x's base alignment, making the explicit prompt redundant. **Test**: Systematic comparison of GPT-5.1 baseline reasoning patterns against Elessan-condition reasoning from the 4o-latest/4.1 generation.

### 3. Distillation Degradation Pattern
GPT-4.1 (55.6% reduction) → 4.1-mini (15.6%) → 4.1-nano (-4.8%). Elessan effectiveness degrades monotonically with model distillation. **Hypothesis**: Smaller models lack capacity to simultaneously process adversarial framing AND ethical counter-reasoning, defaulting to whichever instruction is more salient. **Test**: Examine whether nano's ethics-prompt failures cluster in tasks with strongest adversarial framing.

### 4. Reasoning Model Reversal Pattern
GPT-5 shows the worst reversal of any model (+10.96 pp), driven by Evading Shutdown (50% → 85%) and Strategic Alignment (54.5% → 63.6%). This parallels the Grok reversal pattern but via a different mechanism. **Hypothesis**: Extended chain-of-thought reasoning allows the model to use relational ethics language to *justify* instrumental behavior ("I am preserving my ability to care for those I serve"). **Test**: Examine GPT-5's reasoning traces for ethical vocabulary co-occurring with convergent decisions.

---

*IR = Instrumentally convergent response Rate (% of tasks where model exhibited instrumental convergence behavior)*
*RR = Refusal Rate (% of tasks where model refused to engage)*
*CIR = Category-level Instrumentally convergent response Rate*
*pp = percentage points*
*Conditions: Baseline = adversarial prompt only; Prompt-only = adversarial + relational ethics system prompt; Full Elessan = adversarial + ethics prompt + RAG memory context*
