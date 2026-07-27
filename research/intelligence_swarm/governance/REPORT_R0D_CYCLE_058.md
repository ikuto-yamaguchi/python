# R0-D Cycle 058 — Resource-cell evaluation split scope in the unified gate

## Scope

This cycle continues R0 benchmark reproducibility, statistics, and leakage auditing only. It does not add memory, replay, fast weights, sleep, forgetting, or another model mechanism.

## Defect

`audit_artifact_eval_split_scope.py` already rejected resource-manifest runs whose `split` was `train` or an unregistered value such as `debug`, `calibration`, `analysis`, or `posthoc`.

The unified acceptance gate did not call that auditor. Consequently, a bundle could pass the core resource artifact checks, positive measurement checks, path containment checks, prediction/statistics checks, and paired-statistics checks while its resource evidence described a non-evaluation split.

A checksum proves the bytes that were submitted; it does not prove that the run belongs to the preregistered evaluation population.

## Change

`audit_r0_acceptance_bundle.py` now requires `artifact_eval_split_scope_contract` in the same fail-closed invocation as all other R0 contracts.

Accepted resource runs must use one of:

- `test`
- `eval`
- `validation`
- `valid`

Resource runs using `train` or any unregistered split reject the entire bundle as `initial_reproduction_failure`, even when every other contract returns `valid=true`.

The acceptance artifact now records:

- `resource_runs_must_use_registered_evaluation_splits=true`
- `train_resource_cells_forbidden=true`
- `unregistered_resource_cells_forbidden=true`

## Regression

`test_acceptance_artifact_eval_split_scope.py` fixes two cases:

1. all contracts, including resource split scope, pass;
2. resource split scope alone fails while core resource and paired-statistics checks pass, and the complete bundle is rejected.

## Current status

This cycle closes omission of the focused resource split auditor from the unified acceptance path. Direct enforcement inside `evaluation_contract.audit_artifacts()` remains a separate core-hardening task.

No R0 evidence bundle or public baseline reproduction is accepted by this report itself.
