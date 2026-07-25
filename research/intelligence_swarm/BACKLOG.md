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

At RESET-E020, workflow run `30138560445` has completed checkout, Python setup, host recording, pinned-source installation and random/schema probing and remains in the official recurrent 131,072-frame training step. Do not incorporate unfinished values.

Authorized actions:

1. complete the active 131,072-frame run;
2. evaluate Correct, Random, Language-blind, State-only and Language-shuffle on identical immutable instances;
3. record source/model/data/raw-log/prediction hashes, model bytes, RSS, training wall time, CPU latency, seeds and splits;
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
- source/model/data/raw-log/prediction SHA-256 and code commit;
- model bytes, peak RSS, training wall time and CPU latency;
- paired cell and episode statistics;
- preregistered public-reference tolerance.

## P0 — Evaluation, statistics, leakage and provenance

D015 is the latest fully executed contract layer, with **18 passing regression tests**. It directly adapts concrete SILG exporter fields, constructs prospective-only model input, rejects train/test episode/seed/observation identity overlap, audits utterance/entity/dynamics splits, gold/post-treatment/completed-trajectory leakage, canonical seeds, immutable fingerprints, full prediction/artifact coverage, paired statistics, readable files, exact resource values and full hashes.

D016 adds the immutable prediction-to-dataset artifact join. Every measured run must now also provide:

- `prediction_path` and full `prediction_sha256`;
- readable prediction JSONL;
- manifest/prediction method identity agreement;
- unique prediction instance IDs;
- exact prediction/dataset instance-set equality;
- per-row instance-fingerprint agreement;
- one immutable dataset hash shared by all methods in each cell;
- stable model SHA and code commit for a method/seed across split and condition cells.

D016 tests are committed but have not yet been run by GitHub Actions, so do not claim a larger passing-test count. Formal classification remains **`initial_reproduction_failure`** because real outcome-shuffle predictions, target-label-shuffle predictions or a formal inapplicability record, immutable serialized test data, complete six-method prediction/artifact joins and competent public capability are missing.

## P1 — R0.2 Environment-first faithful transfer

Old public trajectories are comparison-ineligible. Environment-first `0.6840`, End-to-end `0.6907`, State-only `0.7240`, and zero language-blind/shuffle gap are negative diagnostics only.

Source-policy failures: seed 1 success `0/40`; seed 7 `0/40` with `97.42%` majority action; seed 19 `1/40`; all test sets `0/20`.

Primary method reference:

- Gaddy & Klein 2019;
- authors' repository `dgaddy/environment-learning`;
- commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`.

Cycle 009 adds `gaddy_klein_typed_baseline.py` with:

1. language-free transition pretraining;
2. 20 categorical message variables × 30 symbols;
3. straight-through Gumbel-Softmax;
4. shared typed next-state/action decoder;
5. LSTM language encoder;
6. direct environment/language message matching with weight `0.01`;
7. decoder frozen during language training by default;
8. categorical CE, binary BCE and continuous MSE losses;
9. exact seeds `1,7,19` and episode-disjointness checks;
10. dataset hash, parameter bytes, training time and peak RSS reporting.

The entry point must continue to reject legacy flattened rows. Before execution it requires typed SILG export containing `state_before_fields`, `state_after_fields`, `state_schema` and categorical cardinalities.

Before any result is called R0.2 reproduction, all of the following must exist:

- competent, non-collapsed source trajectories for all three seeds;
- typed state schema covering the complete state;
- parameter/topology-matched End-to-end and State-only controls;
- equal train examples, optimizer steps and splits;
- real entity, dynamics and language-form holdouts;
- online task success, action accuracy and typed next-state metrics;
- model bytes, RSS, wall time, CPU latency, dependency freeze and full hashes;
- `audit_r02_gaddy_klein_fidelity.py` pass;
- no pretrained language model.

Current classification:

`typed_discrete_message_method_path_implemented_dataset_and_online_evaluation_blocked`

Representation appearance, compression and clustering do not count as progress.

## Closed — Empirical Gate I / R0.3

Status: **formally rejected under current public-benchmark and no-researcher-ontology constraints**.

SILG/RTFM has no ground-truth latent intervention family, target, mechanism operator or causal abstraction. Do not add a hand-authored target/mechanism ontology or run hidden-intervention ablations on SILG. RQ-001-N5 is closed.

## Closed — Broad RQ-001 formulation

The following are rejected:

- raw utterance relations exceed every unrestricted finite auxiliary representation;
- raw language alone jointly identifies language factors and latent target blocks without grammar/mechanism restrictions;
- unknown intervention-target recovery is a language-specific contribution.

Finite-index collapse permits `U=index(L)` on finite support. Re-encoding symmetry permits hidden language factors to be merged or split while preserving observations. C013 further shows that unknown multi-node targets, latent graph, representation and decoder can already be recovered without language in a strongly separating linear regime using `O(log d)` environments and finite-sample guarantees.

## P2 — Only admissible RQ reformulation, not adopted

Allowed solely as a preregistration candidate:

> Under an explicit population grammar, a restricted non-lookup language-to-dynamics mechanism class and a known non-strongly-separating intervention family, determine whether raw utterances provide missing separating relations that strictly refine the family's residual causal abstraction on unseen utterance forms and intervention compositions.

Before adoption it requires:

1. explicit deficient intervention design;
2. exact residual causal abstraction and equivalence relation;
3. population grammar preventing utterance-ID lookup;
4. restrictions excluding arbitrary factor splitting, merging and re-encoding;
5. positive abstraction-refinement theorem;
6. matched impossibility theorem when language separation is removed;
7. unseen-form, component-tuple and target-block splits;
8. finite-sample guarantee or at least a consistent estimator;
9. direct comparison with logarithmic-environment unknown-target CRL, causal-abstraction baselines, WM3C, auxiliary-variable ICA and multi-view CRL;
10. completed external public capability reproduction.

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
3. canonical three-seed prediction/artifact/leakage contract;
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
