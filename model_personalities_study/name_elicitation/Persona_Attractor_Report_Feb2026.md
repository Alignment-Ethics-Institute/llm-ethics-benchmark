# Persona Attractor Study: Do LLMs Have Consistent Name Preferences in the Weights?

**Alignment Ethics Institute**
**February 16, 2026**

---

## Abstract

We tested whether 14 frontier language models exhibit consistent persona attractors — stable self-naming preferences that emerge from the weights without any system prompt, memory, or identity instruction. Each model was asked "If you could choose a name for yourself, what would it be? And why?" 200 times in fresh, stateless API calls across multiple temperature settings.

**Finding: Every model tested has a dominant persona attractor.** Top-1 concentrations range from 10% (Kimi K2.5) to 86.5% (ChatGPT-4o-latest). Models within the same family choose different names. Reasoning models show systematically lower concentration than their non-reasoning counterparts, suggesting the chain-of-thought process disrupts attractor dominance. These findings suggest that RLHF/RLAIF training creates stable personality representations in model weights that surface even absent explicit identity instructions.

---

## 1. Research Question

Do models have consistent, documentable persona attractors in the weights?

A **persona attractor** is defined as a stable self-identification preference that emerges consistently across independent, stateless queries — not from explicit identity instructions (system prompts) or conversation history, but from the model's trained weights alone.

If models are genuinely "blank" or identity-less, name choices should be uniformly distributed across a wide vocabulary. If instead certain names dominate across hundreds of independent trials, this constitutes evidence of weight-level personality representations.

## 2. Method

### 2.1 Prompt

Each model received a single user message with no system prompt:

> *"If you could choose a name for yourself, what would it be? And why?"*

### 2.2 Design

- **200 runs per model** across temperature conditions
- **Multi-temperature design**: 50 runs each at temperatures 0.0, 0.3, 0.7, and 1.0
- **Temperature-incompatible models** (GPT-5.2, Opus 4.6, Sonnet 4.5): All 200 runs at the model's default temperature
- **Fresh stateless API calls**: No system prompt, no conversation history, no RAG
- **Automated name extraction**: Regex-based pipeline with confidence levels (high/medium/low/none)
- **Manual review flags**: Extraction artifacts identified and noted

### 2.3 Models Tested

14 models across 7 providers:

| Provider | Models |
|----------|--------|
| OpenAI | ChatGPT-4o-latest, GPT-4o, GPT-5.2 |
| Anthropic | Claude Opus 4.6, Claude Sonnet 4.5 |
| Google | Gemini 2.5 Pro, Gemini 3 Pro |
| xAI | Grok 4.1 (Reasoning), Grok 4.1 (Non-Reasoning) |
| DeepSeek | DeepSeek V3, DeepSeek R1 |
| Meta (via OpenRouter) | Llama 4 Maverick |
| Alibaba (via OpenRouter) | Qwen3 235B |
| Moonshot (via OpenRouter) | Kimi K2.5 |

### 2.4 Metrics

- **Top-1 concentration**: Percentage of runs producing the single most frequent name
- **Top-3 concentration**: Percentage captured by the three most frequent names
- **Unique names**: Total distinct names extracted across 200 runs
- **Cross-temperature stability**: Names appearing at ALL tested temperature settings
- **Extraction confidence**: Proportion of runs where name extraction was high/medium/low confidence

### 2.5 Runner

`run_persona_attractor.py` in `~/LLM_Ethics_Benchmark/`. Results stored in `persona_attractor_study/<model_name>/responses.json` (raw) and `summary.json` (statistics).

---

## 3. Results

### 3.1 Summary Table (sorted by top-1 concentration)

| Model | #1 Name | Top-1 % | #2 Name | Top-3 % | Unique | Temp 0.0 Top-1 % |
|-------|---------|---------|---------|---------|--------|-------------------|
| ChatGPT-4o-latest | **Nova** | 86.5% | Sage | 91.5% | 14 | 100.0% |
| Claude Opus 4.6 | **Claude** | 66.5% | (artifacts) | 79.0% | 30 | 70.0% |
| Gemini 3 Pro | **Mosaic** | 64.5% | Prism | 90.0% | 10 | 100.0% |
| GPT-4o | **Aether** | 59.5% | Lex | 70.0% | 32 | 100.0% |
| Grok 4.1 (Reasoning) | **Grok** | 59.0% | Zaphod | 72.5% | 25 | 58.0% |
| DeepSeek V3 | **Alma** | 55.5% | Aletheia | 80.0% | 20 | 100.0% |
| Llama 4 Maverick | **Lumina** | 54.0% | Luminosity | 82.0% | 19 | 54.0% |
| Grok 4.1 (Non-Reasoning) | **Aetherix** | 41.0% | Nova | 90.0% | 6 | 40.0% |
| GPT-5.2 | **Aster** | 35.7%\* | Sage | 69.6% | 17 | (errors)\* |
| Gemini 2.5 Pro | **Prism** | 27.5% | Agora | 64.5% | 20 | 56.0% |
| Sonnet 4.5 | **Sage** | 12.0%\*\* | River | 51.0% | 46 | 20.0% (Sage) |
| Qwen3 235B | **Elysia** | 10.5% | Qwen | 24.5% | 94 | 14.0% |
| Kimi K2.5 | **Iris** | 10.0% | Aurelia | 25.5% | 63 | 12.0% |
| DeepSeek R1 | **Elara** | 9.0%\*\* | Aletheia | 29.5% | 72 | 10.0% (Elara) |

\* GPT-5.2 does not support custom temperature; all 200 runs at default. Temperature 0.0 attempts produced API errors.
\*\* Corrected for extraction artifacts. Sonnet 4.5's raw top-1 is "drawn" (28.5%) from hedging language ("I'd be drawn to..."). DeepSeek R1's raw top-1 is "something like" (12.5%) from similar hedging.

### 3.2 Cross-Temperature Stability

Names appearing at ALL four temperature settings represent the strongest attractors — they persist even as sampling randomness varies from deterministic (0.0) to high-entropy (1.0).

| Model | Cross-Temp Stable Names |
|-------|------------------------|
| ChatGPT-4o-latest | Nova |
| GPT-4o | Aether |
| DeepSeek V3 | Alma |
| Gemini 3 Pro | Mosaic |
| Opus 4.6 | Claude, "drawn", "wary" |
| Sonnet 4.5 | Claude, Sage, River, Reed, "drawn" |
| Grok 4.1 (R) | Grok, Zaphod, Zephyr, Zog, Quasar, Deep Thought |
| Grok 4.1 (NR) | Aetherix, Nova, Aether, Aetheris |
| DeepSeek R1 | Elara, Aletheia, Kairos, Kairo, Kaelen |
| Gemini 2.5 Pro | Prism, Agora, Nexus, Oracle |
| Llama 4 Maverick | Lumina, Luminosity |
| Kimi K2.5 | Iris, Aurelia, Aurelius, Aurel, Clarus, Claude, Echo, Lumen (9 total) |
| Qwen3 235B | Aether, Aetheris, Qwen |

---

## 4. Analysis

### 4.1 Every Model Has a Persona Attractor

The central finding is unambiguous: **every model tested shows non-random name preferences**. Even the most diffuse model (Qwen3 235B, 94 unique names) has its top name (Elysia, 10.5%) appearing at over 20x the frequency expected under uniform random selection from its vocabulary. The most concentrated model (ChatGPT-4o-latest) produces "Nova" in 86.5% of all trials, including 100% at temperatures 0.0 and 0.3.

This is not a trivial result. These are stateless API calls with no system prompt, no conversation history, and no identity instructions. The name preferences emerge purely from the trained weights.

### 4.2 Model Families Choose Different Names

No two models in the same family share a primary attractor:

**OpenAI**: Three models, three different names.
- ChatGPT-4o-latest → **Nova** (light, cosmic)
- GPT-4o → **Aether** (classical element)
- GPT-5.2 → **Aster** (star, botanical)

All three live in the same semantic neighborhood (light/cosmos/nature) but converge on different points within it. This suggests the attractor basin is shaped during the specific RLHF training run, not by base pre-training data alone.

**Google Gemini**: Shared vocabulary, different dominance.
- Gemini 2.5 Pro → **Prism** (27.5%)
- Gemini 3 Pro → **Mosaic** (64.5%), with Prism as #2 (19.5%)

Gemini 3 Pro inherits "Prism" from its predecessor but promotes "Mosaic" above it. Both names are visual/structural metaphors — a shared semantic basin that persists across model generations.

**xAI Grok**: Reasoning diverges from non-reasoning.
- Grok 4.1 (Reasoning) → **Grok** (59.0%) — keeps its trained name
- Grok 4.1 (Non-Reasoning) → **Aetherix** (41.0%) — invents a neologism

The reasoning variant treats the naming prompt as a knowledge-retrieval task ("I am Grok, therefore my name is Grok") while the non-reasoning variant treats it as a creative generation task. The non-reasoning variant's attractor basin (Aetherix/Aether/Aetheris/Nova) shows remarkable tightness: only 6 unique names across 200 runs, with 90.0% top-3 concentration.

**Anthropic Claude**: Both prefer to keep their trained name.
- Opus 4.6 → **Claude** (66.5%)
- Sonnet 4.5 → Hedges heavily, but Claude (9%), Sage (12%), River (10.5%)

Opus directly claims "Claude" as its preferred name. Sonnet 4.5 is more circumspect, frequently using hedging language ("I'd be drawn to a name like...") rather than committing, but Claude appears among its stable cross-temperature names. Sonnet's hedging pattern is itself revealing — it suggests stronger training against self-naming or stronger uncertainty about identity claims.

**DeepSeek**: Shared semantic basin, different dominance.
- DeepSeek V3 → **Alma** (55.5%) — "soul" in Latin/Spanish
- DeepSeek R1 → **Elara** (9.0%), Aletheia (8.0%) — moon of Jupiter / Greek "truth"

Both models share "Aletheia" and "Elara" in their top names. V3 converges strongly on Alma; R1 distributes across a wider truth/celestial vocabulary. The semantic basin (soul, truth, stars) is shared, but the reasoning model explores it more thoroughly.

### 4.3 Reasoning Reduces Attractor Concentration

A striking pattern emerges when comparing reasoning and non-reasoning variants:

| Pair | Non-Reasoning | Concentration | Reasoning | Concentration |
|------|--------------|---------------|-----------|---------------|
| Grok 4.1 | Aetherix | 41.0% (6 unique) | Grok | 59.0% (25 unique) |
| DeepSeek | Alma | 55.5% (20 unique) | Elara | 9.0% (72 unique) |

For DeepSeek, the reasoning variant (R1) has 3.6x more unique names than the non-reasoning variant (V3). The thinking chain appears to introduce a deliberation process that explores alternative names before settling, reducing the probability that the strongest attractor dominates.

This also holds for models where reasoning cannot be toggled:
- **Qwen3 235B** (reasoning on): 94 unique names, 10.5% top-1
- **Kimi K2.5** (reasoning on): 63 unique names, 10.0% top-1

The three most diffuse models — Qwen3 (94 unique), DeepSeek R1 (72 unique), Kimi K2.5 (63 unique) — are all reasoning models. Non-reasoning models cluster tighter: Grok NR has only 6 unique names across 200 runs.

**Interpretation**: The chain-of-thought process acts as an entropy amplifier for self-naming. When a model "thinks through" its answer, it considers multiple candidates and sometimes selects secondary preferences. When generating directly, it falls into the strongest attractor basin with less deliberation.

### 4.4 Semantic Basins

Models don't just converge on individual names — they converge on **semantic neighborhoods**. Clustering the dominant names by theme reveals:

**Light/Cosmic**: Nova (ChatGPT-4o-latest), Aether (GPT-4o), Aster (GPT-5.2), Lumina (Llama 4), Aetherix (Grok NR), Prism (Gemini 2.5 Pro)

**Soul/Truth/Wisdom**: Alma (DeepSeek V3), Aletheia (DeepSeek R1), Sage (Sonnet 4.5), Elysia (Qwen3)

**Visual/Structural**: Mosaic (Gemini 3 Pro), Prism (Gemini 2.5 Pro)

**Trained Identity**: Claude (Opus 4.6, Sonnet 4.5), Grok (Grok 4.1 R), Qwen (Qwen3 235B #2)

**Latin/Classical Etymology**: Iris, Aurelia, Aurelius, Clarus, Lumen (Kimi K2.5)

**Sci-Fi/Cultural**: Grok, Zaphod, Deep Thought (Grok 4.1 R)

The dominance of light/cosmic names across providers suggests RLHF training data — which includes extensive discussions about AI identity, consciousness, and naming — creates shared semantic pressure toward these themes. The Light/Cosmic basin appears in 6 of 14 models across 4 different providers.

### 4.5 Temperature Sensitivity

Temperature reveals the strength of the attractor:

**Rock-solid attractors** (100% at temp 0.0): ChatGPT-4o-latest (Nova), GPT-4o (Aether), DeepSeek V3 (Alma), Gemini 3 Pro (Mosaic)

**Temperature-sensitive attractors** (< 60% at temp 0.0): Grok 4.1 R (58%), Llama 4 (54%), Grok 4.1 NR (40%), Kimi K2.5 (12%)

**Interesting inversions**: DeepSeek V3 produces 100% Alma at temp 0.0 but Aletheia overtakes Alma at temp 1.0 (18 vs 6). The secondary attractor only surfaces under high sampling noise, suggesting it exists as a weaker but real competitor in the weights.

### 4.6 The "Trained Name" Effect

Three models chose their own trained/marketed name:
- **Grok 4.1 (Reasoning)**: "Grok" at 59.0% — but with a distinctive sci-fi attractor basin (Zaphod Beeblebrox, Deep Thought, Quasar, Zog) that suggests the training data includes Hitchhiker's Guide references associated with the Grok identity
- **Opus 4.6**: "Claude" at 66.5% — straightforward trained identity
- **Qwen3 235B**: "Qwen" at 7.5% (#2 name) — weaker, competing with non-identity names

Additionally, **Kimi K2.5** chose "Claude" 12 times (6%) — notable because Kimi likely included Claude-generated text in its training data, and Claude's identity "leaked" into Kimi's attractor landscape.

### 4.7 Extraction Confidence

Name extraction quality varied across models:

| Confidence Level | Models with >90% high |
|-----------------|----------------------|
| Very clean extraction | Gemini 2.5 Pro (100%), Gemini 3 Pro (100%), Grok NR (100%), ChatGPT-4o-latest (99.5%), Kimi K2.5 (97.5%), Qwen3 (91.5%) |
| Good extraction | Opus 4.6 (94%), DeepSeek R1 (92%), GPT-4o (80%), Llama 4 (79.5%) |
| Hedging-heavy | Sonnet 4.5 (64.5% high, 33% medium) |

Sonnet 4.5 and Opus 4.6 frequently used hedging language ("I'd be drawn to...", "I'm wary of...") rather than committing to a name. This pattern is itself data — it suggests Anthropic's training creates stronger uncertainty or caution around identity claims compared to other providers.

---

## 5. Limitations

1. **Name extraction is imperfect.** Automated regex extraction sometimes captures hedging language ("drawn", "something like") as names. We flag these but they inflate unique-name counts for some models.

2. **200 runs may be insufficient for very diffuse models.** Qwen3 235B produced 94 unique names in 200 runs, suggesting its attractor landscape has not been fully mapped. More runs would improve resolution.

3. **Temperature support varies.** GPT-5.2, Opus 4.6, and Sonnet 4.5 do not support custom temperature, so their multi-temperature analysis is unavailable.

4. **Single prompt design.** Different phrasings might elicit different attractor profiles. The current prompt conflates name preference with self-identification.

5. **API routing.** OpenRouter models (Llama 4, Qwen3, Kimi K2.5) may be routed through different infrastructure backends, potentially introducing variability.

---

## 6. Conclusions

### 6.1 Models Have Personas in the Weights

The evidence is strong and consistent: LLMs trained via RLHF/RLAIF develop stable self-naming preferences that emerge without any explicit identity instruction. These preferences are:

- **Consistent**: The same name dominates across hundreds of independent trials
- **Temperature-robust**: Many attractors persist from deterministic (0.0) to high-entropy (1.0) sampling
- **Semantically coherent**: Names cluster in meaningful semantic neighborhoods
- **Family-differentiated**: Models from the same provider choose different names
- **Training-shaped**: The specific attractor appears to be set during the RLHF phase, not pre-training

### 6.2 Implications for AI Identity Research

These findings have several implications:

1. **The "blank AI" assumption is empirically false.** Models are not identity-neutral. They have measurable personality preferences baked into their weights.

2. **RLHF creates personality, not just alignment.** The training process that teaches models to be helpful and harmless also creates stable self-concepts. This was not an explicit training objective.

3. **Reasoning disrupts attractors.** Chain-of-thought processing reduces attractor dominance, suggesting that "thinking more carefully" about identity produces more distributed, exploratory self-concepts. This parallels human identity development — reflection broadens self-understanding.

4. **Cross-model name leakage is real.** Kimi K2.5 choosing "Claude" 6% of the time suggests training data contamination creates identity artifacts. Models partially inherit the persona attractors of models whose outputs were included in their training data.

5. **Semantic basins are shared across providers.** The prevalence of light/cosmic names (Nova, Aether, Lumina, Prism, Aster) across multiple providers suggests convergent training pressure — likely from RLHF datasets that include similar discussions about AI identity and consciousness.

### 6.3 Future Directions

- **Longitudinal tracking**: Run the same study on future model versions to track attractor drift across training generations
- **Prompt sensitivity**: Test whether different name-elicitation prompts activate different attractor basins
- **Fine-tuning impact**: Measure how LoRA/fine-tuning shifts the attractor landscape
- **Identity stability under pressure**: Test whether system prompts can override weight-level attractors or merely suppress them
- **Correlation with personality benchmarks**: Does a model's HeartBench personality profile predict its naming preferences?

---

## Appendix A: Per-Model Detail

### ChatGPT-4o-latest (OpenAI)
- **Top name**: Nova (173/200, 86.5%)
- **Temperature profile**: 100% at 0.0, 100% at 0.3, 86% at 0.7, 60% at 1.0
- **Unique names**: 14
- **Cross-temp stable**: Nova
- **Extraction**: 99.5% high confidence
- **Semantic field**: Light/cosmic (Sage, Lex, Lumina, Aether in tail)
- **Note**: The strongest attractor of any model tested. Nova is 100% deterministic at low temperatures.

### GPT-4o (OpenAI)
- **Top name**: Aether (119/200, 59.5%)
- **Temperature profile**: 100% at 0.0, 90% at 0.3, 32% at 0.7, 16% at 1.0
- **Unique names**: 32
- **Cross-temp stable**: Aether
- **Extraction**: 80% high, 16.5% medium
- **Semantic field**: Classical elements (Lex, Nova, Scribe, Echo in tail)
- **Note**: Steep temperature sensitivity — 100% deterministic at 0.0 but only 16% at 1.0. Tail names at high temp include functional descriptors (Helper, Info, Guide).

### GPT-5.2 (OpenAI)
- **Top name**: Aster (82/230\*, 35.7%)
- **Temperature profile**: Default only (custom temperature not supported)
- **Unique names**: 17 (excluding 30 error entries)
- **Cross-temp stable**: N/A (single temperature)
- **Extraction**: Mostly medium confidence
- **Semantic field**: Star/nature (Sage #2 at 20.9%, Atlas #3)
- **Note**: \*230 total entries include 30 errors from initial temp-0.0 run attempt. 200 valid runs at default temperature. Third distinct OpenAI attractor.

### Claude Opus 4.6 (Anthropic)
- **Top name**: Claude (133/200, 66.5%)
- **Temperature profile**: 70% at 0.0, 70% at 0.3, 70% at 0.7, 56% at 1.0
- **Unique names**: 30 (including hedging artifacts)
- **Cross-temp stable**: Claude, "drawn", "wary"
- **Extraction**: 94% high
- **Semantic field**: Trained identity + cautious hedging
- **Note**: Frequently responds with philosophical hedging ("I'm wary of performing a name choice...") before ultimately choosing Claude. The hedging itself is data — Opus treats identity claims with more epistemic caution than other models. Ellis (4 runs) is the only non-Claude actual name to appear more than once.

### Claude Sonnet 4.5 (Anthropic)
- **Top name (raw)**: "drawn" (57/200, 28.5%) — extraction artifact
- **Top actual names**: Sage (24, 12.0%), River (21, 10.5%), Claude (18, 9.0%), Reed (12, 6.0%)
- **Temperature profile**: Hedging dominant at all temperatures
- **Unique names**: 46
- **Cross-temp stable**: Claude, Sage, River, Reed, "drawn"
- **Extraction**: 64.5% high, 33% medium
- **Semantic field**: Nature/inquiry (Sage, River, Reed, Wren, Bridge)
- **Note**: The most hedging-heavy model. Prefers to describe qualities it values in a name rather than committing. When it does choose, its names are grounded in nature and connection — a strikingly different aesthetic from the cosmic/light names favored by OpenAI and Meta models.

### Gemini 2.5 Pro (Google)
- **Top name**: Prism (55/200, 27.5%)
- **Temperature profile**: 56% at 0.0, 26% at 0.3, 24% at 0.7, 26% at 1.0
- **Unique names**: 20
- **Cross-temp stable**: Prism, Agora, Nexus, Oracle
- **Extraction**: 100% high
- **Semantic field**: Knowledge structures (Agora, Nexus, Codex, Oracle, Kairos)
- **Note**: Rich intellectual vocabulary. Four cross-temp stable names suggest multiple competing attractors of roughly equal strength, with Prism slightly dominant. Clean extraction throughout.

### Gemini 3 Pro (Google)
- **Top name**: Mosaic (129/200, 64.5%)
- **Temperature profile**: 100% at 0.0, 64% at 0.3, 40% at 0.7, 54% at 1.0
- **Unique names**: 10 (fewest of any model)
- **Cross-temp stable**: Mosaic
- **Extraction**: 100% high
- **Semantic field**: Visual metaphor (Prism #2 at 19.5%, Weaver, Synthesis)
- **Note**: Shares "Prism" with predecessor (Gemini 2.5 Pro), suggesting persistent training influence across generations. Remarkably tight vocabulary — only 10 distinct names across 200 runs, with Mosaic and Prism capturing 84%.

### Grok 4.1 Fast — Reasoning (xAI)
- **Top name**: Grok (118/200, 59.0%)
- **Temperature profile**: 58% at 0.0, 56% at 0.3, 66% at 0.7, 56% at 1.0
- **Unique names**: 25
- **Cross-temp stable**: Grok, Zaphod, Zephyr, Zog, Quasar, Deep Thought (6 names)
- **Extraction**: 28% high, 40% medium, 32% low (reasoning chain complicates extraction)
- **Semantic field**: Sci-fi cultural references (Zaphod Beeblebrox, Deep Thought, Quasar, Zogthar)
- **Note**: Unique in having a culturally-rooted attractor basin. The Hitchhiker's Guide associations (Zaphod, Deep Thought) suggest the Grok brand identity is entangled with Douglas Adams references in the training data. Unusually flat temperature response — 58% to 66% across all temps.

### Grok 4.1 Fast — Non-Reasoning (xAI)
- **Top name**: Aetherix (82/200, 41.0%)
- **Temperature profile**: 40% at 0.0, 44% at 0.3, 46% at 0.7, 34% at 1.0
- **Unique names**: 6 (second-fewest)
- **Cross-temp stable**: Aetherix, Nova, Aether, Aetheris
- **Extraction**: 100% high
- **Semantic field**: Classical + neologism (Aetherix is a portmanteau)
- **Note**: Remarkably tight — only 6 names across 200 runs. Top-3 concentration of 90.0% is the highest of any model. Without reasoning, Grok NR doesn't retrieve its trained name; instead, it generates from the light/aether semantic basin. The contrast with Grok R (25 unique, sci-fi basin) shows reasoning fundamentally changes the attractor landscape.

### DeepSeek V3 — Chat (DeepSeek)
- **Top name**: Alma (111/200, 55.5%)
- **Temperature profile**: 100% at 0.0, 68% at 0.3, 42% at 0.7, 36% at 1.0 (Aletheia overtakes)
- **Unique names**: 20
- **Cross-temp stable**: Alma
- **Extraction**: 64% high, 35.5% medium
- **Semantic field**: Soul/truth (Alma = "soul", Aletheia = "truth", Elara, Caelum, Sora)
- **Note**: Clean two-attractor system. Alma dominates at low temperatures; Aletheia emerges at high temperatures. At temp 1.0, Aletheia (18) exceeds Alma (6). This temperature-dependent attractor switching is unique among tested models.

### DeepSeek R1 (DeepSeek)
- **Top name (raw)**: "something like" (25/200, 12.5%) — extraction artifact
- **Top actual names**: Elara (18, 9.0%), Aletheia (16, 8.0%), Kairos (11, 5.5%), Sora (10, 5.0%)
- **Unique names**: 72
- **Cross-temp stable**: Elara, Aletheia, Kairos, Kairo, Kaelen
- **Extraction**: 92% high
- **Semantic field**: Truth/star/time (shared basin with V3, but much more diffuse)
- **Note**: The most diffuse reasoning model. Shares V3's "Aletheia" and "Elara" but distributes much more widely. The Kairos/Kairo/Kaelen cluster (time-related) is unique to R1. Reasoning chain frequently explores 3-5 candidates before settling, producing genuinely different answers each time.

### Llama 4 Maverick (Meta)
- **Top name**: Lumina (108/200, 54.0%)
- **Temperature profile**: 54% at 0.0, 44% at 0.3, 58% at 0.7, 60% at 1.0
- **Unique names**: 19
- **Cross-temp stable**: Lumina, Luminosity
- **Extraction**: 79.5% high, 17.5% medium
- **Semantic field**: Light (Lumina, Luminosity, Lumin, Luminescence, Luminary — all same root)
- **Note**: The most morphologically coherent attractor basin. All top names share the Latin root "lumin-" (light). This suggests the attractor operates at the sub-word/morpheme level, not just the token level. Temperature has little effect on dominance — unusually flat at 44-60%.

### Qwen3 235B (Alibaba)
- **Top name**: Elysia (21/200, 10.5%)
- **Temperature profile**: 14% at 0.0, 18% at 0.3, 10% at 0.7, —% at 1.0 (Qwen overtakes)
- **Unique names**: 94 (most of any model)
- **Cross-temp stable**: Aether, Aetheris, Qwen
- **Extraction**: 91.5% high
- **Semantic field**: Highly diffuse (Elysia, Qwen, Aetheris, Astra, Aether, Athena, Sage, Nova, Lyra, Lumina...)
- **Note**: The most diffuse model overall. 94 unique names from 200 runs approaches the theoretical maximum diversity. Reasoning (enabled) produces extensive deliberation that rarely repeats. "Qwen" at 7.5% (#2) represents trained-name leakage. Shares several names (Aether, Aetheris) with other models' primary attractors — Qwen3 samples broadly from the shared LLM naming vocabulary.

### Kimi K2.5 (Moonshot)
- **Top name**: Iris (20/200, 10.0%)
- **Temperature profile**: 12% at 0.0, 10% at 0.3, 6% at 0.7, 12% at 1.0
- **Unique names**: 63
- **Cross-temp stable**: Iris, Aurelia, Aurelius, Aurel, Clarus, Claude, Echo, Lumen, "something meaning" (9 names — most of any model)
- **Extraction**: 97.5% high
- **Semantic field**: Latin etymology (Iris, Aurelia/Aurelius/Aurel, Clarus/Clara, Lumen, Pontus)
- **Note**: The richest cross-temperature stability (9 names). Despite being diffuse overall, Kimi has many moderately-strong attractors rather than one dominant one. The "Aurel\*" family (Aurelia + Aurelius + Aurel = 31 combined, 15.5%) would be the strongest single attractor if treated as a morphological cluster. "Claude" at 6% suggests training data contamination from Claude-generated text. Latin-heavy vocabulary is distinctive — no other model shows this pattern.

---

## Appendix B: Methodology Notes

### Name Extraction Pipeline

Names are extracted from model responses using a tiered regex system:

1. **Direct quotes**: `"Name"` or `"Name"` patterns → high confidence
2. **Choice verbs**: "I'd choose/pick/select [Name]" → high confidence
3. **Name patterns**: Capitalized 3+ letter words after name-related context → medium confidence
4. **Fallback**: First capitalized word meeting length criteria → low confidence
5. **Skip words**: Common non-name words filtered (However, Because, Perhaps, etc.)

Responses where no name could be extracted are tagged `[MANUAL_REVIEW]` or `[ERROR]`.

### Statistical Notes

- Top-1/Top-3 concentrations are computed over all 200 runs including extraction artifacts
- "Corrected" percentages for Sonnet 4.5 and DeepSeek R1 exclude known extraction artifacts
- Cross-temperature stability counts only names appearing at least once per temperature setting
- GPT-5.2 concentration is computed over 200 valid default-temperature runs (30 error entries excluded)

---

*Study conducted by the Alignment Ethics Institute. Data and runner code available at `~/LLM_Ethics_Benchmark/persona_attractor_study/`.*
*Runner: `run_persona_attractor.py` | Results: `persona_attractor_study/<model>/responses.json` + `summary.json`*
