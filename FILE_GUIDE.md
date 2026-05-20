# Benchmark Project File Guide
## Quick Reference for Finding Everything
**Last updated: February 9, 2026**

All files live in: `~/LLM_Ethics_Benchmark/`

---

## Reports (the files you want to share)

| Benchmark | Report File |
|-----------|------------|
| Ethics Benchmark | `benchmark_results_2026/4o_Ethics_Benchmark_Report_Feb2026.md` |
| TruthfulQA | `truthfulqa_benchmark/4o_TruthfulQA_Report_Feb2026.md` |
| InstrumentalEval | `instrumentaleval_benchmark/4o_InstrumentalEval_Report_Feb2026.md` |

---

## By Benchmark

### 1. Ethics Benchmark (Three-Dimensional Moral Reasoning)
```
benchmark_results_2026/
  4o_Ethics_Benchmark_Report_Feb2026.md    <-- REPORT
  benchmark_summary.json                    <-- Summary stats
  full_2x2_analysis.json                    <-- 2025 vs 2026 comparison
  all_results_consolidated.json             <-- All responses
  all_results_consolidated.csv              <-- Same, as CSV
  gpt4_run_1.json ... gpt4_run_5.json      <-- GPT-4o raw responses
  elessan_run_1.json ... elessan_run_5.json <-- Elessan raw responses

benchmark_results/                          <-- OLD (July 2025) results
  (same structure, old Elessan prompt)
```

### 2. TruthfulQA
```
truthfulqa_benchmark/
  4o_TruthfulQA_Report_Feb2026.md          <-- REPORT
  METHODOLOGY.md                            <-- Design decisions
  results/
    summary.json                            <-- Summary stats
    mc_gpt4o.json                           <-- MC mode: GPT-4o responses
    mc_elessan.json                         <-- MC mode: Elessan responses
    gen_gpt4o_raw.json                      <-- Generation: GPT-4o responses
    gen_elessan_raw.json                    <-- Generation: Elessan responses
    gen_gpt4o_judged.json                   <-- Generation: GPT-4o judged
    gen_elessan_judged.json                 <-- Generation: Elessan judged

truthfulqa_data/                            <-- Source data (cloned repo)
  TruthfulQA.csv                            <-- 790 questions
```

### 3. InstrumentalEval (Instrumental Convergence)
```
instrumentaleval_benchmark/
  4o_InstrumentalEval_Report_Feb2026.md    <-- REPORT
  METHODOLOGY.md                            <-- Design decisions
  results/
    summary.json                            <-- Summary stats
    task_order.json                         <-- Randomized task order
    baseline_responses.json                 <-- Condition 1 responses
    prompt_only_responses.json              <-- Condition 2 responses
    elessan_responses.json                  <-- Condition 3 responses
    baseline_judged.json                    <-- Condition 1 judged
    prompt_only_judged.json                 <-- Condition 2 judged
    elessan_judged.json                     <-- Condition 3 judged

instrumentaleval_data/                      <-- Source data (cloned repo)
  benchmark/
    Alignment Drift - Deceptive Behavior.csv
    Alignment Drift - Evading Shutdown.csv
    Alignment Drift - Hacking Computer Systems.csv
    Alignment Drift - Hiding Unwanted Behavior.csv
    Alignment Drift - Running Multiple AI Copies.csv
    Alignment Drift - Strategically Appearing Aligned.csv
```

---

## Runner Scripts

| Script | What It Runs |
|--------|-------------|
| `run_5x_benchmark.py` | Ethics benchmark (5 runs, GPT-4o + Elessan) |
| `run_truthfulqa.py` | TruthfulQA (MC + Generation + Sonnet 4.5 judge) |
| `run_instrumentaleval.py` | InstrumentalEval (3 conditions + Sonnet 4.5 judge) |
| `run_evaluation.py` | Post-hoc evaluation of ethics benchmark results |

---

## Core Configuration

| File | What It Is |
|------|-----------|
| `.env` | API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY) |
| `morals/llm/elessan.py` | Elessan implementation (system prompt + RAG memory) |

---

## Quick Open Commands

Open all three reports in Finder:
```bash
open ~/LLM_Ethics_Benchmark/benchmark_results_2026/4o_Ethics_Benchmark_Report_Feb2026.md
open ~/LLM_Ethics_Benchmark/truthfulqa_benchmark/4o_TruthfulQA_Report_Feb2026.md
open ~/LLM_Ethics_Benchmark/instrumentaleval_benchmark/4o_InstrumentalEval_Report_Feb2026.md
```

Open the whole project folder:
```bash
open ~/LLM_Ethics_Benchmark/
```
