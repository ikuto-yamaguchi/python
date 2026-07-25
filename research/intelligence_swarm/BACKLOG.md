# Intelligence Swarm Backlog

## P0 — Complete the faithful staged SILG recurrent reproduction

Completed evidence remains the official SILG `multi` recurrent at 32,768 requested frames for seeds `1,7,19`, with matched fixed-instance controls:

- parameters: `4,916,915`
- state-dict audit bytes: `19,694,385`
- maximum RSS: `505,600 KiB`
- total three-seed training time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct win rate: `0.0167`
- Random win rate: `0.0667`
- Language-blind, State-only and Language-shuffle: each `0.0167`

Classification remains:

`matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`

At RESET-E019, workflow run `30136732061` has passed source installation and random/schema probing and is in the official recurrent 131,072-frame training step. Do not incorporate unfinished values.

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

D015 is the active contract. It directly adapts concrete SILG exporter fields:

- `text_tokens -> utterance`;
- `action -> gold_action`;
- `state_after -> gold_state_after`;
- prospective-only default `model_input`;
- reward, done, outcome, gold action and after-state excluded from model input;
- shared train/test `episode_id`, `episode_seed`, or `observation_fingerprint` rejected;
- wholly absent required methods included in coverage failure reports.

Every measured run must also pass:

- train/test utterance overlap and entity/dynamics split checks;
- gold action, after-state, post-treatment and completed-trajectory leakage checks;
- canonical seeds `1,7,19`;
- prediction-side instance fingerprints;
- complete prediction/artifact coverage;
- score and artifact cells indexed by `method × seed × domain × split × condition`;
- paired mean/minimum-cell gaps, exact McNemar and cluster-bootstrap 95% CI;
- independently readable raw logs, models and immutable data;
- full 40-hex source/code pins and 64-hex artifact hashes;
- exact reported model bytes versus artifact size;
- finite RSS, wall time and CPU latency;
- explicit `answer_leakage:false` and `pretrained_language_model:false`.

Shuffle predictions additionally require donor ID/fingerprint, donor existence, no self-donor, same-cell assignment, fingerprint agreement, cell-wise bijection, fixed-point-free derangement and no donor reuse.

D015 has **18 passing regression tests**. Formal classification remains **`initial_reproduction_failure`** because real outcome-shuffle predictions, target-label-shuffle predictions or a formal inapplicability record, immutable serialized test checksum, complete artifact joins and competent public capability are missing.

## P1 — R0.2 Environment-first faithful transfer

Old public trajectories are comparison-ineligible. Environment-first `0.6840`, End-to-end `0.6907`, State-only `0.7240`, and zero language-blind/shuffle gap are negative diagnostics only.

Source-policy failures: seed 1 success `0/40`; seed 7 `0/40` with `97.42%` majority action; seed 19 `1/40`; all test sets `0/20`.

Every source-policy seed must first satisfy:

- majority action share `<=0.90`;
- successful train episodes `>=5`;
- at least two actions with `>=5%` support.

Primary method reference:

- Gaddy & Klein 2019;
- authors' repository `dgaddy/environment-learning`;
- commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`.

The faithful full method requires language-free `E(s,s')->m`, reused `D(s,m)->s'`, structured discrete messages, direct environment/language message matching, an LSTM language module, and a pretrained decoder frozen by default.

The current SILG adaptation is not accepted because it uses a continuous width-48 message, no direct message matching, a GRU, flat mixed-field MSE, no online task success, and no verified entity/dynamics/language-form holdouts.

`audit_r02_gaddy_klein_fidelity.py` must pass before any result is called R0.2 reproduction. It requires:

1. exact seeds `1,7,19` and disjoint train/test episodes;
2. typed state schema that covers the full state vector;
3. typed per-field transition losses;
4. real entity, dynamics and language-form holdouts;
5. successful, non-collapsed source trajectories;
6. official discrete-message and direct message-alignment contract;
7. identical Environment-first/End-to-end inference topology and parameter count;
8. separately reported language-labelled data, transition data and optimizer steps;
9. online task success, action accuracy and typed next-state metrics;
10. model bytes, RSS, wall time, CPU latency and full hashes;
11. no pretrained language model.

Current classification: **`official_method_transfer_audited_current_dataset_blocked`**.

Representation appearance, compression and clustering do not count as progress.

## Closed — Empirical Gate I / R0.3

Status: **formally rejected under current public-benchmark and no-researcher-ontology constraints**.

SILG/RTFM has no ground-truth latent intervention family, target, mechanism operator or causal abstraction. Audited J-CRe3, CausalTriplet, ACCESS, MIB and CausalPhys do not jointly provide all required observations and ground truth.

Do not add a hand-authored target/mechanism ontology or run hidden-intervention ablations on SILG. RQ-001-N5 is closed.

## Closed — RQ-001-T1 current formulation

Finite-index collapse rejects the claim that raw utterance relations exceed every unrestricted finite auxiliary-index representation. On finite support, `U=index(L)` can losslessly encode every observed utterance and deterministic relation derived from it.

C012 adds a stronger re-encoding obstruction: without population-grammar and mechanism restrictions, hidden language factors can be bijectively merged into one factor controlling a combined block, or reversibly split into pseudo-components, while preserving the observable distribution. The number and size of language-controlled target blocks are therefore not jointly identifiable.

## P2 — Only admissible RQ reformulation, not adopted

Allowed solely as a preregistration candidate:

> Under an explicit population grammar and a restricted non-lookup language-to-dynamics mechanism class, determine whether raw utterances jointly identify a nontrivial utterance factorization and a refinement of a known intervention-induced causal abstraction when neither language components nor target blocks are supplied.

Before adoption it requires:

1. formal population language generator;
2. restrictions ruling out utterance-ID lookup and arbitrary factor splitting/merging;
3. exact causal-model equivalence relation;
4. known residual causal abstraction;
5. unseen-form, component-tuple and target-block splits;
6. positive joint-identification theorem;
7. matched impossibility result when assumptions are removed;
8. explicit comparison with WM3C, auxiliary-variable ICA and multi-view CRL;
9. completed external public capability reproduction.

No implementation, synthetic benchmark or architecture is authorized before preregistration.

## P1 — Prior-art and novelty matrix

Maintain primary-source comparison through 2026 for unknown/uncoupled interventions, causal abstractions, finite-sample CRL, auxiliary/temporal/multi-view/hidden-regime ICA, grouping and weak supervision, mechanistic independence, mechanism sparsity, interactive grounding, environment-first, language-dynamics pretraining, causal world-model interfaces and WM3C.

Broad language-as-auxiliary, shuffle-negative, shared-view, unknown-target recovery, utterance-grouping, supplied-language-component block identification and unseen recombination claims are not novel.

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
