# Intelligence Swarm Backlog

## P0 — Resolve corrected 32,768-frame SILG evaluation

Current status: **corrected workflow run `30120620610` in progress; no capability result integrated**.

Only authorized actions:

1. obtain the completed artifact for seeds `1,7,19`;
2. verify checkpoint, model, source, data and raw-log SHA-256;
3. record actual frames, model bytes, training wall time, peak RSS and CPU inference latency;
4. verify Correct / Random / Language-blind / State-only / Language-shuffle share every initial-instance fingerprint;
5. recompute run and top-level aggregates from episode records;
6. compute episode-level win, return and length paired gaps;
7. run source-trajectory competence and anti-collapse eligibility audits.

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
- target-label shuffle only if a non-oracle operational proxy exists; otherwise record formal inapplicability instead of inventing a target ontology

Required outputs:

- per-instance/episode predictions
- mandatory immutable `instance_fingerprint`
- complete method × seed × domain × split coverage
- online win, return and episode length
- source/model/data/raw-log SHA-256 and exact code commit
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
- no duplicate method × seed run
- domain × seed × condition cells
- paired mean/minimum-cell gaps and positive-cell fraction
- Correct-only/control-only counts and exact McNemar test
- hierarchical cluster-bootstrap 95% CI
- run-level aggregate recomputation from episode records
- top-level aggregate recomputation from run values
- full 40-hex SILG/RTFM source pins
- full 64-hex checkpoint/model/data/raw-log SHA-256
- finite positive model bytes, peak RSS, training wall time and CPU inference latency
- explicit `answer_leakage: false` and `pretrained_language_model: false`

Current classification: **`initial_reproduction_failure`**. Target-label shuffle or a formal non-oracle inapplicability record, Outcome shuffle, immutable test-set checksum and raw-log artifact join remain missing. Aggregate-only summaries are invalid.

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
2. preserve typed observation-field boundaries and use typed transition losses;
3. reproduce Gaddy & Klein 2019 or an explicitly documented faithful task-matched variant;
4. reproduce Language Dynamics Distillation or a faithful next-state objective;
5. match parameter and data budgets to End-to-end;
6. measure online task success, action accuracy, typed next-state prediction and real entity/dynamics/language-form transfer;
7. run language-blind, language-shuffle, state-only and transition/outcome-shuffle on identical instances;
8. pass the full evaluation/artifact contract.

Internal representation appearance, compression and latent clustering do not count as progress.

## Closed — Empirical Gate I / R0.3

**Status: formally rejected under the current public-benchmark and no-researcher-ontology constraints.**

SILG/RTFM does not define latent intervention families, targets, mechanism pre/post operators or a causal abstraction. Audited J-CRe3, CausalTriplet, ACCESS, MIB and CausalPhys also fail to jointly provide:

- raw episode-aligned language and sequential/interactive trajectories
- independently defined mechanism-changing variation
- explicit mechanism pre/post data
- ground-truth intervention family or theoretically justified abstraction
- held-out target or mechanism split
- permutation-aware evaluation
- intervention diversity that distinguishes competing partitions

Do not create a hand-authored target/mechanism ontology to reopen this track. Do not run hidden-intervention ablations on SILG.

Rejected empirical claim **RQ-001-N5**:

> On a qualified public mechanism-change benchmark, episode-aligned language retains mechanism information after conditioning on the complete non-language trajectory, strictly refines a trajectory-only equivalence class, and improves held-out mechanism capability.

The closure is a benchmark/claim qualification decision, not a universal impossibility theorem.

## P2 — Theory-only candidate RQ-001-T1

Status: **candidate, not adopted; no implementation authorized**.

> Under explicit observation and intervention assumptions, characterize when raw language can strictly refine the causal equivalence class identifiable from trajectories alone, and prove impossibility when the mechanism is conditionally independent of language given complete non-language history or when no intervention family separates competing partitions.

Before adoption, all are required:

1. formal observation model;
2. precise equivalence relation;
3. difference from multimodal nonlinear ICA, environment-indexed CRL and basic conditional-independence restatements;
4. at least one nontrivial positive construction;
5. at least one nontrivial negative construction;
6. exactly one preregistered claim, primary theorem, counterexamples and stopping rule;
7. completed R0.1 public capability reproduction before any new architecture.

Necessary condition `I(M;L|X)>0` is not sufficient and does not itself constitute novelty.

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
- causal world models connected to language agents
- physical causal-reasoning benchmarks with expert graphs

Broad claims that interventions create causal representations, unknown targets can be recovered, language and dynamics can be jointly learned, or capable agents contain predictive world models are not novel.

## P2 — Japanese realism audit

Pinned candidate: official `riken-grp/J-CRe3`.

- pin commit, license, download command, checksums, split and annotation schema;
- reproduce supported text-only, vision-only and combined baselines;
- separate direct reference, predicate-argument and bridging reference;
- audit subject omission and demonstratives where annotation permits.

J-CRe3 is an external Japanese grounding audit and must not be averaged into SILG scores or treated as Gate I.

## P2 — Preregister exactly one successor claim

Only after R0 completion, preregister one of:

- RQ-001-T1 as a nontrivial impossibility/sufficient-condition theorem; or
- another claim that survives the completed novelty matrix and is supported by a qualified public benchmark.

The preregistration must specify prior-art difference, assumptions, primary metric or theorem, controls/counterexamples, resource ceiling and stopping rule before any new architecture.

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
- hidden-intervention ablations on SILG
- tuning R0.2 on failed-policy demonstrations
- starting RQ-001-T1 before formalization and preregistration

## R0 completion rule

All must hold:

1. at least one learned external public capability baseline reproduced;
2. random/language-blind/state-only/shuffle controls on immutable public instances;
3. three canonical seed logs and complete artifact/leakage contract;
4. CPU/RSS/model-size measurements;
5. R0.2 matched public online comparison with typed metrics and real holdouts;
6. empirical R0.3 formally rejected and integrated;
7. novelty matrix through relevant 2026 primary literature;
8. empirical RQ rejected and theory candidate adopted/rejected after formal comparison;
9. exactly one next-stage central claim preregistered.