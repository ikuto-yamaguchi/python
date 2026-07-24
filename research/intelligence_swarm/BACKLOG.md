# Intelligence Swarm Backlog

## P0 — Resolve corrected 32,768-frame SILG evaluation

Current status: **corrected workflow in progress; no capability result integrated**.

Only authorized actions:

1. obtain the completed artifact for seeds `1,7,19`;
2. verify checkpoint, model, source, data and raw-log SHA-256;
3. record actual frames, model bytes, training wall time, peak RSS and CPU inference latency;
4. verify Correct / Random / Language-blind / State-only / Language-shuffle share every initial-instance fingerprint;
5. compute episode-level win, return and length paired gaps;
6. run source-trajectory competence and anti-collapse eligibility audits.

Decision:

- if policy competence and trajectory eligibility pass, freeze one immutable public test set and proceed to strict matched evaluation;
- if they fail, change only the official recurrent training budget or reproduction condition;
- do not tune Environment-first, add a new architecture or infer that language is irrelevant from a failed policy.

## P0 — Immutable R0.1 public capability evaluation

R0.1 completes only when one serialized `rtfm_test_s1-v0` set is frozen for seeds `1,7,19` and every method consumes that exact snapshot.

Required controls:

- official recurrent Correct
- random valid action
- language-blind
- state-only
- environment-ID-only
- within-environment language shuffle
- transition or outcome shuffle
- target-label shuffle only if a non-oracle operational proxy exists

Required outputs:

- per-instance/episode predictions
- mandatory immutable `instance_fingerprint`
- complete method × seed × domain × split coverage
- online win, return and episode length
- source/model/data/log SHA-256 and exact code commit
- model bytes, peak RSS, training wall time and CPU latency
- cell-level and episode-paired statistics
- preregistered reference tolerance

Interpret no capability score until the evaluation contract passes.

## P0 — Evaluation, statistics, leakage and provenance

Every measured run must pass:

- normalized train/test utterance overlap check
- entity and dynamics split-overlap check
- gold action, next state, reward, done, post-treatment and completed-trajectory leakage checks
- canonical seeds `1,7,19`
- prediction-supplied instance fingerprints
- complete prediction and artifact coverage
- domain × seed × condition cells
- paired mean/minimum-cell gaps and positive-cell fraction
- Correct-only/control-only counts and exact McNemar test
- hierarchical cluster-bootstrap 95% CI
- source/model/data/log SHA-256 and code commit
- model bytes, peak RSS, training wall time and CPU inference latency

Current classification: **`initial_reproduction_failure`**. Aggregate-only summaries are invalid.

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

Before representation comparison, every source-policy seed must satisfy:

- majority action share `<= 0.90`
- successful train episodes `>= 5`
- at least two actions with `>=5%` support

After R0.1 competence and trajectory qualification:

1. export competent public trajectories;
2. use typed observation-field transition losses;
3. reproduce Gaddy & Klein 2019 or an explicitly documented faithful task-matched variant;
4. reproduce Language Dynamics Distillation or a faithful next-state objective;
5. match parameter and data budgets to End-to-end;
6. measure online task success, action accuracy, typed next-state prediction and real entity/dynamics/language-form transfer;
7. run language-blind, language-shuffle, state-only and transition/outcome-shuffle on identical instances;
8. pass the full evaluation/artifact contract.

Internal representation appearance, compression and latent clustering do not count as progress.

## P1 — Gate-I benchmark qualification

SILG/RTFM is rejected as a direct intervention-partition benchmark because it does not define latent intervention families, targets, mechanism pre/post operators or a causal abstraction.

A qualified public benchmark must contain:

- raw episode-aligned language and sequential/interactive trajectories
- independently defined mechanism-changing variation
- explicit mechanism pre/post data
- ground-truth intervention family or theoretically justified abstraction
- held-out target or mechanism split
- permutation-aware evaluation
- intervention diversity that distinguishes competing partitions

Audited candidates SILG/RTFM, J-CRe3, CausalTriplet, ACCESS and MIB do not meet the joint requirements.

Candidate **RQ-001-N5** remains narrowed and not adopted:

> On a qualified public mechanism-change benchmark, does episode-aligned language retain mechanism information after conditioning on the complete non-language trajectory, strictly refine a trajectory-only equivalence class, and improve held-out mechanism capability?

Necessary condition: `I(M;L|X)>0`, with `X` including state, action, history, reward, time, policy phase and environment identity.

Close the empirical Gate-I direction if no benchmark qualifies, if an equal/weaker-assumption primary source already solves it, or if researcher-authored target slots are required. No R0.3 model experiment is authorized before Gate L is positive and benchmark qualification succeeds.

## P1 — Prior-art and novelty matrix

Maintain primary-source comparison through 2026 for:

- unknown, multi-node and soft intervention recovery
- finite-sample few-environment identifiability
- nonparametric general-environment CRL
- score-based CRL under general transformations
- subset-intervention causal abstraction
- raw-trajectory system-parameter identifiability
- temporal partition and causal-graph joint learning
- multimodal partial-sharing identifiability
- perturbation-target and causal-response representations
- interactive language grounding
- language-dynamics and environment-first pretraining

Broad claims that interventions create causal representations, unknown targets can be recovered, or language and dynamics can be jointly learned are not novel.

## P2 — Japanese realism audit

Pinned candidate: official `riken-grp/J-CRe3`.

- pin commit, license, download command, checksums, split and annotation schema;
- reproduce supported text-only, vision-only and combined baselines;
- separate direct reference, predicate-argument and bridging reference;
- audit subject omission and demonstratives where annotation permits.

J-CRe3 is an external Japanese grounding audit and must not be averaged into SILG scores or treated as Gate I.

## P2 — Preregister exactly one successor claim

Only after R0 completion, preregister one of:

- an impossibility theorem under explicit joint language–causal symmetry; or
- a sufficient-condition theorem for shared-permutation or supported-abstraction recovery.

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
- tuning R0.2 on failed-policy demonstrations

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
