# Intelligence Swarm Backlog

## P0 — Complete the faithful staged SILG recurrent reproduction

Completed evidence remains the official SILG `multi` recurrent at 32,768 requested frames for seeds `1,7,19`, with matched fixed-instance controls. It has `4,916,915` parameters, `19,694,385` state-dict audit bytes, maximum RSS `505,600 KiB`, total three-seed training time `1,033.885 s`, and CPU forward audit `6.911 ms/step`.

Correct achieved `0.0167` win rate versus Random `0.0667`; Language-blind, State-only and Language-shuffle were each `0.0167`. Classification remains:

`matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`

The first 131,072-frame attempt was stopped by a fixed harness timeout, not an official learner exception. Timeout handling was corrected without changing the model, loss, optimizer, source pins, seeds, split or schema.

At RESET-E018, head workflow run `30133481693` is in the official recurrent training step. Do not incorporate unfinished values.

Authorized actions:

1. complete the active 131,072-frame run;
2. evaluate Correct, Random, Language-blind, State-only and Language-shuffle on identical immutable instances;
3. record source/model/data/raw-log hashes, model bytes, RSS, training wall time, CPU latency, seeds and splits;
4. test policy competence and trajectory anti-collapse eligibility;
5. if competence is absent, correct only a verified official reproduction mismatch or classify resource/budget insufficiency at the preregistered ceiling.

Forbidden:

- tuning R0.2 on failed-policy trajectories;
- adding architecture or mechanism families;
- selecting favorable seeds or test instances;
- inferring language irrelevance from an incompetent policy;
- treating unfinished or duplicate workflow runs as evidence.

## P0 — Immutable R0.1 evaluation

R0.1 completes only when a competent learned public baseline and controls consume one frozen serialized `rtfm_test_s1-v0` snapshot for seeds `1,7,19`.

Required controls:

- official recurrent Correct;
- random valid action;
- language-blind;
- state-only;
- environment-ID-only;
- within-environment language shuffle;
- transition/outcome shuffle;
- target-label shuffle only if a non-oracle benchmark label exists, otherwise a formal inapplicability record.

Required outputs:

- per-instance predictions and immutable fingerprints;
- complete `method × seed × domain × split × condition` coverage;
- win, return and episode length;
- source/model/data/raw-log SHA-256 and code commit;
- model bytes, peak RSS, training wall time and CPU latency;
- paired cell and episode statistics;
- preregistered public-reference tolerance.

## P0 — Evaluation, statistics, leakage and provenance

Every measured run must pass:

- train/test utterance overlap and entity/dynamics split checks;
- gold action, after-state, reward, done, post-treatment and completed-trajectory leakage checks;
- canonical seeds `1,7,19`;
- prediction-side instance fingerprints;
- complete prediction/artifact coverage;
- no duplicate method-seed run;
- score and artifact cells indexed by `method × seed × domain × split × condition`;
- paired mean/minimum-cell gaps, positive-cell fraction, exact McNemar and cluster-bootstrap 95% CI;
- run and top-level aggregate recomputation;
- independently readable raw logs, models and immutable data;
- full 40-hex source/code pins and 64-hex artifact hashes;
- exact reported model bytes versus artifact size;
- finite resource measurements;
- explicit `answer_leakage:false` and `pretrained_language_model:false`.

Shuffle predictions additionally require donor ID/fingerprint, donor existence, no self-donor, same-cell assignment, fingerprint agreement, cell-wise bijection, fixed-point-free derangement and no donor reuse.

D014 has 15 passing regression tests. Formal classification remains **`initial_reproduction_failure`** because real shuffle predictions or formal target-label inapplicability, immutable serialized test checksum, complete artifact joins and competent public capability are missing.

## P1 — R0.2 Environment-first reproduction

Old public trajectories are comparison-ineligible. Environment-first `0.6840`, End-to-end `0.6907`, State-only `0.7240`, and zero language-blind/shuffle gap are negative diagnostics only.

Source-policy failures: seed 1 success `0/40`; seed 7 `0/40` with `97.42%` majority action; seed 19 `1/40`; all test sets `0/20`.

Every source-policy seed must first satisfy:

- majority action share `<=0.90`;
- successful train episodes `>=5`;
- at least two actions with `>=5%` support.

After R0.1 qualification:

1. export competent trajectories;
2. preserve typed observation boundaries and typed transition losses;
3. reproduce the structured discrete-message and direct message-alignment elements of Gaddy & Klein or document task-required deviations;
4. match parameters and data to End-to-end;
5. measure online task success, action accuracy, typed next-state prediction and real entity/dynamics/language-form transfer;
6. run all controls on identical instances;
7. pass the full artifact/leakage contract.

Representation appearance, compression and clustering do not count as progress.

## Closed — Empirical Gate I / R0.3

Status: **formally rejected under current public-benchmark and no-researcher-ontology constraints**.

SILG/RTFM has no ground-truth latent intervention family, target, mechanism operator or causal abstraction. Audited J-CRe3, CausalTriplet, ACCESS, MIB and CausalPhys do not jointly provide all required observations and ground truth.

Do not add a hand-authored target/mechanism ontology or run hidden-intervention ablations on SILG. RQ-001-N5 is closed.

## Closed — RQ-001-T1 current formulation

C011 rejects the claim that raw utterance relations exceed every finite auxiliary-index representation. On finite support, `U=index(L)` can losslessly encode every observed utterance and every deterministic relation derived from it. A finite benchmark cannot demonstrate language-specific identifiability against an unrestricted finite auxiliary class.

## P2 — Only admissible RQ reformulation, not adopted

Allowed solely as a preregistration candidate:

> Under an explicit population grammar and a restricted auxiliary class that cannot copy utterance identity, determine whether compositional relations among unseen utterance forms refine a known intervention-induced causal abstraction beyond complete non-language trajectories.

Before adoption it requires:

1. formal population language generator;
2. explicit admissible auxiliary class;
3. exact causal-model equivalence relation;
4. known residual causal abstraction;
5. unseen-form positive construction and matched negative construction;
6. proof sketch and falsification condition;
7. lookup-preventing split;
8. prior-art comparison through relevant 2026 primary work;
9. completed external public capability reproduction.

No implementation, synthetic benchmark or architecture is authorized before preregistration.

## P1 — Prior-art and novelty matrix

Maintain primary-source comparison through 2026 for unknown/uncoupled interventions, causal abstractions, finite-sample CRL, auxiliary/temporal/multi-view/hidden-regime ICA, grouping and weak supervision, mechanistic independence, mechanism sparsity, interactive grounding, environment-first and language-dynamics pretraining, and causal world-model interfaces.

Broad language-as-auxiliary, shuffle-negative, shared-view, unknown-target-recovery and utterance-grouping claims are not novel.

## P2 — Japanese realism audit

Pinned candidate: official `riken-grp/J-CRe3`. Pin commit, license, downloads, checksums, split and schema; reproduce supported text/vision/combined baselines; audit direct reference, predicate-argument, bridging, omission and demonstratives where annotations permit. Do not average J-CRe3 into SILG or treat it as Gate I.

## Stage transition

Propose the next stage only after:

1. one learned external public capability baseline;
2. immutable-instance controls;
3. canonical three-seed artifact/leakage contract;
4. qualified R0.2 online comparison with typed metrics and real holdouts;
5. formal R0.3 rejection integrated in governance;
6. novelty matrix through 2026;
7. exactly one preregistered successor claim/theorem with counterexamples and stopping rule.

## Frozen work

- new toy benchmarks or renamed toy mechanisms;
- memory/replay/fast weights/sleep/forgetting;
- best-seed or average-only positives;
- prospective leakage;
- new stacked PR chains;
- installation/smoke/offline imitation as intelligence progress;
- manual Gate-I ontology;
- R0.2 tuning on failed demonstrations;
- RQ implementation before formalization and preregistration.
