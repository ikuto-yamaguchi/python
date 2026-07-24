# C Identifiability Protocol 001

## Status

Design contract only. This is not a capability result and not a new mechanism.

## Goal

Measure whether raw language contributes to recovery and use of latent intervention structure beyond what can be obtained from state/action trajectories alone.

## Phase order

### Phase 0 — Public baseline reproduction

Use an official SILG task and shared recurrent baseline without a pretrained language model.

Required artifacts:

- pinned repository commit
- pinned Python and dependency versions
- exact environment/task and split
- official training command or a line-by-line faithful equivalent
- seeds 1, 7, 19
- raw stdout/stderr logs
- task success and episode return
- parameter bytes, checkpoint bytes, peak RSS
- training wall time and CPU inference latency

No hidden-intervention modification is allowed before Phase 0 succeeds.

### Phase 1 — Information controls

Train/evaluate on the same episodes and random seeds:

1. full language + state + action history;
2. state + action history, language removed;
3. language only, state masked;
4. language shuffled across episodes within environment;
5. transition pairs shuffled within environment;
6. environment ID only;
7. random policy.

The implementation must guarantee identical episode IDs and evaluation instances across conditions.

### Phase 2 — Dynamics objective reproduction

Implement or reproduce a language-conditioned next-state/dynamics objective comparable to Language Dynamics Distillation.

Report:

- next-observation or state-change prediction;
- policy task success after pretraining;
- sample efficiency at fixed environment steps;
- held-out entity, dynamics and language-form transfer.

A representation probe alone is insufficient.

### Phase 3 — Hidden-intervention-target split

Only after Phases 0–2:

- remove explicit labels for which entity/state component an action affects;
- group data into multiple uncoupled intervention environments;
- preserve repeated causal mechanisms across entity rename and instruction paraphrase;
- hold out combinations of mechanism × entity × language form;
- evaluate recovery only up to a shared permutation.

## Primary metrics

1. held-out task success;
2. held-out next-state prediction;
3. intervention-target partition adjusted Rand index, after optimal shared permutation matching;
4. cross-expression equivalence retrieval accuracy;
5. counterfactual action consequence accuracy;
6. non-target preservation accuracy.

## Claim gate

A joint language-causal result requires all of the following over seeds 1, 7, 19:

- full model exceeds state/action-only by at least 0.10 absolute on held-out task success or counterfactual consequence accuracy;
- full model exceeds language-shuffle and transition-shuffle by at least 0.10;
- latent intervention partition is stable across renamed entities and paraphrased instructions;
- cross-expression equivalence survives a complete vocabulary rename;
- no final outcome, target label, completed trajectory or test-domain dictionary enters training or model selection;
- the same advantage appears in at least two environment families.

Until these conditions pass, results are reproduction, diagnosis or falsification—not intelligence progress.

## Identifiability failure tests

Before training a new model, generate paired datasets that are observationally equivalent under a joint permutation of:

- latent variables;
- instruction families;
- action labels where the environment permits relabeling.

If the predictor receives no observable that distinguishes the pair, exact semantic labels cannot be a valid metric. Evaluation must be permutation-invariant or the task must add an explicit symmetry breaker.

## Stop conditions

Reject or further narrow the candidate research question when:

- the full language model does not beat state/action-only controls;
- performance disappears under entity rename while dynamics are unchanged;
- recovery depends on explicit environment or intervention labels;
- public baseline reproduction cannot be stabilized;
- the apparent contribution reduces to response equality, clustering, candidate filtering or a benchmark-specific parser.

## Resource ceiling

For reconstruction experiments:

- model/checkpoint under 1 GB;
- CPU inference measured batch size 1;
- peak RSS recorded;
- no external LLM or retrieval system;
- pretrained language models excluded from the primary claim, but may be recorded as an out-of-scope upper baseline.
