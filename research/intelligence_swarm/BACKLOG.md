# Intelligence Swarm Backlog

## P0 — Resolve the 32,768-frame SILG run

Current status: **submitted / result not yet integrated**.

Only authorized actions:

1. obtain the completed GitHub Actions artifact for seeds `1,7,19`;
2. verify checkpoint, model, data and raw-log SHA-256;
3. record frames, model bytes, training wall time, peak RSS and CPU inference latency;
4. verify Correct / Random / Language-blind / State-only / Language-shuffle share all initial-instance fingerprints;
5. evaluate episode-level paired gaps;
6. run the trajectory-eligibility audit.

Decision:

- if policy competence and trajectory eligibility improve, proceed to immutable matched evaluation;
- if not, increase or repair only the official recurrent training budget/reproduction condition;
- do not tune Environment-first, invent a new architecture or claim language irrelevance from a collapsed policy.

## P0 — Immutable R0.1 public capability evaluation

R0.1 completes only when one serialized `rtfm_test_s1-v0` evaluation set is frozen for seeds `1,7,19` and every method consumes that exact snapshot.

Required methods:

- official recurrent Correct
- random valid action
- language-blind
- state-only
- environment-ID-only
- within-environment language shuffle
- outcome or transition shuffle
- target-label shuffle only if a non-oracle operational proxy exists

Required outputs:

- per-instance prediction JSONL
- mandatory `instance_fingerprint`
- complete method × seed × domain × split coverage
- online win / return / episode length
- model/data/log checksums and exact source commit
- model bytes, peak RSS, training wall time and CPU latency
- cell-level and instance-paired statistics
- comparison with a preregistered public reference tolerance

Interpret no score until `evaluation_contract.py` passes.

## P0 — Evaluation and artifact contract

Every measured experiment must pass:

- train/test normalized utterance overlap check
- entity and dynamics split overlap check
- gold action, next state, reward, done, post-treatment and completed-trajectory leakage checks
- canonical seeds `1,7,19`
- prediction-supplied immutable instance fingerprints
- complete prediction and artifact coverage
- domain × seed × condition cells
- paired mean/minimum-cell gaps and positive-cell fraction
- exact McNemar test and hierarchical cluster-bootstrap 95% CI
- source/model/data/log SHA-256 and code commit
- model bytes, peak RSS, training wall time and CPU inference latency

Current classification: **`initial_reproduction_failure`**. Contract tests: **7 passed**. Aggregate summaries alone are invalid.

## P1 — R0.2 Environment-first reproduction

Current status: **old public trajectories rejected as comparison-ineligible**.

Observed negative diagnostic:

- Environment-first action accuracy: `0.6840`
- matched End-to-end: `0.6907`
- State-only: `0.7240`
- Language-blind gap: `0.0000`
- Language-shuffle gap: `0.0000`

Eligibility failure:

- seed 1 successful train episodes: `0/40`
- seed 7: `0/40`; majority action `97.42%`
- seed 19: `1/40`
- all test sets: `0/20`

Before any representation comparison, source trajectories must satisfy per seed:

- majority action share `<= 0.90`
- successful train episodes `>= 5`
- at least two actions with `>=5%` support

After R0.1 competence and eligibility:

1. export competent public trajectories;
2. use typed observation-field next-state losses;
3. reproduce Gaddy & Klein 2019 or a faithful task-matched Environment-first baseline;
4. reproduce Language Dynamics Distillation or a faithful next-state objective;
5. match parameter and data budgets to End-to-end;
6. measure online task success, action accuracy, typed next-state prediction and real held-out entity/dynamics/language-form transfer;
7. run language-blind, language-shuffle, state-only and transition/outcome-shuffle on identical instances;
8. pass the evaluation/artifact contract.

Internal representation appearance, compression and latent clustering do not count as progress.

## P1 — Gate-I benchmark qualification

SILG/RTFM is rejected as a direct intervention-partition benchmark because it does not define latent intervention families, targets, mechanism pre/post operators or a causal abstraction.

A qualified public benchmark must contain:

- raw language and sequential/interactive trajectories
- independently defined mechanism-changing variation
- explicit mechanism pre/post data
- ground-truth intervention family or theoretically justified causal abstraction
- held-out intervention target or mechanism
- permutation-aware evaluation
- intervention diversity that distinguishes competing partitions

Candidate RQ-001-N4 remains **narrowed, not adopted**:

> Does episode-aligned raw language strictly refine a trajectory-only equivalence class into a finer intervention-supported causal abstraction and improve held-out mechanism prediction?

Reject the empirical joint-identification direction if no public benchmark qualifies, if an equal/weaker-assumption primary source solves it, or if hand-written target slots/ontology are required.

No R0.3 model experiment is authorized before Gate L is positive and Gate-I qualification succeeds.

## P1 — Prior-art and novelty matrix

Maintain primary-source comparison through 2026 for:

- unknown / multi-node / soft intervention recovery
- finite-sample few-environment identifiability
- nonparametric general-environment CRL
- subset-intervention causal abstraction
- raw-trajectory system parameter identifiability
- temporal partition and causal-graph joint learning
- multimodal partial-sharing identifiability
- perturbation-target and causal-response representations
- interactive language grounding
- language-dynamics and environment-first pretraining

Broad claims that interventions create causal representations, or that language and dynamics can be jointly learned, are not novel.

## P2 — Japanese realism audit

Pinned candidate: official `riken-grp/J-CRe3`.

Tasks:

- pin commit, license, download command, checksum, split and annotation schema;
- reproduce supported text-only, vision-only and combined baselines;
- separate direct reference, predicate-argument and bridging reference;
- audit subject omission and demonstratives where annotations permit.

J-CRe3 is an external Japanese grounding audit and must not be averaged into SILG scores.

## P2 — Preregister at most one next-stage claim

Only after R0 completion, preregister one of:

- an impossibility theorem under an explicit joint language–causal symmetry; or
- a sufficient-condition theorem for shared-permutation / supported-abstraction recovery.

The preregistration must specify prior-art difference, assumptions, primary metric, controls, resource ceiling and stopping rule before any new architecture.

## Frozen work

- new opaque-token toy benchmarks
- renamed span/slot/graph/tensor/assembly/attractor mechanisms
- AF-014 derivatives before reproduction
- memory/replay/fast weights/sleep/forgetting optimization
- best-seed, average-only or single-condition positives
- after-state/completed-trajectory prospective leakage
- new stacked PR chains
- treating installation, random control, training-path smoke or offline imitation as intelligence progress
- manually adding a Gate-I ontology to SILG
- tuning R0.2 representation models on failed-policy demonstrations

## R0 completion rule

All must hold:

1. at least one learned external public capability baseline reproduced;
2. random/language-blind/state-only/shuffle controls on immutable public instances;
3. three canonical seed logs and complete artifact/leakage contract;
4. CPU/RSS/model-size measurements;
5. R0.2 matched public online comparison with typed metrics and real holdouts;
6. R0.3 completed on a qualified benchmark or formally rejected;
7. novelty matrix through relevant 2026 primary literature;
8. empirical RQ adopted, further narrowed or rejected;
9. exactly one next-stage central claim preregistered.
