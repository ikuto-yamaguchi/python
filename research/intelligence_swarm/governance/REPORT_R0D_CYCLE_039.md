# R0-D Cycle 039 — Nonzero measured-resource and artifact audit

## Scope

This cycle advances only R0 benchmark reproducibility and evidence auditing on the canonical reconstruction branch. It does not add memory, replay, fast weights, sleep, forgetting, a new architecture, or a toy mechanism.

## Defect found

The core artifact contract accepted finite **non-negative** values for:

- `model_bytes`
- `peak_rss_bytes`
- `training_wall_seconds`
- `cpu_inference_ms_per_item`

Consequently, a structurally complete manifest could use zero-valued placeholders for measurements that had never been taken. Independently hashed model, data, and raw-log paths could also point to empty files. Such a bundle is not a completed public-baseline reproduction.

## Added fail-closed audit

`audit_nonzero_measurements.py` requires every run to contain:

- finite, strictly positive model bytes;
- finite, strictly positive peak RSS;
- finite, strictly positive training wall time;
- finite, strictly positive CPU inference latency;
- non-empty model, dataset, and raw-log artifacts;
- independently recomputed SHA-256 matches;
- exact agreement between `model_bytes` and the model artifact size.

Any violation is classified as `initial_reproduction_failure`.

## Regression coverage

The focused test suite fixes the following cases:

1. measured non-empty bundle passes;
2. zero model bytes fails;
3. zero peak RSS fails;
4. zero training time fails;
5. zero CPU latency fails;
6. empty artifact fails even when its checksum is correct;
7. model-size mismatch fails.

A short GitHub Actions workflow runs compile and regression checks without starting SILG training.

## Status

- Accepted R0 reproduction bundle: 0
- Accepted public baseline value: 0
- New capability evidence: none
- New intelligence principle: none
- Failure classification until all contracts pass: `initial_reproduction_failure`
