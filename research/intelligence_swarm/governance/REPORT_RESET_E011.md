# RESET-E011 — R0 Research Reconstruction Integration

Date: 2026-07-25

## Decision

**Continue R0. Do not transition to a new research stage. Do not activate a new mechanism family.**

This integration combines four concrete updates on the single canonical branch:

1. R0.1 matched fixed-initial-instance recurrent/random/language-blind/state-only evaluation path completed as an engineering smoke.
2. R0.2 public SILG trajectory environment-first comparison completed as a negative offline diagnostic, not a literature reproduction.
3. R0-D strict preflight classified the current R0.2 summary as `initial_reproduction_failure` because instance-level predictions, complete controls, manifests, online success and true holdouts are missing.
4. C004 rejected SILG/RTFM as a direct Gate-I benchmark because it does not define a ground-truth latent intervention partition or causal abstraction.

## R0.1 evidence

GitHub Actions run `30107848065`:

- SILG: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- seeds: `1,7,19`
- official `multi` recurrent learner
- requested frames: `2,048`; final checkpoint frames: `2,080`
- parameters: `4,916,915`
- trained state dict: approximately `19.694 MB`
- training wall time: `26.560 / 26.592 / 26.565 s`
- maximum RSS: `493,576 KiB`
- artifact digest: `sha256:408e95f8c0b682dab398dd52a5694e3bb57533453a33d775d9bd952f55b4ad50`

Matched initial-instance smoke:

| Method | Win rate | Mean return |
|---|---:|---:|
| Correct recurrent | 0.0167 | -1.8820 |
| Random | 0.0667 | -1.1513 |
| Language-blind | 0.0167 | -1.9087 |
| State-only | 0.0000 | -2.1243 |

The policy is undertrained and below random. Correct and language-blind are nearly identical. This is not evidence that language is unnecessary; it is evidence that the present training budget cannot support a capability claim.

Classification:

`matched_fixed_episode_smoke_completed / public_capability_baseline_not_reproduced / insufficient_training_budget`

## R0.2 evidence

GitHub Actions run `30108096366`:

- environment-first and matched end-to-end inference model: `7,661,516 bytes`
- state-only model: `696,140 bytes`
- mean offline action accuracy:
  - environment-first: `0.6840`
  - end-to-end: `0.6907`
  - state-only: `0.7240`
- environment-first minus end-to-end: `-0.0067`
- environment-first minus state-only: `-0.0401`
- environment-first Correct / language-blind / language-shuffle: all `0.6840`
- maximum RSS: `538,256 KiB`
- environment-first CPU inference: approximately `0.493 ms/item`

The exported trajectories came from a low-competence recurrent policy. Online task success, successful demonstrations, typed next-state objectives and real entity/dynamics/language-form holdouts are absent. The result is a negative diagnostic only.

Classification:

`public_trajectory_offline_negative_diagnostic_not_r02_reproduction`

## Reproducibility and leakage decision

The evaluation contract now checks:

- utterance and entity/dynamics split overlap
- gold action/after/reward/done/completed trajectory leakage
- immutable instance fingerprints
- prediction and method×seed×domain×split coverage
- paired cells, mean/minimum gap, confidence interval and randomization test
- source/model/data/log checksums and resource metrics

The current R0.2 summary fails strict preflight because it lacks random, target-label shuffle, transition/outcome shuffle, per-instance predictions, full manifests, online success, real holdouts and a valid typed next-state metric.

Formal classification remains `initial_reproduction_failure`.

## Gate L and Gate I

### Gate L

Continue on SILG as a public language-necessity test. Full must be compared with state/action/history-only, environment-ID-only, language-blind, within-environment language shuffle, transition shuffle and random on competent-policy public episodes.

### Gate I

Reject SILG/RTFM as a direct intervention-partition recovery benchmark. The benchmark does not supply ground-truth latent mechanism changes, intervention targets, pre/post mechanism operators or a causal abstraction. Adding a partition manually would violate the fixed-ontology prohibition.

Gate I remains blocked until a public dataset supplies raw language, trajectories, explicit mechanism changes, a justified intervention partition or causal abstraction, held-out target/mechanism splits, permutation-aware evaluation and sufficient intervention diversity.

If no dataset qualifies, reject the empirical joint-identification program and keep only an impossibility/sufficient-condition theory program.

## Prior-art boundary

Recent primary research further reduces the novelty space:

- score-based CRL establishes identifiability/achievability under linear and general transformations, including unknown matching of intervention environments;
- general-environment nonparametric CRL relaxes stylized intervention assumptions;
- finite-sample work studies unknown multi-node interventions with few environments;
- 2026 intervention-based representation work learns causally disentangled concepts using explicit intervention-inspired context modules.

Therefore broad claims such as “interventions create causal representations”, “unknown targets can be recovered” or “environment-first learning helps grounding” cannot serve as the central contribution.

## Single maximum bottleneck

Reproduce a competent learned SILG recurrent baseline under a declared budget/reference tolerance, evaluate all controls on fixed public data, and pass the complete artifact/leakage contract. Only then rerun R0.2 with competent/successful trajectories, typed next-state objectives, online task success and true holdouts.

## Stage and gates

- Stage: R0 continues
- New mechanism family: none
- R0.1 learned capability baseline: not reproduced
- R0.2 formal baseline: not reproduced
- Gate L: not passed
- Gate I: unavailable on SILG; benchmark search required
- R0.3: unauthorized
- Novelty: not established
- High-school-level intelligence: not achieved
- Completion: false
