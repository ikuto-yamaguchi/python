# R0-D Cycle 033 — prediction payload checks integrated into the evaluation contract

## Scope

This cycle changes only R0 benchmark reproducibility, leakage, and statistical acceptance. It introduces no memory mechanism, replay, fast weights, sleep, forgetting, architecture, or intelligence claim.

## Defect closed

`audit_prediction_payload_leakage.py` already rejected gold labels, outcomes, completed trajectories, unregistered debug fields, non-finite predictions, and actions outside the instance action schema. However, callers could invoke `evaluation_contract.py score` directly and bypass that companion audit while still obtaining coverage and paired statistics.

## Canonical correction

`evaluation_contract.score()` now fails closed before accepting prediction rows when any of the following occurs:

- gold action, gold after-state, inverse label, answer, or label is embedded in prediction JSONL;
- reward, terminal status, episode return/success, future state, rollout, or completed trajectory is embedded;
- an unregistered top-level prediction field is present;
- `pred_state_after` or `pred_inverse` contains NaN, Infinity, or an unsupported non-JSON value;
- `pred_action` violates the instance `valid_action_mask` / `valid` schema.

The score report now preserves payload findings and explicitly records strict schema, finite-value, and valid-action checks. Any failure is classified as `initial_reproduction_failure`.

## Regression coverage

A focused regression suite covers:

1. a clean six-method same-instance bundle;
2. leaked `gold_state_after`;
3. leaked `completed_trajectory`;
4. an unregistered debug payload;
5. a non-finite predicted state;
6. an action outside the valid-action schema.

A short GitHub Actions workflow compiles and runs only this contract regression. It does not trigger the long SILG reproduction workflow.

## Research status

- accepted real R0 bundle: 0
- accepted public baseline reproduction: 0
- accepted model/RSS/runtime/latency evidence bundle: 0
- new capability claim: none
- new intelligence principle claim: none
- current failure classification until a complete bundle passes: `initial_reproduction_failure`
