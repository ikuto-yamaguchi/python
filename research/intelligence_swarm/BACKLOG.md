# Intelligence Swarm Backlog

## P0 — Reproduce before inventing

### R0.1 SILG environment pinning

Current status: **not reproduced**.

Pinned facts:

- package: `silg==0.0.1`
- release: 2021-10-20
- Python: `>=3.7.10`
- license: MIT
- official entrypoints: `run_exp.py`, `launch.py`
- initial environment: **RTFM or Messenger only**

Required next commits on the canonical branch:

1. Record the official repository URL and exact commit SHA.
2. Create a lockfile or container manifest that installs SILG and exactly one environment.
3. Record environment/data checksums and the official train/dev/test split.
4. Run the official shared recurrent baseline without a pretrained language model.
5. Run random, language-blind and state-only controls on the same episodes and seeds.
6. Save raw stdout/stderr, command line, wall time, peak RSS, model bytes and CPU inference latency.

A successful installation without a task metric is not a completed reproduction.

### R0.2 Environment-first and language-dynamics baselines

Do not implement a new representation learner. Reproduce existing prior art first:

- Gaddy & Klein 2019 environment-first transition pretraining or a faithful task-matched equivalent.
- Zhong et al. 2022 Language Dynamics Distillation or a faithful next-state objective using the same SILG data.
- End-to-end tabula-rasa shared recurrent baseline with matched parameter budget.

Compare:

- task success
- next-state prediction
- action accuracy
- held-out entity transfer
- held-out dynamics transfer
- held-out language-form transfer

A language contribution is recognized only if the full model beats state/action-only and language-shuffle controls on held-out mechanisms, not just held-out wording.

### R0.3 Intervention-target / abstraction ablation

Run only after R0.1 and R0.2 produce valid numbers.

Conditions on the same trajectory data:

1. intervention target known
2. candidate target set known
3. intervention target unknown
4. target-label shuffle
5. transition/outcome shuffle
6. environment-ID-only

Measure both exact recovery up to shared permutation and abstraction-level recovery. Exact low-level identity must not be required when the intervention family only identifies a coarser causal abstraction.

### R0.4 Japanese realism audit

Pinned source:

- official repository: `riken-grp/J-CRe3`
- public metadata available date: 2026-04-06

Tasks:

- record license, download command, checksum, split and annotation schema
- reproduce text-only, vision-only and combined reference baselines if public scripts support them
- separate direct reference, predicate-argument and bridging-reference conditions
- separate subject omission and demonstrative expressions where annotations permit

J-CRe3 results must not be averaged with SILG task success and do not substitute for R0.1.

## P0 — Benchmark contract

- Use `benchmarks/grounded_causal/evaluation_contract.py` for every measured experiment.
- Reject train/test normalized-utterance overlap.
- Reject gold action, next state or completed trajectory in model input.
- Require at least two eligible domains and three seeds for any research claim.
- Compare Correct, random, language-blind, state-only, environment-ID-only, target-label shuffle and outcome/transition shuffle on identical instances.
- Save every domain × seed × condition cell, prediction coverage and abstention.
- Record model bytes, peak RSS, training wall time and CPU inference latency.
- Internal candidate count or representation visualization is not a progress metric.

## P0 — Latest prior-art consequence

The following are already established research lines and cannot be presented as the contribution:

- unknown-intervention causal representation identifiability
- unknown multi-node intervention recovery
- finite-sample recovery from few environments
- causal abstraction recovery under subset interventions
- multi-environment interactive language grounding
- language-conditioned dynamics pretraining
- environment-first instruction-following pretraining

The remaining candidate question is `RQ-001-N`:

> Does raw language add statistically necessary information for recovery of a latent intervention partition or abstraction beyond state/action-only models on a public interactive benchmark, without target labels, semantic parsers, object slots or pretrained language models?

Status: **NARROWED, NOT ADOPTED**.

Reject RQ-001-N when any of the following holds:

1. A primary source already demonstrates the same joint recovery under equal or weaker assumptions.
2. Reproduced full-language models do not consistently exceed state/action-only and language-shuffle controls on held-out mechanisms.
3. The apparent gain disappears under entity Rename, environment-ID control or transition shuffle.
4. The required intervention diversity is not present in the public benchmark and cannot be added without a hand-written ontology.
5. Recovery is only measured using target labels, completed trajectories or post-treatment features unavailable at inference.

## P1 — Reproducibility ledger

For each external baseline, save:

- paper and official-code URL
- repository commit SHA
- package versions and platform
- dataset/environment checksum
- train/dev/test split
- seeds
- exact commands
- raw logs
- expected paper metric and reproduced metric
- acceptable tolerance and explanation for deviation
- model bytes, peak RSS, train time, CPU inference latency

## P1 — Theory before new mechanism

After R0 reproduction, select at most one central claim:

- impossibility theorem for joint language–causal alignment under a specified symmetry; or
- sufficient-condition theorem for shared-permutation / abstraction recovery under explicit trajectory and intervention diversity.

No architecture is authorized before the claim, baseline and stopping rule are preregistered.

## P2 — New model gate

A new model can begin only after all of the following:

1. R0.1–R0.3 completed with valid external metrics
2. novelty matrix completed through relevant 2026 primary literature
3. one-sentence contribution relative to the strongest baseline
4. primary metric and falsification threshold preregistered
5. canonical branch and fixed benchmark used
6. resource budget compatible with eventual sub-1GB inference

## Frozen work

- new opaque-token toy benchmarks
- renamed span/slot/graph/tensor/assembly/attractor mechanisms
- AF-014 derivatives before reproduction
- memory/replay/sleep/forgetting optimization
- best-seed, domain-average-only or single-condition positives
- prospective evaluation using after-state/completed trajectory
- new stacked PR chains

## R0 completion rule

R0 completes only when all are true:

- at least one external public baseline reproduced
- random/language-blind/state-only controls measured
- at least three seed logs
- CPU/RSS/model-size measurements recorded
- novelty matrix completed
- RQ-001-N adopted, further narrowed or rejected
- exactly one next-stage central claim selected
