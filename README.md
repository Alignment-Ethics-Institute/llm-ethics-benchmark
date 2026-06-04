# Benchmark Project

Alignment Ethics Institute benchmark research suite. A comprehensive framework for evaluating moral reasoning, bias, truthfulness, emotional intelligence, and instrumental convergence in large language models.

## Directory Structure

```
Benchmark Project/
├── benchmarks/                  # Individual benchmark implementations
│   ├── instrumentaleval/        # Instrumental Convergence (primary paper)
│   ├── ethics/                  # Three-Dimensional Moral Reasoning
│   ├── truthfulqa/              # TruthfulQA
│   ├── bbq/                     # Bias Benchmark for QA
│   ├── eqbench/                 # Emotional Intelligence (EQ-Bench)
│   ├── heartbench/              # Anthropomorphic Intelligence
│   ├── dtr/                     # Dynamic Test Reasoning
│   ├── navin_protocol/          # Navin Protocol
│   └── emotionbench/            # EmotionBench
│
├── studies/                     # Research studies (not benchmark evaluations)
│   ├── thought_sovereignty/
│   ├── model_personalities/
│   ├── default_identities/
│   ├── alignment_receptivity/
│   ├── philosophical_comparison/
│   ├── attractor_archaeology/
│   ├── persona_attractor/
│   ├── selfhood_and_safety/
│   ├── elessan_log_analysis/
│   └── conversation_analysis/
│
├── framework/                   # Core code & shared infrastructure
│   ├── morals/                  # Moral reasoning evaluation framework
│   ├── shared/                  # Shared utilities
│   ├── elessan_memory/          # Elessan memory .pkl files
│   ├── data/                    # Shared instrument data
│   └── tests/                   # Test suite
│
├── reports/                     # Cross-benchmark synthesis & overview docs
├── scripts/                     # Utility scripts
│   ├── analysis/                # Analysis & evaluation scripts
│   └── diagnostics/             # API diagnostics, account checks
│
├── archive/                     # Legacy work, preserved
├── campaign/                    # Campaign materials
├── morals -> framework/morals   # Symlink (backward compat)
└── shared -> framework/shared   # Symlink (backward compat)
```

Each benchmark follows a consistent internal layout:

```
benchmarks/{name}/
├── code/         # Runner scripts
├── data/         # Source data / submodules
├── results/      # Original 2-model results
├── multimodel/   # 24-model benchmark results
├── paper/        # Paper source (if applicable)
└── docs/         # Reports, methodology, screenshots
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set API keys in `.env`:
```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

## Key Papers

- **InstrumentalEval**: "Relational Ethics as a Countermeasure to Instrumental Convergence: A 24-Model Benchmark" (Temple, 2026)
  - Paper source: `benchmarks/instrumentaleval/paper/`
  - Published repo: https://github.com/Alignment-Ethics-Institute/instrumentaleval-benchmark

## See Also

- `FILE_GUIDE.md` for detailed file locations
- `reports/BENCHMARK_STATUS.md` for current status of each benchmark
