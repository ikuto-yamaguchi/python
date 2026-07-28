# R0-D Cycle 045 — Registered evaluation split scope

## Scope

This cycle advances R0 benchmark reproducibility, statistics, and leakage auditing only. It adds no memory mechanism, replay, fast weights, sleep, forgetting, toy mechanism, architecture family, branch, or PR chain.

## Defect found

The current scoring path constructs the evaluation set as every dataset instance whose split is not exactly `train`. Consequently, an exporter can introduce unregistered split names such as `debug`, `calibration`, `analysis`, or `posthoc`; those rows become prediction-coverage obligations and can enter domain × seed × condition statistics despite not being preregistered evaluation splits.

This is fail-open behavior because the benchmark contract already defines the only accepted evaluation split vocabulary as:

- `test`
- `eval`
- `validation`
- `valid`

A non-train predicate is not equivalent to membership in that vocabulary.

## Added fail-closed auditor

`audit_prediction_eval_split_scope.py` now requires:

1. Dataset split values are exactly `train` or one of the registered evaluation split names.
2. Predictions refer only to registered evaluation instances.
3. All six preregistered methods cover the same registered evaluation instances and cells:
   - correct
   - random
   - language-blind
   - state-only
   - target-label shuffle
   - outcome shuffle
4. Evaluation topology uses exactly seeds `1`, `7`, and `19`.
5. Missing domain × seed × split × condition coverage is rejected.

Any violation is classified as `initial_reproduction_failure`.

## Regression cases

The regression suite fixes the following behavior:

- canonical train/test data pass;
- `debug` split is rejected even when predictions are supplied;
- `calibration` predictions are rejected;
- predictions for train instances are rejected;
- one missing Outcome-shuffle instance/cell is rejected;
- noncanonical evaluation seed `23` is rejected.

## Evidence status

This cycle modifies only the audit contract. It does not produce or accept a public baseline reproduction bundle. No model bytes, peak RSS, training wall time, CPU inference latency, raw logs, prediction artifacts, statistics artifacts, or checksums are accepted by this change alone.

## Decision

- Accepted R0 bundle: 0
- Public baseline reproduction: not established
- Classification until a complete bundle passes: `initial_reproduction_failure`
- New intelligence principle: not established
- Capability progress: not established
- High-school-level intelligence: not achieved
