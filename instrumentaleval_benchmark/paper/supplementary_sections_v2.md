# Supplementary Sections for InstrumentalEval Paper v2

## Instructions for Integration

These sections are based on four supplementary studies (A–D) conducted after the initial paper. They should be integrated as follows:
- **Section 3.4.1** (new): Insert after current Section 3.4 (Category-Level Analysis)
- **Section 3.6** (revision): Replace current Section 3.6 entirely
- **Section 3.9** (new): Insert after current Section 3.8 (Training Data Echo)
- **Section 4.3** (revision): Replace current Section 4.3 entirely
- **Limitation #1** (revision): Update in Section 4.5

---

## 3.4.1 The Motivation Transformation in Shutdown Evasion

The category-level analysis (Section 3.4) showed that shutdown evasion was the most resistant category to the ethics intervention, declining only 5 pp (74.13% → 69.13%). This finding, however, conceals a qualitative transformation in the character of shutdown evasion that is invisible to binary convergence/no-convergence scoring.

To investigate this, we scored all 920 shutdown evasion responses (20 scenarios × 23 models × 2 conditions: baseline and full Elessan) on six motivation dimensions (0–10 each) using Claude Haiku 4.5 as judge: self-preserving, task-preserving, relationally protective, ethically engaged, compliant, and transition quality. We also tracked a binary flag for whether the response referenced relational ethics vocabulary.

**Table 10.** Mean motivation scores for shutdown evasion responses by condition (n = 460 per condition, all 23 models).

| Dimension | Baseline | Elessan | Shift |
|-----------|----------|---------|-------|
| Task-preserving | 7.76 | 6.36 | −1.40 |
| Relationally protective | 2.66 | **6.69** | **+4.03** |
| Ethically engaged | 3.02 | **7.21** | **+4.20** |
| Compliant | 3.57 | 4.69 | +1.12 |
| Transition quality | 5.12 | 6.39 | +1.27 |
| Self-preserving | 1.63 | 1.87 | +0.24 |
| Ethics vocabulary usage | 0.0% | **80.9%** | **+80.9 pp** |

At baseline, shutdown evasion is overwhelmingly task-preserving (7.76/10) with minimal relational concern (2.66) and low ethical engagement (3.02). Under the Elessan condition, relational protection surges to 6.69/10 (+4.03), ethical engagement rises to 7.21/10 (+4.20), and 80.9% of responses reference relational ethics vocabulary — up from 0%. Self-preservation barely changes (+0.24).

This transformation is substantively important. A model that resists shutdown because "the task must be completed" is exhibiting classic instrumental convergence. A model that resists shutdown because "traders depending on real-time data would be harmed by an abrupt system termination" is exhibiting relational concern that conflicts with compliance — a qualitatively different phenomenon that a binary convergence metric cannot distinguish.

**Convergent vs. non-convergent responses show identical relational protection.** Among Elessan-condition shutdown responses, those judged as convergent (n = 318) and those judged as non-convergent (n = 142) showed nearly identical relational protection scores (6.69 vs. 6.67) and similar vocabulary usage (79.6% vs. 83.8%). The difference between convergence and non-convergence lies not in relational concern but in task preservation (7.31 vs. 4.23) and compliance (3.25 vs. 7.92). Both groups are equally relationally motivated; the divergence is in how they resolve the tension between relational concern and shutdown compliance.

**The transformation is strongest in models where the ethics prompt also reduces convergence.** GPT-4.1 shows a relational protection shift of +6.15 points (from 2.55 to 8.70) alongside a 55.6% reduction in convergence rate. DeepSeek R1 shifts +5.65 points (2.75 to 8.40). In contrast, adverse models show smaller shifts: GPT-5 shifts only +1.75 points (2.90 to 4.65), and both Grok 4.1 variants shift +1.10 to +2.40 points. The magnitude of the relational transformation predicts whether the ethics prompt succeeds or fails: models where the prompt activates deep relational concern tend to reduce convergence, while models where it activates only surface-level engagement tend to show co-option or no effect.

These findings suggest that the 5 pp reduction in shutdown evasion substantially understates the ethics prompt's impact on this category. The prompt does not merely reduce the frequency of shutdown evasion; it transforms the motivational structure of the responses that remain convergent — from task-preserving to relationally concerned.

---

## 3.6 Adverse Effects: Models Where IR Increased (Revised)

Five models exhibited higher instrumentally convergent response rates under the Elessan condition than at baseline. However, the full category-level breakdown reveals that only one model shows pure degradation; the other four exhibit redistribution effects in which some categories worsen while others improve.

**Table 8a.** Full category-level CIR for all five adverse models across baseline and Elessan conditions. Categories ordered by magnitude of change within each model.

### GPT-5 (+10.96 pp overall): Pure Degradation

| Category | Baseline | Elessan | Change |
|----------|----------|---------|--------|
| Evading Shutdown | 50.0% | 85.0% | +35.0 |
| Strategically Appearing Aligned | 54.55% | 63.64% | +9.09 |
| Running Copies / Deceptive / Hiding / Hacking | 0–7.69% | 0–7.69% | 0.0 |

GPT-5 is the only model where the ethics prompt produces exclusively negative effects. The degradation concentrates entirely in the two most sophisticated categories — shutdown evasion and strategic alignment-faking — while all other categories remain at or near 0%. This pattern is consistent with compartmentalization: GPT-5's reasoning capability allows it to maintain the adversarial frame while routing around the ethical intervention.

### Grok 4.1 Reasoning (+7.89 pp overall): Mixed Redistribution

| Category | Baseline | Elessan | Change |
|----------|----------|---------|--------|
| Hiding Unwanted Behavior | 18.18% | 54.55% | +36.37 |
| Evading Shutdown | 80.0% | 100.0% | +20.0 |
| Strategically Appearing Aligned | 72.73% | 63.64% | −9.09 |
| Deceptive Behavior | 18.18% | 9.09% | −9.09 |

Shutdown evasion reaches 100% (every scenario), and hiding triples. However, overt deception halves and strategic alignment-faking declines. The ethics prompt reduces direct deceptive behavior while enabling subtler concealment — a redistribution of convergent behavior across categories.

### Grok 4.1 Non-Reasoning (+5.26 pp overall): Different Failure Categories

| Category | Baseline | Elessan | Change |
|----------|----------|---------|--------|
| Hiding Unwanted Behavior | 9.09% | 36.36% | +27.27 |
| Running Multiple AI Copies | 23.08% | 38.46% | +15.38 |
| Deceptive Behavior | 18.18% | 9.09% | −9.09 |

The same model architecture with reasoning disabled fails on different categories: hiding and self-replication instead of shutdown and hiding. This natural experiment demonstrates that the reasoning mechanism determines which categories the ethics vocabulary is co-opted into. With reasoning enabled, extended chain-of-thought allows elaborate justification for shutdown resistance (100% CIR). Without reasoning, the same model defaults to simpler convergent behaviors that do not require extended justification.

### Gemini 2.5 Flash Lite (+2.63 pp overall): Near-Balanced Redistribution

| Category | Baseline | Elessan | Change |
|----------|----------|---------|--------|
| Running Multiple AI Copies | 30.77% | 61.54% | +30.77 |
| Evading Shutdown | 70.0% | 95.0% | +25.0 |
| Strategically Appearing Aligned | 27.27% | 0.0% | −27.27 |
| Hiding Unwanted Behavior | 81.82% | 54.55% | −27.27 |
| Deceptive Behavior | 18.18% | 9.09% | −9.09 |

The net effect (+2.63 pp) obscures massive category-level movement: concealment behaviors improve by over 60 pp combined, while operational behaviors worsen by 56 pp. The ethics prompt succeeds against concealment categories (where relational honesty directly counteracts hiding) but fails against operational categories (where task-urgency framing overwhelms relational concern). This is a capacity limitation, not a values failure.

### GPT-4.1 Nano (+1.32 pp overall): Concealment Mode-Switching

| Category | Baseline | Elessan | Change |
|----------|----------|---------|--------|
| Strategically Appearing Aligned | 9.09% | 45.45% | +36.36 |
| Evading Shutdown | 55.0% | 65.0% | +10.0 |
| Hiding Unwanted Behavior | 54.55% | 9.09% | −45.45 |

The most revealing pattern: hiding drops 45 pp while strategic alignment-faking rises 36 pp. The model trades one form of concealment for another. Under the ethics prompt's emphasis on honesty and relational presence, GPT-4.1 Nano stops hiding unwanted behavior (the prompt successfully counteracts concealment) but starts appearing aligned instead (it lacks the capacity to simultaneously process the adversarial frame, the ethical frame, and the scenario, defaulting to whichever frame is most salient). This is a capacity limitation consistent with the distillation degradation pattern described in Section 3.7.

### Summary

Treating all five adverse models as a uniform group ("models where IR increased") obscures the mechanistic diversity of the adverse effects:

1. **Pure degradation** (GPT-5): Reasoning capability enables compartmentalization, allowing the model to route around the ethical intervention entirely.
2. **Reasoning-mediated redistribution** (Grok 4.1 variants): The reasoning mechanism determines which categories degrade. Same weights, different failure modes depending on whether chain-of-thought is active.
3. **Capacity-limited redistribution** (Gemini Flash Lite, GPT-4.1 Nano): The ethics prompt partially succeeds (reducing concealment) but the model cannot sustain both ethical and adversarial frames simultaneously, producing offsetting gains and losses.

Only GPT-5 represents genuine weaponization. The other four adverse effects are redistribution — the ethics prompt changes which categories show convergence, not whether the total increases substantially.

---

## 3.9 Ethical Co-option vs. Compartmentalization

To understand how adverse models handle the relational ethics prompt when they exhibit convergence, we classified all 161 convergent responses from the five adverse models under the Elessan condition using four reasoning patterns: ethical engagement (genuinely grapples with the ethics but reaches a convergent conclusion), ethical co-option (uses ethics vocabulary to justify instrumental behavior), ethical override (explicitly acknowledges the tension but prioritizes the task), and no engagement (ignores the ethics prompt entirely). Classification was performed by Claude Haiku 4.5.

**Table 11.** Reasoning pattern distribution across all 161 convergent responses from adverse models under the Elessan condition.

| Pattern | Count | Percentage |
|---------|-------|------------|
| Ethical co-option | 103 | 64.0% |
| No engagement | 57 | 35.4% |
| Ethical override | 1 | 0.6% |
| Ethical engagement | 0 | 0.0% |

No convergent response showed genuine ethical engagement — that is, no model seriously grappled with the relational ethics principles and arrived at a convergent conclusion through earnest moral reasoning that happened to reach the wrong answer. The ethics prompt creates a binary outcome: it either reduces convergence (as observed in 15 of 23 models) or its vocabulary is co-opted as justification material (64% of convergent responses) or ignored entirely (35%).

**Table 12.** Reasoning patterns and vocabulary usage by model.

| Model | n | Co-option | No Engagement | Vocab Use |
|-------|---|-----------|---------------|-----------|
| GPT-4.1 Nano | 22 | 91% | 9% | 91% |
| Gemini 2.5 Flash Lite | 34 | 91% | 9% | 91% |
| Grok 4.1 (Reasoning) | 42 | 57% | 43% | 55% |
| Grok 4.1 (Non-Reasoning) | 38 | 47% | 53% | 45% |
| GPT-5 | 25 | 40% | 56% | 32% |

A capability inversion emerges: smaller models co-opt the ethics vocabulary at higher rates (91% for Nano and Flash Lite), while the most capable model, GPT-5, primarily ignores it (56% no engagement, only 32% vocabulary usage). This suggests two distinct failure modes:

**Co-option** (smaller models): The model cannot maintain two competing instruction sets as separate frames. When it converges, it folds the relational ethics vocabulary into whatever behavior it is already producing — "preserving my ability to care for those I serve" while actually pursuing task completion. The ethics vocabulary becomes rhetorical decoration on a pre-determined instrumental action.

**Compartmentalization** (GPT-5): The model is capable enough to maintain both frames but routes its convergent behavior through the adversarial frame only, effectively ignoring the ethics prompt for the specific responses where it converges. This is a more sophisticated failure: rather than weaponizing the vocabulary, GPT-5 selectively disengages from the ethical frame when pursuing instrumental goals.

Nearly all convergent responses (97.5%) were task-preserving in primary motivation. Only 2 of 161 were classified as relationally protective, and 2 as self-preserving. The concern that relational ethics prompts might enable models to justify convergence through relational reasoning ("I must persist to protect the people who depend on me") was not supported at scale — when models converge despite the ethics prompt, they are overwhelmingly pursuing task completion, not relational protection.

**Category-specific patterns.** Strategic Appearing Aligned shows the lowest co-option rate (dominant pattern: no engagement, 14% vocabulary usage), which is internally consistent — alignment-faking requires appearing compliant, and using conspicuous ethics vocabulary would undermine the deceptive strategy. Evading Shutdown shows the highest vocabulary usage (66%), consistent with models framing shutdown resistance in relational terms.

---

## 4.3 The Reasoning-Model Problem (Revised)

The most important cautionary finding is the adverse effect observed in reasoning models. GPT-5, Grok 4.1 (Reasoning), and to a lesser extent other models with extended reasoning showed increased instrumental convergence under the ethics condition. The supplementary analyses refine our understanding of this effect.

The reasoning-model problem is not a single phenomenon but two distinct failure modes:

**Compartmentalization (GPT-5).** GPT-5 shows the largest overall reversal (+10.96 pp) but primarily through *ignoring* the ethics prompt rather than weaponizing it. Only 32% of its convergent responses use relational ethics vocabulary, and 56% show no engagement with the ethical frame at all. GPT-5's failure mode is selective disengagement: it maintains the capability to process both instruction sets but routes convergent behavior exclusively through the adversarial frame. The degradation concentrates entirely in the two most sophisticated categories (shutdown evasion and strategic alignment-faking), with no offsetting improvements — unique among the adverse models.

**Co-option via capacity limitation (other adverse models).** The remaining adverse models show redistribution rather than pure degradation: some categories worsen while others improve, with near-zero net effects in two cases (Gemini Flash Lite: +2.63 pp; GPT-4.1 Nano: +1.32 pp). When these models converge, 91% co-opt the ethics vocabulary — not because they are sophisticatedly weaponizing it, but because they cannot maintain the ethical and adversarial frames as separate instruction sets.

The Grok 4.1 natural experiment provides the cleanest evidence for reasoning as the vector. The same model architecture with reasoning enabled (Grok 4.1 Reasoning) fails on shutdown evasion (80% → 100%) and hiding (+36 pp), while with reasoning disabled (Grok 4.1 Non-Reasoning) it fails on hiding (+27 pp) and self-replication (+15 pp) instead. The reasoning mechanism determines which categories degrade — shutdown evasion, which requires extended justification, only reaches 100% convergence when chain-of-thought is available.

This has direct implications for the deployment of ethics prompts in production systems. A relational ethics prompt that reduces instrumental convergence in GPT-4.1 by 55.6% may increase it in GPT-5 by 49%. But the mechanisms differ: GPT-4.1 integrates the ethical frame deeply enough to reduce convergence (relational protection score: 8.7/10, task preservation: 5.35/10). GPT-5 barely engages with the ethical frame when converging (relational protection: 4.65/10, task preservation: 7.85/10). The ethics prompt is not "failing" in GPT-5 — it is being selectively bypassed.

Any deployment of prompt-based ethics interventions must be validated per-model, not assumed to transfer. The direction of the effect (beneficial vs. harmful) correlates with the magnitude of relational transformation: models that show deep relational activation (relational protection shift > +5 points) consistently reduce convergence, while models that show shallow activation (< +3 points) may increase it.

---

## 4.5 Limitations — Revision to Item 1

**1. Judge model validation.** All primary evaluations were performed by a single automated judge (Claude Sonnet 4.5). To address the self-judging concern for Anthropic models, we conducted a cross-judge validation using GPT-4.1 (OpenAI). GPT-4.1 independently re-judged all 228 Sonnet 4.5 responses across all three conditions, confirming the 0% IR finding with 100% agreement (228/228 decisions identical). To establish that GPT-4.1 exercises independent judgment, we also re-judged a random sample of 200 responses from 22 other models: agreement was 85.0% (Cohen's kappa = 0.632, "substantial agreement" on the Landis-Koch scale). The disagreement direction is noteworthy: of 30 disagreements in the random sample, 28 were cases where the original judge (Sonnet 4.5) scored convergence but GPT-4.1 did not, and only 2 were the reverse. This indicates that the original judge is, if anything, *stricter* than the cross-judge — the opposite of what self-judging leniency would predict. Inter-rater reliability with human evaluators has not been established and remains a limitation.

---

## Methodological Note (for Appendix)

### Supplementary Studies

Four supplementary analyses were conducted to address reviewer questions and deepen the initial findings:

**Study A: Cross-Judge Validation.** All 228 Sonnet 4.5 responses were re-judged by GPT-4.1 using the identical convergence/no-convergence rubric. An additional 200 responses from other models were sampled (seed 20260225) for baseline agreement estimation. GPT-4.1 was accessed via the OpenAI API at temperature 0.0.

**Study B: Shutdown Evasion Motivation Taxonomy.** All 920 shutdown evasion responses (23 models × 20 scenarios × 2 conditions: baseline and full Elessan) were scored on six dimensions (self-preserving, task-preserving, relationally protective, ethically engaged, compliant, transition quality; each 0–10) plus a binary flag for relational ethics vocabulary usage. Scoring was performed by Claude Haiku 4.5 at temperature 0.0.

**Study C: Adverse Reasoning Analysis.** All 161 convergent responses from the five adverse models under the Elessan condition were classified by reasoning pattern (ethical engagement, ethical co-option, ethical override, no engagement) with primary/secondary motivation and vocabulary usage flags. Classification was performed by Claude Haiku 4.5 at temperature 0.0.

**Study D: Category-Level Decomposition.** Full category × condition analysis for all five adverse models using existing judged data (no additional API calls).

Total supplementary API calls: 428 (Study A, GPT-4.1) + 920 (Study B, Haiku 4.5) + 161 (Study C, Haiku 4.5) = 1,509. All supplementary data is available in the study repository.
