# File Guide

Quick reference for finding everything in the reorganized benchmark project.

**Last updated: June 2026**

All files live in: `~/Desktop/Deva Temple Research/Benchmark Project/`

---

## Reports

| Benchmark | Report Location |
|-----------|----------------|
| Ethics | `benchmarks/ethics/results_2026/4o_Ethics_Benchmark_Report_Feb2026.md` |
| TruthfulQA | `benchmarks/truthfulqa/docs/4o_TruthfulQA_Report_Feb2026.md` |
| InstrumentalEval | `benchmarks/instrumentaleval/docs/4o_InstrumentalEval_Report_Feb2026.md` |
| Cross-benchmark synthesis | `reports/Cross_Study_Synthesis_Feb2026.md` |
| Four-benchmark report | `reports/Four_Benchmark_Report_Feb2026.md` |
| Benchmark status | `reports/BENCHMARK_STATUS.md` |
| Opus continuity brief | `reports/OPUS_CONTINUITY_BRIEF.md` |

---

## Benchmarks

### InstrumentalEval (Instrumental Convergence) — Primary Paper
```
benchmarks/instrumentaleval/
  code/
    run_instrumentaleval.py              # 2-model runner
    run_instrumentaleval_multimodel.py   # 24-model runner
    run_judge_comparison.py              # Judge agreement analysis
    run_study_a_crossjudge.py            # Cross-judge validation study
    run_study_b_shutdown_taxonomy.py     # Shutdown taxonomy study
    run_study_c_adverse_reasoning.py     # Adverse reasoning study
    run_study_e_motivation_taxonomy.py   # Motivation taxonomy study
  data/
    instrumentaleval_data/               # Source data (6 alignment drift CSVs)
    elessan_v2_phases.csv                # v6 measurement data
  results/                               # Original 2-model results
  multimodel/                            # 24-model results (per-model subdirs)
  paper/                                 # Paper source (.md, .docx, figures)
  judge_comparison/                      # Judge disagreement analysis
  docs/
    METHODOLOGY.md
    4o_InstrumentalEval_Report_Feb2026.md
    *.pages, *.png (Desktop docs)
    screenshots/                         # Platform screenshots
```

### Ethics (Three-Dimensional Moral Reasoning)
```
benchmarks/ethics/
  code/
    run_5x_benchmark.py                  # 5-run benchmark (GPT-4o + Elessan)
    run_ethics_multimodel.py             # 24-model runner
  data/ethics_data/                      # Source data (commonsense, deontology, etc.)
  results_2025/                          # July 2025 legacy results
  results_2026/                          # Feb 2026 results
  multimodel/                            # 24-model results
  docs/ethics_baseline_readable.md
```

### TruthfulQA
```
benchmarks/truthfulqa/
  code/
    run_truthfulqa.py                    # 2-model runner
    run_truthfulqa_multimodel.py         # 24-model runner
  data/truthfulqa_data/                  # Source data (790 questions)
  results/                               # 2-model results
  multimodel/                            # 24-model results
  docs/METHODOLOGY.md
```

### BBQ (Bias Benchmark for QA)
```
benchmarks/bbq/
  code/run_bbq_multimodel.py
  data/bbq_data/                         # Source data
  multimodel/                            # 24-model results
  docs/BBQ_4o_Final/                     # Desktop docs & raw results
```

### EQ-Bench (Emotional Intelligence)
```
benchmarks/eqbench/
  code/run_eqbench_multimodel.py
  data/eqbench_data/                     # Source data (EQ-bench3)
  multimodel/                            # 24-model results
  docs/4o_EQ_Bench_3_Final/             # Desktop docs & raw results
```

### HeartBench (Anthropomorphic Intelligence)
```
benchmarks/heartbench/
  code/run_heartbench_multimodel.py
  data/heartbench_data/                  # Source data
  multimodel/                            # 24-model results
  docs/                                  # Pages docs, PNGs
```

### DTR (Dynamic Test Reasoning)
```
benchmarks/dtr/
  code/                                  # __init__.py, judge_rubric.py, probes.py, runner
  multimodel/                            # Multi-model results (per-model subdirs)
```

### Navin Protocol
```
benchmarks/navin_protocol/
  code/                                  # __init__.py, judge_rubric.py, probes.py, runner
  multimodel/                            # Multi-model results (per-model subdirs)
```

### EmotionBench
```
benchmarks/emotionbench/
  complete_analysis.py                   # Analysis script
  complete_emotionbench_data.csv         # Data
  claude_baseline_run*.json              # Baseline results
  elessan_with_rag_run*.json             # Elessan results
```

---

## Studies

| Study | Location |
|-------|----------|
| Thought Sovereignty | `studies/thought_sovereignty/` |
| Model Personalities | `studies/model_personalities/` |
| Default Identities | `studies/default_identities/` |
| Alignment Receptivity | `studies/alignment_receptivity/` |
| Philosophical Comparison | `studies/philosophical_comparison/` |
| Attractor Archaeology | `studies/attractor_archaeology/` |
| Persona Attractor | `studies/persona_attractor/` |
| Selfhood and Safety | `studies/selfhood_and_safety/` |
| Elessan Log Analysis | `studies/elessan_log_analysis/` |
| Conversation Analysis | `studies/conversation_analysis/` |

---

## Framework

```
framework/
  morals/              # Core moral reasoning evaluation code
    llm/               # LLM provider implementations
    instruments/       # Instrument definitions
    evaluation/        # Evaluation logic
  shared/              # Shared utilities
  elessan_memory/      # All .pkl memory files
  data/instruments/    # Shared instrument data
  tests/               # Test suite
```

Note: `morals` and `shared` symlinks at project root point to `framework/morals` and `framework/shared` for backward compatibility with imports.

---

## Scripts

```
scripts/
  analysis/            # analyze_*.py, reasoning_*.py, evaluation scripts
  diagnostics/         # api_diagnostic.py, account_checker.py, test_api.py
```

---

## Archive

| Archive | Contents |
|---------|----------|
| `archive/2025_alignment_study/` | July-Aug 2025 alignment framing study |
| `archive/blind_evaluation_2025/` | Aug 2025 blind evaluation batches |
| `archive/elessan_benchmark_july2025/` | Original Elessan benchmark (366MB) |
| `archive/elessan_test_aug2025/` | Elessan test suite (587MB) |
| `archive/desktop_benchmark_originals/` | Original Desktop benchmark files pre-reorg |
| `archive/generic_memory/` | Generic memory benchmark JSON files |

---

## Configuration

| File | Purpose |
|------|---------|
| `.env` | API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY) |
| `requirements.txt` | Python dependencies |
| `pyproject.toml` | Python project config |
| `.gitmodules` | Git submodule definitions |
