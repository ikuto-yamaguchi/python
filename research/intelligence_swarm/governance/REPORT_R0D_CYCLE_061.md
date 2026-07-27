# R0-D Cycle 061 — Raw-log measurement binding in the unified acceptance gate

## Scope

This cycle continues R0 benchmark reproducibility, statistics, and leakage auditing only. It introduces no memory, replay, fast-weights, sleep, or forgetting mechanism.

## Defect

The focused `audit_raw_log_measurement_binding.py` auditor already rejected resource manifests whose raw logs did not contain exactly one machine-readable measurement record matching the declared run cell and resource/provenance values. However, the unified acceptance gate did not invoke that auditor.

A bundle could therefore pass the unified gate when the model/data/raw-log files and their checksums were present, while the raw log itself was unrelated to the manifest's `model_bytes`, `peak_rss_bytes`, `training_wall_seconds`, `cpu_inference_ms_per_item`, commit, or artifact checksums.

## Change

`audit_r0_acceptance_bundle.py` now requires `raw_log_measurement_binding_contract` together with every existing contract.

The gate rejects the whole bundle when the raw log:

- lacks a matching machine-readable measurement record;
- contains more than one matching record for the same method × seed × domain × split × condition cell;
- reports a different code commit or model/data checksum;
- reports different model bytes, peak RSS, training wall time, or CPU inference latency;
- is plain text or otherwise cannot be bound to the declared run.

The failure classification remains `initial_reproduction_failure`.

## Regression

`test_acceptance_raw_log_measurement_binding.py` fixes two cases:

1. all contracts, including raw-log binding, pass and the bundle is `reproduced`;
2. every other contract passes but raw-log binding fails, and the bundle is rejected solely as `initial_reproduction_failure`.

The unified acceptance workflow now compiles the raw-log auditor, watches it and the focused regression, and executes the regression.

## Status

- Unified-gate omission path: closed.
- `evaluation_contract.audit_artifacts()` direct-core raw-log binding: still pending.
- Accepted real R0 bundles: 0.
- Public baseline reproduction: not certified.
- Classification: `initial_reproduction_failure`.
