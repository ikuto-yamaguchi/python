# R0.2 Cycle 014 — Immutable holdout manifest join

## Scope

This cycle advances the faithful Environment-first representation baseline without adding a new operation/goal toy hypothesis, model family, or architecture.  It addresses the concrete dataset blocker identified in Cycle 013: the typed SILG exporter emitted placeholder holdout labels rather than real entity, dynamics, and language-form partitions.

## Completed work

Added `attach_r02_holdout_manifest.py`, a fail-closed dataset-governance adapter that joins a preregistered episode-level manifest onto typed SILG trajectories using the exact key:

- `domain`
- `split`
- `seed`
- `episode_seed`

The manifest must provide non-empty:

- `entity_signature`
- `dynamics_signature`
- `language_form_signature`

and explicit Boolean assignments for:

- `entity_holdout`
- `dynamics_holdout`
- `language_holdout`

The adapter rejects duplicate manifest keys, non-canonical seeds, train episodes marked as held out, missing episode assignments, and extra manifest episodes.  Every output row records the immutable manifest SHA-256.  The summary also records input trajectory SHA-256, output dataset SHA-256, episode count, and held-out episode counts.

This deliberately does **not** infer a holdout from model predictions, task success, reward, next-state error, or action accuracy.  It therefore removes the prior placeholder annotations without introducing outcome-dependent split selection.

## Regression contract

Added `test_attach_r02_holdout_manifest.py` covering:

1. exact episode-level joining across multiple steps;
2. rejection of an uncovered exported episode;
3. rejection of a held-out train episode;
4. rejection of duplicate manifest keys.

CI completion is not claimed in this report.  The tests are committed but must still be executed by the lightweight R0.2 workflow or an equivalent pinned environment.

## Remaining blocker

A valid manifest itself is not yet present.  It must be generated from the fixed RTFM generator/configuration and committed before predictions or evaluation outcomes are inspected.  It must include real, non-overlapping entity, dynamics, and language-form signatures with seed `1 / 7 / 19` coverage, then pass `audit_r02_holdout_assignments.py`.

After that, the minimal execution path is:

1. finish or obtain a competent three-seed R0.1 recurrent policy;
2. export typed trajectories for the fixed train/test environments;
3. attach the preregistered manifest and preserve all hashes;
4. run the matched Environment-first, End-to-end, and State-only comparison;
5. measure online task success independently from offline action and next-state metrics;
6. save model bytes, peak RSS, training wall time, CPU inference latency, dependencies, raw logs, seeds, splits, and checksums.

## Classification

`immutable_holdout_join_implemented_manifest_generation_and_qualified_silg_execution_blocked`

R0.2 public-data reproduction remains incomplete.  No novelty, intelligence principle, or capability progress is claimed.
