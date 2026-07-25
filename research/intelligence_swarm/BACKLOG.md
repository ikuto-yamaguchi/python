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

At RESET-E021, no completed 131,072-frame artifact is verified at the current canonical head. Previous attempts were blocked by a fixed harness timeout or repeatedly restarted by workflow triggers. Timeout scaling, concurrency and trigger scope have been corrected.

Authorized actions:

1. launch exactly one clean 131,072-frame run from the stable workflow head;
2. verify all three checkpoints and raw logs before incorporating any value;
3. evaluate Correct, Random, Language-blind, State-only and Language-shuffle on identical immutable instances;
4. record source/model/data/raw-log/prediction hashes, model bytes, RSS, training wall time, CPU latency, seeds and splits;
5. test policy competence and trajectory anti-collapse eligibility;
6. if competence is absent, correct only a verified official reproduction mismatch or classify resource/budget insufficiency at the preregistered ceiling.

Forbidden:

- tuning R0.2 on failed-policy trajectories;
- adding architecture or mechanism families;
- selecting favorable seeds or test instances;
- inferring language irrelevance from an incompetent policy;
- treating unfinished, canceled or duplicate workflow runs as evidence.

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

D015 is the latest fully executed contract layer, with **18 passing regression tests**. It adapts concrete SILG exporter fields, constructs prospective-only model input and rejects train/test identity overlap, utterance/entity/dynamics leakage, gold/post-treatment/completed-trajectory leakage, incomplete prediction coverage, bad fingerprints, incomplete resources and malformed hashes.

D016 adds the immutable prediction-to-dataset artifact join. Every measured run must provide:

- `prediction_path` and full `prediction_sha256`;
- readable prediction JSONL;
- manifest/prediction method identity agreement;
- unique prediction instance IDs;
- exact prediction/dataset instance-set equality;
- per-row instance-fingerprint agreement;
- one immutable dataset hash shared by all methods in each cell;
- stable model SHA and code commit for a method/seed across split and condition cells.

D017 adds `audit_dataset_cell_coverage.py`. Every `domain × split × condition` evaluation cell must contain exactly seeds `1,7,19`. Missing, extra and noncanonical seeds fail closed. The report stores observed/missing/extra seeds and dataset SHA-256 per cell.

A separate lightweight workflow, `.github/workflows/r0_evaluation_contract_tests.yml`, runs evaluation-contract tests without restarting SILG training. D016/D017 completion is not yet verified at the canonical head, so do not claim more than 18 passing tests.

Formal classification remains **`initial_reproduction_failure`** because real outcome-shuffle predictions, target-label-shuffle predictions or a formal inapplicability record, immutable serialized test data, complete six-method prediction/artifact joins and competent public capability are missing.

## P1 — R0.2 Environment-first faithful transfer

Old public trajectories are comparison-ineligible. Environment-first `0.6840`, End-to-end `0.6907`, State-only `0.7240`, and zero language-blind/shuffle gap are negative diagnostics only.

Source-policy failures: seed 1 success `0/40`; seed 7 `0/40` with `97.42%` majority action; seed 19 `1/40`; all test sets `0/20`.

Primary method reference:

- Gaddy & Klein 2019;
- authors' repository `dgaddy/environment-learning`;
- commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`.

The faithful implementation path now includes:

1. `gaddy_klein_typed_baseline.py`:
   - language-free transition pretraining;
   - 20 categorical message variables × 30 symbols;
   - straight-through Gumbel-Softmax;
   - shared typed next-state/action decoder;
   - LSTM language encoder;
   - direct environment/language message matching, weight `0.01`;
   - decoder frozen during language training by default;
   - categorical CE, binary BCE and continuous MSE;
   - exact seeds `1,7,19`, episode-disjointness, hashes and resource reporting.
2. `export_silg_typed_policy_trajectories.py`:
   - `state_before_fields`, `state_after_fields`, `state_schema`;
   - metadata-derived categorical cardinalities;
   - episode/seed/split/observation fingerprint provenance;
   - dataset and schema SHA-256;
   - fail-closed rejection of unknown fields/cardinalities;
   - exclusion of text, reward, done and outcomes from environment state.

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

`typed_discrete_message_and_typed_export_paths_implemented_execution_blocked`

Representation appearance, compression and clustering do not count as progress.

## Closed — Empirical Gate I / R0.3

Status: **formally rejected under current public-benchmark and no-researcher-ontology constraints**.

SILG/RTFM has no ground-truth latent intervention family, target, mechanism operator or causal abstraction. Do not add a hand-authored target/mechanism ontology or run hidden-intervention ablations on SILG. RQ-001-N5 is closed.

## Closed — Broad RQ-001 formulation

The following are rejected:

- raw utterance relations exceed every unrestricted finite auxiliary representation;
- raw language alone jointly identifies language factors and latent target blocks without grammar/mechanism restrictions;
- unknown intervention-target recovery is a language-specific contribution;
- language is required merely because targets are unknown, environments are incomplete, dynamics are nonlinear or observation mixing is nonparametric;
- language-shuffle degradation or semantic naming alone establishes causal identifiability.

Finite-index collapse permits `U=index(L)` on finite support. Re-encoding symmetry permits hidden language factors to be merged or split while preserving observations. Strongly separating and general-environment CRL results recover broad latent structure without language under their assumptions. If `L ⟂ M | X,E`, language cannot refine the remaining causal equivalence class.

## P2 — Only admissible RQ reformulation, not adopted

Allowed solely as a preregistration candidate:

> After exhausting general-environment non-language statistics, under an explicit population grammar and restricted non-lookup language-to-dynamics class, determine whether raw language supplies an independent separating relation that strictly refines a formally specified residual causal abstraction on unseen utterance forms and intervention compositions.

Before adoption it requires:

1. explicit deficient intervention design;
2. exact residual causal abstraction and equivalence relation;
3. proof that general-environment sufficient-change conditions fail;
4. `I(M;L|X,E)>0` plus a condition showing the information breaks the relevant symmetry;
5. population grammar preventing utterance-ID lookup;
6. restrictions excluding arbitrary factor splitting, merging and re-encoding;
7. positive abstraction-refinement theorem;
8. matched impossibility theorem when language separation is removed;
9. unseen-form, component-tuple and target-block splits;
10. finite-sample guarantee or at least a consistent estimator;
11. direct comparison with unknown-target/general-environment CRL, causal-abstraction baselines, WM3C, auxiliary-variable ICA and multi-view CRL;
12. completed external public capability reproduction.

No implementation, synthetic benchmark or architecture is authorized before preregistration.

## P1 — Prior-art and novelty matrix

Maintain primary-source comparison through 2026 for unknown/uncoupled interventions, causal abstractions, finite-sample and general-environment CRL, auxiliary/temporal/multi-view/hidden-regime ICA, grouping and weak supervision, mechanistic independence, mechanism sparsity, interactive grounding, environment-first, language-dynamics pretraining, causal world-model interfaces and WM3C.

Broad language-as-auxiliary, shuffle-negative, shared-view, unknown-target recovery, utterance-grouping, supplied-language-component block identification, unseen recombination and environment-label-recovery claims are not novel.

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
