# Intelligence Swarm Backlog

## P0 — Reproduce before inventing

### R0.1 SILG environment and baseline reproduction

Current status: **public environment and random control reproduced; official shared recurrent baseline not reproduced**.

Completed:

- SILG commit `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Ubuntu 22.04 / Python 3.8.18 installation
- resolved `pip freeze`
- `rtfm_train_s1-v0` schema probe
- random-valid-action control: 60 public episodes across seeds 0/1/2
- raw install/probe logs, host manifest and SHA-256 bundle
- workflow artifact digest recorded

Random-control result:

- 8 wins / 60 episodes
- aggregate win rate 0.1333
- mean return -1.0237
- mean episode length 15.5167
- random action selection 7.324 µs/action

Required next commits on the canonical branch:

1. Change canonical seeds to `1,7,19`.
2. Add deterministic episode-instance capture/replay so every method sees identical worlds.
3. Run the official shared recurrent baseline without a pretrained language model.
4. Run random, language-blind, state-only and language-shuffle controls on identical instances.
5. Save model bytes, peak RSS, training wall time and CPU inference latency for every learned method.
6. Compare reproduced official metric to the paper/code reference with a declared tolerance.
7. Run the test split `rtfm_test_s1-v0`; train-environment random control alone is not a task reproduction.

R0.1 completion requires a learned official or faithful recurrent baseline and matched controls. Installation/schema/random-only success does not complete it.

### R0.2 Environment-first and language-dynamics baselines

Do not implement a new representation learner. Reproduce existing prior art first:

- Gaddy & Klein 2019 environment-first transition pretraining or a faithful task-matched equivalent.
- Zhong et al. 2022 Language Dynamics Distillation or a faithful next-state objective using the same SILG data.
- End-to-end tabula-rasa shared recurrent baseline with matched parameter budget.

The synthetic-fixture harness is a pipeline smoke test only and must not enter the research score table.

After R0.1 instance replay exists, compare on identical RTFM instances:

- task success
- next-state prediction
- action accuracy
- held-out entity transfer
- held-out dynamics transfer
- held-out language-form transfer
- model bytes
- peak RSS
- training wall time
- CPU inference latency

A language contribution is recognized only if the full model beats state/action/history-only and language-shuffle controls on held-out mechanisms, not merely held-out wording.

### R0.3 Intervention-target / abstraction ablation

Run only after R0.1 and R0.2 produce valid public numbers.

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
- Require at least two eligible domains and three canonical seeds for any research claim.
- Canonical seeds are `1,7,19`; runs using other seeds are engineering checks unless preregistered.
- Compare Correct, random, language-blind, state-only, environment-ID-only, target-label shuffle and outcome/transition shuffle on identical instances.
- Save every domain × seed × condition cell, prediction coverage and abstention.
- Record model bytes, peak RSS, training wall time and CPU inference latency.
- Require raw logs, package lock, repository SHAs, dataset/environment checksum and artifact digest.
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
- language-feature-conditioned intervention distribution modeling

The remaining candidate question is `RQ-001-N2`:

> On a fixed public interactive benchmark, does raw language contain statistically necessary information about an intervention partition or causal abstraction beyond state, action, history and environment identity, and can that information be recovered up to joint permutation without target labels, semantic parsers, object slots, pretrained language models or supplied perturbation-feature semantics?

Status: **NARROWED, NOT ADOPTED**.

Reject RQ-001-N2 when any of the following holds:

1. A primary source already demonstrates the same joint recovery under equal or weaker assumptions.
2. Reproduced full-language models do not consistently exceed state/action/history-only and language-shuffle controls on held-out mechanisms.
3. The apparent gain disappears under entity Rename, environment-ID control or transition shuffle.
4. The required intervention diversity is absent from the public benchmark and cannot be added without a hand-written ontology.
5. Recovery is measured using target labels, completed trajectories or post-treatment features unavailable at inference.
6. Recovery is only exact-name recovery and vanishes under a shared latent/language permutation.
7. The strongest result is restricted to a synthetic fixture rather than the pinned public split.

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
- workflow run ID and artifact digest
- expected paper metric and reproduced metric
- acceptable tolerance and explanation for deviation
- model bytes, peak RSS, train time, CPU inference latency

Current ledger entry:

- Workflow run: `30101406916`
- Artifact: `r0-silg-rtfm-probe-30101406916`
- Digest: `sha256:ed463e76d5c528b2cf25d740847c77978dbe66d0ed5455a57289519ba0455afd`
- Status: installation/schema/random control success; baseline reproduction incomplete

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
- treating random-control reproduction as intelligence progress
- treating synthetic-fixture scores as public benchmark evidence

## R0 completion rule

R0 completes only when all are true:

- at least one learned external public baseline reproduced
- random/language-blind/state-only controls measured on identical instances
- at least three canonical seed logs
- CPU/RSS/model-size measurements recorded
- novelty matrix completed
- RQ-001-N2 adopted, further narrowed or rejected
- exactly one next-stage central claim selected
