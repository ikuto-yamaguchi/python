# R0-D Cycle 028 — Exact Prediction-Method Topology

## Scope

This cycle advances only R0 benchmark reproducibility, statistics, and leakage auditing. It adds no memory, replay, fast-weights, sleep, forgetting, toy mechanism, architecture family, or new branch.

## Defect closed

`evaluation_contract.score()` requires complete coverage for the registered controls, but historical prediction bundles could still contain an additional unregistered method. Such a method could enter summary/cell statistics and be compared against `correct`, despite not being preregistered and despite having no corresponding artifact/resource cell.

This violates the fail-closed requirement that every evaluation instance and every `seed × domain × split × condition` cell use exactly the same preregistered method topology.

## Implementation

Added `audit_prediction_method_topology.py`, which composes the existing dataset and scoring contracts and additionally requires exactly:

- `correct`
- `random`
- `language_blind`
- `state_only`
- `target_label_shuffle`
- `outcome_shuffle`

The auditor rejects:

- any unregistered extra prediction method;
- any required method missing globally;
- any required method missing on one evaluation instance;
- any required method missing from one cell;
- predictions outside the evaluation set;
- any failure already reported by `validate_dataset()` or `score()`.

Failure classification is `initial_reproduction_failure`.

## Regression coverage

`test_audit_prediction_method_topology.py` fixes four cases:

1. exact six-method topology passes;
2. an unregistered `representation_probe` method fails;
3. `state_only` missing on one instance fails;
4. `outcome_shuffle` missing from one seed cell fails.

The dedicated short CI workflow compiles the auditor, the evaluation contract, and the tests, then runs the regression suite. It does not launch the long SILG training workflow.

## Status

- accepted real R0 bundle: none newly established;
- public baseline reproduction: not newly established;
- capability progress: not recognized;
- classification remains `initial_reproduction_failure` until the immutable real bundle passes all contracts.
