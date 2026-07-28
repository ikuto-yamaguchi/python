# R0 Research Reconstruction — RESET-E025

Date: 2026-07-25
Branch: `research/intelligence-swarm-reconstruction-001`
Stage: R0 public capability reproduction and benchmark qualification

## Scope and governance

This integration accumulates only public benchmark reproduction, prior-art audit, evaluation-contract qualification, and the already closed hidden intervention-target track. It introduces no A–D toy mechanism, operation/goal toy hypothesis, memory/replay/fast-weights/sleep/forgetting mechanism, architecture family, intervention ontology, branch, or PR chain. Existing stacked draft PRs remain negative-results archives and are not bases for active work.

No external learned capability baseline has been reproduced. Therefore novelty, an intelligence principle, capability progress, and high-school-level intelligence remain unrecognized.

## 1. Primary literature and official-code overlap audit

C018 added Morioka and Hyvärinen, **Causal Representation Learning Made Identifiable by Grouping of Observational Variables**, ICML 2024, and the official `hmorioka/GCaRL` implementation at audited commit `0020bfce34736d61d70ab8175f061d02951a7ed4`.

The result identifies qualifying latent variables from observations partitioned into known groups under group-wise invertible mixing, graph nondegeneracy, causal-function variation/asymmetry, and population/optimization assumptions. It does not require language, intervention labels, weak supervision, or temporal ordering.

Consequences for RQ-001:

- known sensor/modality/object-slot/time/field grouping is already a non-language identifiability route;
- language that predicts or restates grouping metadata recoverable from observations does not jointly identify a grouping and latent intervention-target partition;
- a G-CaRL-style estimator succeeding after a grouping is supplied is conditional identification, not evidence that raw language discovered the grouping;
- interactive replies determined by state, schema, environment ID, action history, or grouping metadata do not shrink the population causal equivalence class.

The remaining candidate is narrowed to externally anchored joint grouping-and-partition identification after intervention, general-environment, trajectory-local, multimodal partial-sharing, and known-grouping criteria have been exhausted. It is not adopted. The G-CaRL repository exposes training/evaluation code but does not provide an exact dependency lock, so no reproduction is claimed.

## 2. SILG / J-CRe3 reproduction progress

### R0.1 SILG / RTFM

Pinned conditions remain:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent, no pretrained language model
- train `silg:rtfm_train_s1-v0`
- test `silg:rtfm_test_s1-v0`
- seeds `1 / 7 / 19`
- Python 3.8.18 on Ubuntu 22.04 with pinned core dependencies

Accepted evidence remains the 32,768-requested-frame staged run:

- parameters: `4,916,915`
- state-dict audit bytes: `19,694,385`
- maximum RSS: `505,600 KiB`
- total three-seed training wall time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct win rate: `0.0167` (`1/60`)
- Random win rate: `0.0667` (`4/60`)
- Language-blind / State-only / Language-shuffle: each `0.0167`

Correct remains below Random. This is an incompetent-policy result, not public capability reproduction and not evidence that language is irrelevant.

At pre-integration head `8325ff9f63e8d782209cccce232170adc95689bb`, no combined CI status was registered. No verified completed 131,072-frame artifact is accepted. Unfinished, cancelled, duplicate, or unbound artifacts remain excluded.

### R0.2 Environment-first

Cycle 014 added `attach_r02_holdout_manifest.py`, which joins a preregistered immutable episode manifest to typed trajectories using `(domain, split, seed, episode_seed)`. It requires non-empty entity, dynamics, and language-form signatures plus explicit Boolean holdout assignments; rejects duplicate, missing, extra, non-canonical, or train-held-out entries; and records manifest/input/output SHA-256 values.

This closes the adapter gap but not the dataset gap. A valid manifest generated from the pinned RTFM generator/configuration before predictions or outcomes are inspected still does not exist. Qualified three-seed source trajectories, real non-overlapping holdouts, online task success, typed next-state prediction, action accuracy, and matched Environment-first / End-to-end / State-only execution remain absent.

Classification: `immutable_holdout_join_implemented_manifest_generation_and_qualified_silg_execution_blocked`.

### J-CRe3

The official `riken-grp/J-CRe3` candidate remains unreproduced. It is not averaged into SILG and is not used to reopen the rejected hidden-target track.

## 3. Matched controls

The required immutable-instance comparison remains:

- official recurrent Correct
- random valid action
- language-blind
- state-only
- target-label shuffle when a non-oracle target label exists, otherwise a formal inapplicability record
- outcome / transition shuffle

Environment-ID-only and within-environment language shuffle remain governance-required auxiliary controls. No favorable seed, instance, or average-only positive is admissible.

## 4. Resource, seed, split, and artifact accounting

D021 added `audit_runtime_artifact_cells.py`. Every `method × seed × domain × split × condition` cell must now bind:

- prediction path and SHA-256
- dataset path and SHA-256
- raw log and SHA-256
- checkpoint, SHA-256, and exact byte count where applicable
- full 40-hex code commit
- model bytes
- peak RSS
- training wall time
- CPU inference latency

The audit requires exact seeds `1 / 7 / 19`, identical cell coverage across all six methods, one shared dataset hash per cell, stable checkpoint/commit per method and seed across conditions, and rejects copied full resource/artifact tuples across methods. Random has no checkpoint requirement but still requires immutable predictions, data, logs, code provenance, RSS, runtime, and CPU latency.

The committed regression cases cover a complete bundle, post-manifest prediction mutation, a missing State-only seed/cell, and checkpoint switching across conditions. CI completion is not claimed, and the real R0 bundle has not passed D021.

## 5. Leakage and statistical qualification

The evaluation contract now cumulatively includes:

- D015 real SILG schema adaptation and 18 executed regression tests;
- D016 immutable prediction-to-dataset joins and complete prediction coverage;
- D017 exact seed coverage per domain/split/condition cell;
- D018 semantic target-label/outcome shuffle provenance and no-op rejection;
- D019 condition-scoped entity/dynamics holdout integrity;
- D020 episode-cluster hierarchical bootstrap and episode-level paired sign-flip testing;
- D021 runtime/resource/artifact binding to the exact evaluated cell.

The real public-baseline dataset/prediction/artifact bundle has not passed D016–D021. Formal classification remains `initial_reproduction_failure`.

## 6. RQ-001 decision

Rejected routes now include unknown-target recovery alone, environment-label recovery, parameter naming, non-zero language effects, partial shared-latent discovery, language as an extra modality by itself, and language that merely supplies grouping recoverable from non-language observations.

The only surviving candidate is:

> After applying intervention-based, general-environment, trajectory-local, multimodal partial-sharing, and known-observational-grouping identifiability criteria, can an externally anchored population language channel jointly identify an otherwise unknown observational grouping and a residual latent intervention-target partition, rather than merely restating grouping metadata recoverable from non-language observations?

Decision: **narrowed, not adopted; preregistration candidate only**.

Before adoption it requires a formal residual equivalence class, proof that the language information is not measurable from schema/state/history metadata, an anchor that cannot be jointly recoded, a joint grouping-and-partition theorem, a matched impossibility theorem without the anchor, direct grouping metadata and G-CaRL comparisons, unseen form/composition/system evaluation, dependency-pinned public baseline reproduction, and a completed preregistration.

No RQ implementation or new architecture is authorized.

## R0.1–R0.3 and stage decision

- R0.1 learned public capability baseline: **not reproduced**
- R0.2 formal Environment-first reproduction: **not completed**
- R0.3 empirical hidden intervention-target ablation: **rejected and remains closed**
- novelty matrix: **expanded through C018 but not closed for stage transition**
- central successor proposition preregistration: **not completed**
- next stage proposal: **none**

## Single maximum bottleneck

Complete and audit exactly one clean 131,072-frame official SILG recurrent run with three checkpoints, immutable matched controls, policy-competence and action-collapse checks, complete source/model/data/log/prediction hashes, cell-bound resources, canonical seeds and splits. Until then, R0.2 tuning, RQ-001 implementation, and new architecture work remain prohibited.

## Formal status

- reproduction classification: **`initial_reproduction_failure`**
- public capability baseline: **not reproduced**
- novelty: **not established**
- intelligence principle: **not discovered**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- completion: **false**
