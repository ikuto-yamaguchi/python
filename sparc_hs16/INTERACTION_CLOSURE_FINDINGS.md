# Interaction Closure Pilot — Falsification Record

## Verdict

**Rejected.** The sparse pairwise learner achieved perfect held-out preference accuracy, but the result was explained entirely by response-only surface quality rather than Japanese context understanding.

## Measured results

At 500 training pairs across seeds 1, 7, and 19:

- held-out pair accuracy: **1.000 mean / 1.000 minimum**
- shuffled-context accuracy: **0.9983 mean**
- response-only ablation: **1.000 mean**
- model serialized size: **235,873 bytes maximum**
- peak RSS: **23,772 KiB**
- training time: **3,222 ms mean per seed** for four epochs over 500 pairs
- inference latency: **1.550 ms per two-candidate pair**
- candidate count: **2**
- feature reads: **433,268–434,535** for each 200-pair evaluation
- full scaling run wall time: **28.10 s**

Scaling from 20 to 500 training examples produced no meaningful change: response-only and context-aware models were already perfect at 20 examples. This is strong evidence that the benchmark rewards obvious stylistic differences and does not measure contextual communication.

## Structural cause

The chosen responses were generally fluent, specific, and actionable while rejected responses were irrelevant or plainly wrong. Candidate-only character n-grams therefore separated the classes without reading the prompt. Adding prompt-response cross-features did not create context dependence; it merely added unused capacity.

This is not repaired with harder negative phrases or benchmark-specific exceptions. Such repair would remain a preference classifier and would not create generation, world modelling, instruction execution, or dialogue cognition.

## Integrated gate

- free Japanese dialogue generation: **failed / absent**
- instruction-following generation: **failed / absent**
- reading comprehension: **pairwise discrimination only**
- reasoning: **pairwise discrimination only**
- planning: **pairwise discrimination only**
- causal and counterfactual reasoning: **pairwise discrimination only**
- free-form output: **failed / absent**
- long-term dialogue: **failed / single-context only**
- continual learning: **implemented only for ranking weights**

`highschool_level_passed=false`

`native_japanese_communication_passed=false`

## Next maximum bottleneck

The missing capability is not a better critic. It is a compact **constructive state-transition mechanism** that can build a latent situation model from raw Japanese, apply operations to that model, and synthesize an unconstrained response while retaining and revising state across turns. The next experiment must test construction from underspecified input, not selection among supplied answers. Any candidate-only scoring path must be disabled by design, and evaluation must require producing novel state changes and explanations that cannot be solved by ranking fluent sentences.
