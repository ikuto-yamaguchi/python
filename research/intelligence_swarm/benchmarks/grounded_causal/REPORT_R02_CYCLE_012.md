# R0.2 Cycle 012 — Matched data-exposure and resource audit

## Scope

This cycle adds no operation/goal hypothesis, architecture family, memory mechanism,
or new branch. It tightens the existing Gaddy--Klein-style Environment-first versus
End-to-end versus State-only comparison contract.

## Completed item

A fail-closed result-bundle auditor was added:

- `audit_r02_matched_budget.py`
- `test_audit_r02_matched_budget.py`

The auditor verifies that one R0.2 comparison result contains:

- canonical seed `1`, `7`, or `19`;
- non-empty `train` and `test` splits;
- immutable dataset SHA-256;
- identical training-row exposure for Environment-first, End-to-end, and State-only;
- exact Environment-first versus End-to-end inference parameter-byte equality;
- separately recorded transition-pretraining-only bytes;
- complete test prediction coverage for all three methods;
- action accuracy and typed next-state loss;
- CPU inference latency;
- training wall-time components and peak RSS;
- checkpoint bytes and SHA-256 for every method.

For `n_train = N`, environment epochs `E`, and language epochs `L`, the enforced
row-exposure accounting is:

- Environment-first: `N*E + N*L`;
- End-to-end: `N*(E+L)`;
- State-only: `N*(E+L)`.

A mismatch is classified as `initial_reproduction_failure`.

If all offline checks pass but independently generated online SILG task success is
absent, the classification is:

`matched_offline_budget_audit_passed_online_task_success_pending`

Offline action accuracy or next-state prediction is never substituted for online
task success.

## CI

The lightweight `R0.2 typed comparison tests` workflow now runs both the typed
comparison regression and matched-budget audit tests. This workflow does not start
the long R0.1 SILG training job.

## Current limitation

No qualified three-seed SILG trajectory bundle exists because a competent R0.1
source policy has not yet been reproduced. Therefore this cycle validates the
comparison and audit path only; it is not a public-benchmark result.

## Decision

Classification:

`matched_data_and_resource_audit_implemented_qualified_silg_execution_blocked`

- R0.2 formal reproduction: incomplete
- public capability progress: not recognized
- novelty or intelligence principle: not claimed
- high-school-level intelligence: not achieved
