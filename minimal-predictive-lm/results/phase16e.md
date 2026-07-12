# Phase 16e results: norm-aware causal core

This phase introduces a structured causal adjudicator before attempting
natural-language compilation. No public benchmark examples or targets are used.

## Results

- runtime payload: **307 bytes**
- renamed and reordered causal scenarios: **200/200**
- intentionality cases: **6/6**
- irrelevant-variable invariance: **5/5**
- maximum causal operations: **4**

## Claim boundary

The measured claim is limited to the structured threshold-causal fragment.
Public natural-language causal judgement remains unopened because this phase
does not yet infer events, norms, equations, duties, or temporal paths from prose.

## Limitations

- the causal core receives structured variables, normal values, and an outcome equation
- natural-language extraction is not implemented in this phase
- the current outcome language is a single threshold equation rather than an arbitrary causal DAG
- normality declarations are supplied rather than autonomously learned from culture or context
- proximate causation, omissions with duties, and multi-stage preemption require a richer graph
- the phase creates a causal foundation but does not improve the public causal score yet
