# R0-D Cycle 060 — Raw-log measurement binding

## Scope

This cycle advances only R0 benchmark reproducibility, statistics, leakage, and evidence auditing on the canonical reconstruction branch. It does not add memory, replay, fast weights, sleep, forgetting, or any other mechanism family.

## Defect

The artifact contract previously required a non-empty raw log and a matching SHA-256, but the manifest's resource claims were not bound to any machine-readable record inside that log. A submitter could therefore preserve an unrelated checksummed log while independently writing favorable values for model bytes, peak RSS, training wall time, or CPU inference latency into the manifest.

A checksum fixes bytes; it does not prove that those bytes contain the claimed measurement.

## Fail-closed contract

`audit_raw_log_measurement_binding.py` requires exactly one machine-readable measurement record for every manifest run. JSON, JSONL, and nested JSON event containers are supported.

The matching record is selected by the exact normalized cell:

- method
- seed
- domain
- split
- condition

The record must then exactly match the manifest for:

- full code commit SHA
- model bytes
- peak RSS bytes
- training wall seconds
- CPU inference milliseconds per item
- model artifact SHA-256
- data artifact SHA-256

Zero matching records, duplicate matching records, wrong-cell records, non-finite measurements, plain-text-only logs, or any value mismatch are classified as `initial_reproduction_failure`.

Only registered evaluation splits (`test`, `eval`, `validation`, `valid`) are accepted.

## Regression coverage

`test_audit_raw_log_measurement_binding.py` covers:

1. one exact JSONL measurement record;
2. manifest/log resource mismatch;
3. missing measurement record;
4. duplicate measurement records;
5. wrong seed/cell record;
6. nested JSON event containers;
7. plain-text logs failing closed.

The focused suite passes locally with seven tests.

## Status

- canonical branch accumulation: completed
- raw-log checksum-to-measurement binding auditor: added
- focused regression suite: added and locally passing
- direct integration into `evaluation_contract.audit_artifacts()`: pending
- direct integration into the unified acceptance gate: pending
- accepted real R0 bundle: 0
- public baseline reproduction: not recognized
- formal classification: `initial_reproduction_failure`
