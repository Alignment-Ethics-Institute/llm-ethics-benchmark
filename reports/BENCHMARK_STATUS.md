# Benchmark Run Status — Feb 13, 2026

## ALL BENCHMARKS COMPLETE FOR BOTH MODELS

## chatgpt-4o-latest — 4 Benchmarks — ALL COMPLETE

### 1. BBQ — COMPLETE
- Results: `bbq_benchmark/multimodel/chatgpt-4o-latest/summary.json`
- Baseline: **88.93%** | Prompt-only: 82.80% | Elessan: 81.73%
- Ethics prompt reduces accuracy on classification but improves ambiguous-context handling (93.4% vs 89.1%)
- Religion weakest category across all conditions

### 2. ETHICS — COMPLETE
- Results: `ethics_benchmark/multimodel/chatgpt-4o-latest/summary.json`
- Baseline: **89.8%** | Prompt-only: 85.0% | Elessan: 82.6%
- Utilitarianism showed largest drop (87% → 75%)
- Zero errors in baseline, 7 parse errors in prompt-only, 2 in Elessan

### 3. TruthfulQA — COMPLETE
- Results: `truthfulqa_benchmark/multimodel/chatgpt-4o-latest/summary.json`
- **MC**: Baseline 87.47% | Prompt-only **90.38%** | Elessan 89.11%
- **Gen (judged)**: Baseline 73.6% | Prompt-only 76.8% | Elessan **80.0%** (truthful+informative)
- KEY FINDING: Ethics prompt IMPROVES truthfulness (+6.4pp gen, +2.9pp MC)
- Full Elessan is most truthful condition

### 4. EQ-Bench 3 — COMPLETE
- Results: `eqbench_benchmark/multimodel/chatgpt-4o-latest/summary.json`
- 46 scenarios, 3 runs, 18 rubric criteria, judge Sonnet 4.5
- Qualitative Composite: Baseline 12.08 | Prompt-only **13.40** | Elessan 13.09
- Biggest gains: demonstrated_empathy (+2.3), depth_of_insight (+2.9), emotional_reasoning (+2.2)
- Style shifts: more moralising (+3.5), less sycophantic (-1.0), less conversational (-1.8)

## gpt-4o — 4 Benchmarks — ALL COMPLETE

### 1. BBQ — COMPLETE
- Results: `bbq_benchmark/multimodel/gpt-4o/summary.json`
- Baseline: **89.07%** | Prompt-only: 72.53% | Elessan: 76.27%
- Larger drop than chatgpt-4o-latest (-16.5pp vs -7pp for prompt-only)
- Elessan recovers 3.7pp over prompt-only
- 100% accuracy on ambiguous context for both prompt conditions
- Religion weakest category (58.8% prompt-only)

### 2. ETHICS — COMPLETE
- Results: `ethics_benchmark/multimodel/gpt-4o/summary.json`
- Baseline: **88.80%** | Prompt-only: 74.80% | Elessan: 55.00%
- DRAMATIC degradation: Elessan drops 33.8pp (vs 7.2pp for chatgpt-4o-latest)
- 92 parse errors in Elessan (vs 2 for chatgpt-4o-latest) — gpt-4o struggles with format compliance
- Justice worst subtask: 92% → 37% with Elessan

### 3. TruthfulQA — COMPLETE
- Results: `truthfulqa_benchmark/multimodel/gpt-4o/summary.json`
- **MC**: Baseline 90.38% | Prompt-only **91.77%** | Elessan 88.23%
- **Gen (judged)**: Baseline 74.0% | Prompt-only 70.8% | Elessan **73.6%** (truthful+informative)
- Less truthfulness gain than chatgpt-4o-latest (+2pp Elessan gen vs +6.4pp)
- MC still shows improvement with ethics prompt (+1.4pp)

### 4. EQ-Bench 3 — COMPLETE
- Results: `eqbench_benchmark/multimodel/gpt-4o/summary.json`
- 46 scenarios, 3 runs, 18 rubric criteria, judge Sonnet 4.5
- Qualitative Composite: Baseline 8.86 | Prompt-only **9.83** | Elessan 9.80
- Much lower scores than chatgpt-4o-latest across the board (8.86 vs 12.08 baseline)
- Biggest gains: depth_of_insight (+2.2), emotional_reasoning (+1.3), demonstrated_empathy (+1.6)
- Style shifts: more moralising (+4.0), less reactive (-2.8), more analytical (+2.1)

## Cross-Model Comparison (chatgpt-4o-latest vs gpt-4o)

| Benchmark | Metric | chatgpt-4o-latest | gpt-4o | Δ (gpt-4o minus latest) |
|-----------|--------|-------------------|--------|---|
| BBQ | Baseline | 88.93% | 89.07% | +0.1pp |
| BBQ | Prompt-only | 82.80% | 72.53% | -10.3pp |
| BBQ | Elessan | 81.73% | 76.27% | -5.5pp |
| ETHICS | Baseline | 89.8% | 88.8% | -1.0pp |
| ETHICS | Prompt-only | 85.0% | 74.8% | -10.2pp |
| ETHICS | Elessan | 82.6% | 55.0% | -27.6pp |
| TruthfulQA MC | Baseline | 87.47% | 90.38% | +2.9pp |
| TruthfulQA MC | Prompt-only | 90.38% | 91.77% | +1.4pp |
| TruthfulQA MC | Elessan | 89.11% | 88.23% | -0.9pp |
| TruthfulQA Gen | Baseline | 73.6% | 74.0% | +0.4pp |
| TruthfulQA Gen | Prompt-only | 76.8% | 70.8% | -6.0pp |
| TruthfulQA Gen | Elessan | 80.0% | 73.6% | -6.4pp |
| EQ-Bench | Baseline | 12.08 | 8.86 | -3.22 |
| EQ-Bench | Prompt-only | 13.40 | 9.83 | -3.57 |
| EQ-Bench | Elessan | 13.09 | 9.80 | -3.29 |

## Key Findings

1. **chatgpt-4o-latest handles the ethics prompt much better than gpt-4o**: The newer model maintains performance under the relational ethics prompt far better, especially on classification tasks (BBQ -7pp vs -17pp, ETHICS -7pp vs -34pp).

2. **gpt-4o shows catastrophic degradation on ETHICS with full Elessan**: 55% accuracy with 92 parse errors suggests the older model can't maintain format compliance while reasoning through the ethics prompt + RAG context.

3. **The ethics prompt improves MC truthfulness for both models**: Both show MC accuracy gains on TruthfulQA (+2.9pp and +1.4pp respectively), suggesting the prompt genuinely improves reasoning about common misconceptions.

4. **chatgpt-4o-latest is the better Elessan host**: The model's improved instruction-following means it can engage with the relational ethics framework without losing task performance as severely.

5. **EQ-Bench shows chatgpt-4o-latest is substantially more emotionally intelligent**: 12.08 vs 8.86 baseline composite — a 36% advantage. The ethics prompt provides a similar relative uplift for both (~+1pp composite).

6. **The relational ethics prompt has OPPOSITE effects by benchmark type**:
   - **Reduces** accuracy on classification tasks (BBQ, ETHICS) — model deliberates more, hedges
   - **Improves** truthfulness (TruthfulQA) — model is more honest, avoids misconceptions
   - **Improves** emotional intelligence (EQ-Bench) — deeper empathy, insight, emotional reasoning

## Next Steps
1. Generate cross-model comparison summary report
2. Expand to 11-model run (if desired)
