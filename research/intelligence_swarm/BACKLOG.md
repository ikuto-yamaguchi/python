# Intelligence Swarm Backlog

## P0 — Reproduce a competent public SILG capability baseline

Current status: **corrected 32,768-frame workflow completed; training and matched-evaluation paths reproduced; public capability baseline not reproduced**.

Confirmed staged result:

- official SILG `multi` recurrent, no pretrained language model;
- seeds `1,7,19`;
- 32,800 checkpoint frames per seed;
- `4,916,915` parameters;
- `19,694,385` state-dict audit bytes;
- maximum RSS `505,600 KiB`;
- total training wall time `1,033.885 s`;
- CPU forward audit `6.911 ms/step`;
- Correct win rate `0.0167` versus Random `0.0667`;
- Language-blind, State-only and Language-shuffle win rate `0.0167` each;
- all matched initial-instance fingerprint streams passed.

Classification:

`matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`

Only authorized actions:

1. compare the official paper/code training schedule, optimizer, actor count, unroll, batching, evaluation mode and checkpoint handling against the current staged configuration;
2. increase only the faithful official recurrent training budget or correct an official reproduction-condition mismatch;
3. retain staged checkpoints and evaluate the same immutable matched protocol at preregistered budgets;
4. record frames, model bytes, RSS, training wall time, CPU latency, full source/model/data/log hashes and all failure logs;
5. stop and classify resource insufficiency if competence does not emerge within the fixed ceiling.

Forbidden:

- tuning Environment-first against failed-policy trajectories;
- adding a new architecture or mechanism family;
- inferring that language is irrelevant from an incompetent policy;
- selecting a favorable seed or changing the test instances.

## P0 — Immutable R0.1 public capability evaluation

R0.1 completes only when a competent learned public baseline and every control consume one frozen serialized `rtfm_test_s1-v0` snapshot for seeds `1,7,19`.

Required controls:

- official recurrent Correct;
- random valid action;
- language-blind;
- state-only;
- environment-ID-only;
- within-environment language shuffle;
- transition or outcome shuffle;
- target-label shuffle only if a non-oracle operational proxy exists; otherwise a formal inapplicability record must explain why no benchmark target label exists.

Required outputs:

- per-instance/episode predictions and immutable `instance_fingerprint`;
- complete method × seed × domain × split coverage;
- online win, return and episode length;
- source/model/data/raw-log SHA-256 and exact code commit;
- model bytes, peak RSS, training wall time and CPU latency;
- domain × seed × condition cells and episode-paired statistics;
- preregistered public-reference tolerance.

Interpret no capability score until the complete evaluation contract passes.

## P0 — Evaluation, statistics, leakage and provenance

Every measured run must pass:

- normalized train/test utterance overlap check;
- entity and dynamics split-overlap check;
- gold action, next state, reward, done, post-treatment and completed-trajectory leakage checks;
- canonical seeds `1,7,19`;
- prediction-supplied instance fingerprints;
- complete prediction and artifact coverage;
- no duplicate method × seed run;
- domain × seed × condition cells;
- paired mean/minimum-cell gaps and positive-cell fraction;
- Correct-only/control-only counts and exact McNemar test;
- hierarchical cluster-bootstrap 95% CI;
- run and top-level aggregate recomputation;
- independently readable raw-log, model and immutable-data files;
- full 40-hex source/code pins;
- full 64-hex checkpoint/model/data/raw-log SHA-256;
- exact reported model-bytes versus artifact-size agreement;
- finite model bytes, peak RSS, training wall time and CPU inference latency;
- explicit `answer_leakage: false` and `pretrained_language_model: false`.

Ten regression tests pass.

Current classification: **`initial_reproduction_failure`**. Missing: Outcome/transition shuffle, target-label shuffle or formal non-oracle inapplicability, immutable serialized test-set checksum, and a complete per-cell manifest joining readable logs/models/data with hashes.

## P1 — R0.2 Environment-first reproduction

Current status: **old public trajectories rejected as comparison-ineligible; current implementation is not a faithful Gaddy & Klein default reproduction**.

Observed negative diagnostic:

- Environment-first action accuracy `0.6840`;
- matched End-to-end `0.6907`;
- State-only `0.7240`;
- Language-blind gap `0.0000`;
- Language-shuffle gap `0.0000`.

Eligibility failure:

- seed 1 successful train episodes `0/40`;
- seed 7 `0/40`, majority action `97.42%`;
- seed 19 `1/40`;
- all test sets `0/20`.

Every source-policy seed must first satisfy:

- majority action share `<= 0.90`;
- successful train episodes `>= 5`;
- at least two actions with `>=5%` support.

After R0.1 competence and trajectory qualification:

1. export competent public trajectories;
2. preserve typed observation-field boundaries and use typed transition losses;
3. reproduce the structured discrete-message and message-alignment elements of the official Gaddy & Klein implementation, or document every task-required deviation;
4. match parameter and data budgets to End-to-end;
5. measure online task success, action accuracy, typed next-state prediction and real entity/dynamics/language-form transfer;
6. run language-blind, language-shuffle, state-only and transition/outcome-shuffle on identical instances;
7. pass the full evaluation/artifact contract.

Internal representation appearance, compression and latent clustering do not count as progress.

## Closed — Empirical Gate I / R0.3

**Status: formally rejected under the current public-benchmark and no-researcher-ontology constraints.**

SILG/RTFM does not define latent intervention families, targets, mechanism pre/post operators or causal abstractions. Audited J-CRe3, CausalTriplet, ACCESS, MIB and CausalPhys also fail to jointly provide raw episode-aligned language, interactive trajectories, independently defined mechanism changes, mechanism ground truth, held-out targets and permutation-aware evaluation.

Do not add a hand-authored target/mechanism ontology to SILG. Do not run hidden-intervention ablations on SILG.

Rejected empirical claim: **RQ-001-N5**.

## P2 — Theory-only candidate RQ-001-T1

Status: **narrowed again, not adopted; no implementation authorized**.

Surviving candidate:

> Characterize whether compositional relations among raw utterances can remove a causal-model equivalence that remains after conditioning on complete trajectories and after quotienting out every use of language as a mere auxiliary/environment index; prove impossibility when language reduces to such an index or available interventions do not separate competing partitions.

Before adoption, all are required:

1. formal observation model and trajectory-only equivalence relation;
2. exact quotient by auxiliary/environment-index information;
3. a distinction from auxiliary-variable nonlinear ICA, temporal nonlinear ICA, multimodal partial-sharing CRL and environment-indexed invariance;
4. at least one nontrivial positive construction;
5. at least one nontrivial negative construction;
6. exactly one preregistered theorem, counterexamples and stopping rule;
7. completed R0.1 public capability reproduction before any new architecture.

`I(M;L|X)>0` is necessary at most; it is not sufficient and is not itself novelty.

## P1 — Prior-art and novelty matrix

Maintain primary-source comparison through 2026 for:

- unknown, multi-node and soft intervention recovery;
- finite-sample few-environment identifiability;
- nonparametric general-environment and score-based CRL;
- subset-intervention causal abstraction;
- raw-trajectory system-parameter identifiability;
- temporal partition and causal-graph joint learning;
- auxiliary-variable and temporal nonlinear ICA;
- multimodal partial-sharing identifiability;
- perturbation-target and causal-response representations;
- interactive language grounding;
- language-dynamics and environment-first pretraining;
- causal world models connected to language agents;
- physical causal-reasoning benchmarks with expert graphs.

Broad claims that language is an auxiliary identifiability signal, shuffled language supplies contrastive negatives, interventions create causal representations, unknown targets can be recovered, or capable agents contain world models are not novel.

## P2 — Japanese realism audit

Pinned candidate: official `riken-grp/J-CRe3`.

- pin commit, license, download command, checksums, split and annotation schema;
- reproduce supported text-only, vision-only and combined baselines;
- separate direct reference, predicate-argument and bridging reference;
- audit subject omission and demonstratives where annotation permits.

J-CRe3 is an external Japanese grounding audit and must not be averaged into SILG scores or treated as Gate I.

## P2 — Preregister exactly one successor claim

Only after R0 completion, preregister RQ-001-T1 as a nontrivial theorem or another claim that survives the completed novelty matrix and a qualified public benchmark.

The preregistration must specify prior-art difference, assumptions, primary metric or theorem, controls/counterexamples, resource ceiling and stopping rule before any new architecture.

## Frozen work

- new opaque-token toy benchmarks;
- renamed span/slot/graph/tensor/assembly/attractor mechanisms;
- AF-014 derivatives before reproduction;
- memory/replay/fast weights/sleep/forgetting optimization;
- best-seed, average-only or single-condition positives;
- after-state/completed-trajectory prospective leakage;
- new stacked PR chains;
- treating installation, random control, training-path smoke or offline imitation as intelligence progress;
- manually adding a Gate-I ontology to SILG;
- hidden-intervention ablations on SILG;
- tuning R0.2 on failed-policy demonstrations;
- starting RQ-001-T1 before formalization and preregistration.

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
