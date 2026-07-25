# R0-D Cycle 016 — Immutable prediction-to-dataset artifact join

## Scope

This cycle advances only R0 benchmark reproducibility, statistics and leakage auditing on the canonical reconstruction branch. It introduces no memory, replay, fast weights, sleep, forgetting, toy mechanism or architecture family.

## Gap found

`evaluation_contract.py` already required readable raw-log, model and dataset artifacts with full SHA-256 values. It also checked in-memory prediction coverage and same-instance fingerprints when scoring a supplied prediction file.

However, the artifact manifest did not prove that the predictions used for a reported run were themselves immutable artifacts, nor that each method's prediction file covered exactly the instances in the declared dataset cell. A manifest could therefore pass its resource audit while the separately supplied predictions were changed, truncated, drawn from another dataset snapshot, or evaluated under a different model/code identity across conditions.

## Added fail-closed audit

Added:

- `audit_evaluation_bundle.py`
- `test_audit_evaluation_bundle.py`

The new audit composes the existing `audit_artifacts` checks and additionally requires, for every `method × seed × domain × split × condition` run:

- `prediction_path`
- full `prediction_sha256`
- a readable prediction JSONL artifact
- prediction method identity matching the manifest method
- unique prediction instance IDs
- exact set equality between prediction IDs and the immutable dataset cell
- per-row instance fingerprint agreement with the dataset artifact
- one dataset hash shared by all methods in a cell
- one stable model SHA/code commit for a method and seed across split/condition cells

Any violation is classified as:

`initial_reproduction_failure`

## Regression coverage added

The new tests cover:

1. a complete six-method, three-seed exact join;
2. missing prediction artifact provenance;
3. prediction/dataset instance mismatch;
4. changing model identity between evaluation conditions.

The tests are committed but were not executed by a GitHub Actions job in this cycle because the existing long-running SILG workflow does not include these new paths, and changing that workflow would restart the ongoing public-baseline training. No passing test count is claimed here.

## Current result

The existing completed SILG evidence still lacks a complete immutable prediction artifact join for all of:

- correct
- random
- language-blind
- state-only
- target-label shuffle
- outcome shuffle

across canonical seeds, domains, splits and conditions. Therefore the formal classification remains:

`initial_reproduction_failure`

This cycle strengthens evidence integrity only. It does not establish benchmark capability, novelty, an intelligence principle or capability progress.
