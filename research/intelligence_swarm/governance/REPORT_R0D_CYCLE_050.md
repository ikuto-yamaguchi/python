# R0-D Cycle 050 — core evaluation split scope

## Scope

R0 benchmark reproducibility, statistics, and leakage auditing only. No memory, replay, fast weights, sleep, forgetting, architecture, or mechanism work was added.

## Defect closed

`evaluation_contract.score()` previously treated every dataset row whose split was not exactly `train` as an evaluation instance. Unregistered post-hoc splits such as `debug`, `calibration`, `analysis`, or `posthoc` could therefore enter prediction coverage, domain×seed×condition cells, confidence intervals, and paired tests.

## Fail-closed contract

- training split: exactly `train`
- evaluation splits: exactly `test`, `eval`, `validation`, or `valid`
- all other split labels are rejected by `validate_dataset()`
- `score()` constructs evaluation IDs only from the registered evaluation vocabulary
- predictions for train or unregistered splits are rejected
- the accepted split vocabulary is written into validation and scoring evidence
- failure classification remains `initial_reproduction_failure`

## Verification

Focused regression covers clean train/test data and explicit rejection of `debug`, `calibration`, `analysis`, and `posthoc`. The scorer keeps those rows outside the evaluation denominator even while reporting their presence as a fatal contract violation.

## Research status

No real R0 artifact bundle is accepted by this change. No public baseline reproduction, capability progress, novelty, or intelligence principle is claimed.
