# R0-D Cycle 057 — Artifact evaluation split scope

## Scope

This cycle continues R0 reproducibility, statistics, and leakage auditing only. It does not add memory, replay, fast weights, sleep, forgetting, or any new intelligence mechanism.

## Defect

`evaluation_contract.audit_artifacts()` derives its expected run topology from whatever `split` strings appear in the manifest. It verifies method, seed, domain, condition, resources, checksums, and observed-topology coverage, but it does not require resource runs to belong to the registered evaluation split vocabulary.

Consequently a self-consistent manifest could use `train`, `debug`, `calibration`, `analysis`, or `posthoc` cells and still satisfy the resource topology audit. Such cells are not evidence for the registered R0 evaluation population.

## Added fail-closed audit

`audit_artifact_eval_split_scope.py` requires every resource run to use one of:

- `test`
- `eval`
- `validation`
- `valid`

The audit records the raw and normalized split for every run. Missing, train, and unregistered split values are classified as `initial_reproduction_failure`.

## Regression coverage

The focused test fixes the following cases:

1. canonical `test` run cells pass;
2. case-normalized `VALIDATION` passes;
3. `train` resource cells fail;
4. `debug` resource cells fail;
5. `posthoc` resource cells fail;
6. missing split fails.

A short GitHub Actions workflow compiles the core contract and auditor and runs the focused regression without starting long SILG training.

## Current qualification

No real R0 bundle is accepted by this cycle. Public baseline reproduction, resource measurements, raw logs, and statistics remain unqualified until one self-contained bundle passes every mandatory contract. The formal state remains `initial_reproduction_failure`.

## Remaining direct integration

The split-scope requirement is currently a focused auditor. The same membership check still needs to be made unavoidable inside `evaluation_contract.audit_artifacts()` and the unified acceptance gate.
