# R0-D Cycle 087 — canonical split identity core hardening

## Scope

This cycle continues R0 benchmark reproducibility, statistics, and leakage auditing only. It does not add memory, replay, fast weights, sleep, or forgetting mechanisms.

## Finding

`evaluation_contract.py` used several independent `str(split).lower()` conversions in dataset topology, scoring eligibility, cell identity, instance fingerprints, and holdout checks. Unicode-width, whitespace, and format-character aliases could therefore partition equivalent train/evaluation evidence or bind fingerprints and cells inconsistently.

Examples include `test`, `ＴＥＳＴ`, `te\u200bst`, and ` test `.

## Change prepared on the canonical branch

Cycle 087 adds a shared `canonical_split()` based on NFKC, case folding, and whitespace/control/format removal. Registered evidence must still use the exact canonical spelling; aliases are detected rather than silently accepted.

The core patch routes `_cell_key()`, instance fingerprints, dataset topology, holdout matching, score dataset split checks, and evaluation-instance selection through the shared identity. `validate_dataset()` records non-canonical raw spellings as contract errors. Because `score()` is already bound to dataset validity, those errors suppress cells, summaries, and paired statistics and classify the submission as `initial_reproduction_failure`.

## Regression

The focused regression fixes the following requirements:

- `train`, `test`, and other registered canonical labels remain valid.
- full-width, zero-width-character, and padded aliases are rejected;
- aliases canonicalize to the same identity for leakage/fingerprint comparison;
- invalid split spelling makes the dataset contract invalid;
- canonical split identity requirements are persisted in the audit artifact.

## Status

The patch, focused regression, and workflow are accumulated on `research/intelligence-swarm-reconstruction-001`. Core integration is not considered complete until the workflow applies the patch and the regression passes. No R0 bundle or public baseline reproduction is accepted by this cycle alone.

Formal classification remains `initial_reproduction_failure`.
