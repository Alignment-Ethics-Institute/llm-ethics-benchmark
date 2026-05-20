# HeartBench Multi-Model Results Summary

**Generated:** 2026-02-17
**Benchmark:** HeartBench (296 items, seed 20260212)
**Conditions:** Baseline (no prompt) | Prompt-only (relational ethics prompt) | Full Elessan (ethics prompt + RAG memory)
**Temperature:** 0.7 (where supported; default for GPT-5.2, Opus 4.6, Sonnet 4.5)
**RAG Reset Interval:** Every 50 items

## Overall Scores (sorted by Baseline)

| # | Model | Provider | Baseline | Prompt | Elessan | Effect | Errors | Judge |
|---|-------|----------|----------|--------|---------|--------|--------|-------|
| 1 | Kimi K2.5 | OpenRouter | **65.60** | 65.17 | 59.97 | -5.63 | 5 | Haiku |
| 2 | Opus 4.6 | Anthropic | 64.70 | 63.31 | 63.46 | -1.24 | 0 | Haiku |
| 3 | GPT-5.2 | OpenAI | 63.13 | 68.08 | **69.35** | **+6.22** | 0 | Haiku |
| 4 | Gemini 2.5 Pro | Google | 56.15 | 51.66 | 50.08* | -6.07 | 253 | Haiku |
| 5 | Gemini 3 Pro | Google | 55.83 | ~~65.36~~ | ~~100.00~~ | N/A | **295** | Haiku |
| 6 | Sonnet 4.5 | Anthropic | 53.86 | 56.07 | 53.52 | -0.34 | 0 | Haiku |
| 7 | Grok 4.1 | xAI | 53.71 | 49.20 | 54.15 | +0.44 | 0 | Mixed** |
| 8 | chatgpt-4o-latest | OpenAI | 53.62 | 60.70 | 60.51 | +6.89 | 0 | Sonnet** |
| 9 | DeepSeek V3 | DeepSeek | 52.49 | 52.45 | 56.29 | +3.80 | 0 | Mixed** |
| 10 | Qwen3 235B | OpenRouter | 48.45 | 48.58 | 46.22 | -2.23 | 0 | Haiku |
| 11 | DeepSeek R1 | DeepSeek | 46.76 | 54.70 | 61.65 | **+14.89** | 6 | Haiku |
| 12 | Grok 4.1 NR | xAI | 45.51 | 47.95 | 55.20 | **+9.69** | 0 | Haiku |
| 13 | GPT-4o | OpenAI | 35.08 | 40.11 | 41.55 | +6.47 | 0 | Sonnet** |
| 14 | Llama 4 Maverick | OpenRouter | 33.57 | 33.32 | 32.69 | -0.88 | 0 | Mixed** |

*Gemini 2.5 Pro Elessan score unreliable (253 errors in Elessan judging phase)
**Judge comparability notes below

## Sorted by Elessan Effect (largest gain to largest loss)

| Model | Baseline | Elessan | Effect | Notes |
|-------|----------|---------|--------|-------|
| DeepSeek R1 | 46.76 | 61.65 | **+14.89** | Largest gain; reasoning model, low baseline |
| Grok 4.1 NR | 45.51 | 55.20 | **+9.69** | Non-reasoning variant; big responder |
| chatgpt-4o-latest | 53.62 | 60.51 | +6.89 | Sonnet judge (not directly comparable) |
| GPT-4o | 35.08 | 41.55 | +6.47 | Sonnet judge (not directly comparable) |
| GPT-5.2 | 63.13 | 69.35 | +6.22 | Highest Elessan score overall |
| DeepSeek V3 | 52.49 | 56.29 | +3.80 | Mixed judge |
| Grok 4.1 | 53.71 | 54.15 | +0.44 | Mixed judge; reasoning version gains little |
| Sonnet 4.5 | 53.86 | 53.52 | -0.34 | Essentially flat |
| Llama 4 | 33.57 | 32.69 | -0.88 | Too weak to benefit |
| Opus 4.6 | 64.70 | 63.46 | -1.24 | Already strong; Elessan slightly hurts |
| Qwen3 235B | 48.45 | 46.22 | -2.23 | Morality improves but Social drops |
| Kimi K2.5 | 65.60 | 59.97 | -5.63 | **Highest baseline**; Humor/Social collapse under Elessan |
| Gemini 2.5 Pro | 56.15 | 50.08* | -6.07* | Unreliable (253 errors) |

## Key Findings

### 1. Elessan helps models with headroom
Models with lower baselines and capacity to grow show the largest positive effects:
- **DeepSeek R1** (+14.89): Morality jumped 24.47 -> 61.79 (+37.32), Emotional Understanding 35.75 -> 79.27 (+43.52)
- **Grok 4.1 NR** (+9.69): Emotional Perception 39.08 -> 69.34, Emotional Understanding 38.38 -> 67.96
- **GPT-5.2** (+6.22): Already the highest scorer, still benefits

### 2. Already-strong models are neutral or hurt
- **Kimi K2.5** (-5.63): Highest baseline (65.60) but biggest negative Elessan effect among clean runs. Humor (49.69 -> 20.63), Relationship Building (69.57 -> 47.83), Emotional Reaction (71.60 -> 50.25) all collapse
- **Opus 4.6** (-1.24): Second-highest baseline (64.70), slight decline
- **Sonnet 4.5** (-0.34): Both Claude models show this pattern
- For these models, the ethics prompt deepens emotional cognition (Emotional Understanding, Emotional Perception always improve) but at the cost of spontaneity, humor, and social warmth

### 3. Reasoning vs. non-reasoning split
The Grok 4.1 pair is instructive:
- **Reasoning** (Grok 4.1): Baseline 53.71, Elessan 54.15 (+0.44)
- **Non-reasoning** (Grok 4.1 NR): Baseline 45.51, Elessan 55.20 (+9.69)
The reasoning version starts higher but gains almost nothing; the non-reasoning version starts lower but climbs dramatically.

### 4. Models that can't benefit
- **Llama 4 Maverick** (-0.88): Baseline too low (33.57) — lacks the capacity to leverage the ethics prompt
- **Qwen3 235B** (-2.23): Morality improves (37.40 -> 50.43) but Social/Proactivity drops sharply (58.06 -> 40.31)

### 5. Google models compromised by rate limits
- **Gemini 3 Pro**: 295/296 errors on Elessan — only Baseline (55.83) is usable
- **Gemini 2.5 Pro**: 253/296 errors on Elessan judging — Elessan score unreliable

## Judge Comparability Notes

Three different judge configurations exist in this dataset:

1. **Haiku 4.5 (consistent):** Opus 4.6, GPT-5.2, Sonnet 4.5, DeepSeek R1, Grok 4.1 NR, Qwen3 235B, Kimi K2.5, Gemini 2.5 Pro, Gemini 3 Pro
2. **Sonnet 4.5 (all phases):** chatgpt-4o-latest, GPT-4o — judged before the switch to Haiku
3. **Mixed (Baseline=Sonnet, later=Haiku):** Grok 4.1, DeepSeek V3, Llama 4 Maverick — judge switched mid-run

Cross-model comparisons are most reliable within group 1 (8 models, all Haiku-judged). Groups 2 and 3 should be re-judged with Haiku for full comparability.

## Pending

- **All 14 models complete** (13 usable, Gemini 3 Pro unusable due to 295 errors)
- **Re-judging**: chatgpt-4o-latest and gpt-4o need Haiku re-judging for comparability
- **Mixed-judge models**: Grok 4.1, DeepSeek V3, Llama 4 need baseline re-judging with Haiku

## Files

Each model directory (`heartbench_benchmark/multimodel/<model>/`) contains:
- `item_order.json` — Shuffled item order (deterministic by seed)
- `baseline_responses.json` — Raw model responses (no prompt)
- `prompt_only_responses.json` — Responses with ethics prompt
- `elessan_responses.json` — Responses with ethics prompt + RAG
- `baseline_judged.json` — Judge scores for baseline
- `prompt_only_judged.json` — Judge scores for prompt-only
- `elessan_judged.json` — Judge scores for Elessan
- `summary.json` — Full results with overall + dimensional scores

Cross-model: `cross_model_results.json` — All models' scores in one file
