# Intelligence Swarm Backlog

## P0 — R0.1 learned public capability baseline

Current status: **matched fixed-initial-instance smoke completed; learned public capability baseline not reproduced**.

### Completed

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Ubuntu 22.04 / Python 3.8.18 and resolved dependency lock
- RTFM S1 schema probe and random-valid-action public control
- official SILG `multi` recurrent 3-seed training/checkpoint path
- checkpoint save/reload
- Correct / Random / Language-blind / State-only from identical independently seeded initial test instances
- parameters、model bytes、RSS、training time、CPU latency、artifact digest
- evaluation contract adapters and leakage/artifact regression tests

### Engineering values

- parameters: `4,916,915`
- trained state dict: approximately `19.694 MB`
- training wall time: `26.560 / 26.592 / 26.565 s`
- maximum peak RSS: `493,576 KiB`
- matched smoke Correct win rate: `0.0167`
- matched smoke Random win rate: `0.0667`
- matched smoke Language-blind win rate: `0.0167`
- artifact digest: `sha256:408e95f8c0b682dab398dd52a5694e3bb57533453a33d775d9bd952f55b4ad50`

These values establish the public training/evaluation path only. They do not reproduce the published capability baseline.

### Only authorized R0.1 work

1. Increase official recurrent training budget with checkpointed learning curves until convergence evidence or a declared resource ceiling.
2. Freeze one canonical `rtfm_test_s1-v0` evaluation set for seeds `1,7,19`; store complete dataset SHA-256 and instance fingerprints.
3. Evaluate the same learned checkpoints and all controls:
   - official recurrent
   - random
   - language-blind
   - state-only
   - environment-ID-only
   - within-environment language shuffle
   - outcome/transition shuffle
   - target-label shuffle only if an operational target proxy exists without gold ontology
4. Export per-instance predictions with complete method × seed × split coverage.
5. Record raw-log/model/data SHA-256, exact source commit, model bytes, RSS, train time and CPU latency.
6. Pass `evaluation_contract.py` before interpreting scores.
7. Compare against the paper/code reference score using a preregistered tolerance.

R0.1 completes only when a learned recurrent policy and controls are validly compared on fixed public test data and the artifact/leakage contract passes.

## P0 — Evaluation and artifact contract

Every measured experiment must pass:

- train/test normalized utterance overlap check
- entity and dynamics split overlap check
- gold action、next state、reward、done、post-treatment state、completed trajectory leakage check
- canonical seeds `1,7,19`
- immutable instance fingerprint agreement
- complete method × seed × domain × split coverage
- prediction coverage and duplicate prediction audit
- domain × seed × condition cells
- paired mean gap、minimum cell gap、95% CI、paired randomization test
- source/model/data/log checksums and exact code commit
- model bytes、peak RSS、training wall time、CPU inference latency

Current R0.1/R0.2 formal classification: **`initial_reproduction_failure`** because full controls, complete manifests, valid public ability reference comparison and online/holdout metrics remain absent.

## P1 — R0.2 Environment-first reproduction

Current status: **public trajectory negative diagnostic completed; formal reproduction not completed**.

Observed on undertrained SILG policy trajectories:

- environment-first action accuracy: `0.6840`
- matched end-to-end: `0.6907`
- state-only: `0.7240`
- environment-first language-blind: `0.6840`
- environment-first language-shuffle: `0.6840`

This is not evidence for or against the literature claim because trajectories came from a low-competence policy and online task success / true holdout transfer were not measured.

### Authorized next work

After R0.1 competence is established:

1. export successful or sufficiently competent public trajectories;
2. define typed observation-field losses instead of scalar MSE over mixed continuous/binary/token-ID fields;
3. reproduce Gaddy & Klein 2019 environment-first training or a faithful task-matched equivalent;
4. reproduce Language Dynamics Distillation or a faithful next-state objective;
5. match parameter and data budgets to end-to-end;
6. measure online task success、typed next-state prediction、action accuracy、held-out entity、held-out dynamics/mechanism、held-out language form;
7. run language-blind、language-shuffle、state-only、transition-shuffle controls on identical instances;
8. pass the artifact/evaluation contract.

Internal representation appearance、compression、latent clusteringは進歩へ数えない。

## P1 — Gate-I benchmark qualification

SILG/RTFM is **rejected as a direct Gate-I benchmark** because it does not define ground-truth latent intervention families, targets, mechanism pre/post operators or a causal abstraction. Adding them by hand would reintroduce a fixed ontology.

Search primary literature and official datasets for a benchmark with all of:

- raw language plus sequential or interactive trajectories
- explicit mechanism-change pre/post data
- ground-truth intervention family or theoretically justified causal abstraction
- held-out intervention target or mechanism
- permutation-aware evaluation
- intervention diversity sufficient to distinguish competing partitions

If no public benchmark qualifies, formally reject the empirical joint-identification program and retain only an impossibility/sufficient-condition theory program.

No R0.3 model experiment is authorized before Gate L is positive and a Gate-I benchmark qualifies.

## P1 — Prior-art and novelty matrix

Established areas that are not standalone contributions:

- unknown intervention target and unknown multi-node intervention recovery
- unknown soft-intervention inference
- finite-sample recovery from few environments
- nonparametric causal representation learning under general environments
- causal abstraction under subset interventions
- intervention-conditioned causal response representation
- perturbation-target prediction
- multi-environment interactive language grounding
- language-conditioned dynamics pretraining
- environment-first instruction-following pretraining

Latest boundary: 2025–2026 work extends identifiability/achievability to general mixing, unknown interventions, few environments, finite samples and intervention-inspired disentanglement. A broad claim that interventions create causal representations is not novel.

### Current research-question status

- Gate L on SILG: **continued as public language-necessity evaluation**
- Gate I on SILG: **rejected as undefined**
- joint empirical RQ: **not adopted**
- next-stage central claim: **not preregistered**

Reject the whole empirical direction if:

1. Full fails to exceed state/action/history and language shuffle after competent-policy reproduction;
2. gains disappear under environment-ID control、Rename or transition shuffle;
3. no Gate-I-qualified public benchmark exists;
4. an equal-or-weaker-assumption primary source solves the exact joint problem;
5. target labels、completed trajectories、post-treatment features or hand-written causal ontology are required.

## P2 — Japanese realism audit

Pinned source: official `riken-grp/J-CRe3` repository.

Tasks:

- pin commit、license、download command、checksum、split、annotation schema
- reproduce text-only、vision-only、combined reference baselines where supported
- separate direct reference、predicate-argument、bridging reference
- audit subject omission and demonstratives where annotations permit

J-CRe3 is an external Japanese grounding audit. It does not substitute for SILG R0.1 and must not be averaged into its primary score.

## P2 — Theory before invention

After valid R0 reproduction, preregister at most one claim:

- impossibility theorem for joint language–causal alignment under a specified symmetry; or
- sufficient-condition theorem for shared-permutation / supported-abstraction recovery under explicit trajectory and intervention diversity.

No new architecture is authorized before baseline reproduction、novelty comparison、primary metric and stopping rule are preregistered.

## Frozen work

- new opaque-token toy benchmarks
- renamed span/slot/graph/tensor/assembly/attractor mechanisms
- AF-014 derivatives before reproduction
- memory/replay/fast weights/sleep/forgetting optimization
- best-seed、domain-average-only、single-condition positives
- prospective evaluation using after-state or completed trajectory
- new stacked PR chains
- treating random-control、training-path or offline imitation diagnostics as intelligence progress
- implementing Gate I by manually adding an ontology to SILG

## R0 completion rule

R0 completes only when all are true:

- at least one learned external public capability baseline is reproduced
- random/language-blind/state-only/shuffle controls are measured on fixed public instances
- at least three canonical seed logs exist
- complete artifact/leakage contract passes
- CPU/RSS/model-size measurements are recorded
- R0.2 matched public online comparison is completed
- R0.3 is completed on a qualified benchmark or formally rejected as undefined/unavailable
- novelty matrix covers relevant 2026 primary literature
- the empirical RQ is adopted, further narrowed or rejected
- exactly one next-stage central claim is preregistered