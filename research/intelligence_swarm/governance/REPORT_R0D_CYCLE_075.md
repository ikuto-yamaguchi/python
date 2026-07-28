# R0-D Cycle 075 — canonical instance identity audit

## Scope

This cycle remains limited to R0 benchmark reproducibility, statistics, and leakage auditing. It does not add or modify memory, replay, fast weights, sleep, or forgetting mechanisms.

## Failure mode

`evaluation_contract.py` rejects byte-identical duplicate `instance_id` values, but distinct raw strings that normalize to the same semantic identifier can still coexist. Examples include width/case aliases, whitespace-only differences, and invisible format characters. Such aliases can duplicate an evaluation instance, inflate per-cell sample counts, and contaminate paired statistics while retaining apparently distinct raw identifiers.

Prediction rows may also use a non-exact Unicode alias of a dataset identifier. Such aliases must not be silently resolved because exact instance binding is part of the same-instance evidence contract.

## Added fail-closed audit

`audit_canonical_instance_identity.py` now records and rejects:

- dataset identifiers that are empty after normalization;
- multiple raw dataset identifiers mapping to one canonical identifier;
- prediction identifiers that are non-exact aliases of a dataset identifier;
- missing prediction or dataset identifiers.

Normalization is Unicode NFKC plus case folding and removal of whitespace, control, and format characters. Any failure is classified as `initial_reproduction_failure`.

## Regression coverage

The focused test suite covers:

1. genuinely distinct identifiers;
2. width and case aliases;
3. whitespace and zero-width format aliases;
4. identifiers empty after normalization;
5. non-exact prediction aliases;
6. exact prediction binding.

A short GitHub Actions workflow compiles the auditor and core contract and runs these regressions without starting training.

## Current status

The focused auditor is present on the canonical reconstruction branch. Direct integration into `validate_dataset()` and `score()` remains required before this check becomes impossible to omit through the core entry points. Until a real R0 bundle passes every required dataset, prediction, statistics, resource, raw-log, checksum, and public-baseline contract, the reproduction result remains `initial_reproduction_failure`.
