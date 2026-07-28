# R0-D Cycle 043 — Core artifact acceptance hardening

## Scope

This cycle changes only the R0 reproducibility/evidence contract. It introduces no memory, replay, fast-weight, sleep, forgetting, architecture, or capability mechanism.

## Finding

`evaluation_contract.py audit-artifacts` still accepted two classes of non-reproduction evidence when invoked directly:

1. resource placeholders equal to zero, because measurements were checked as finite and non-negative rather than strictly positive;
2. checksummed artifacts outside the submitted bundle, because paths were joined to `base_dir` without enforcing relative-path containment, parent-traversal rejection, or symlink rejection.

The unified acceptance gate and companion auditors had stricter checks, but the core command remained independently callable. Therefore a caller could obtain a core `reproduced` result from an empty-measurement or externally referenced manifest without running the unified gate.

## Minimal correction

The core `audit_artifacts()` path now requires, for every method × seed × domain × split × condition run:

- `model_bytes > 0`;
- `peak_rss_bytes > 0`;
- `training_wall_seconds > 0`;
- `cpu_inference_ms_per_item > 0`;
- non-empty relative artifact paths;
- no `..` path traversal;
- no symlink component traversal;
- resolved paths contained inside the declared bundle root;
- non-empty regular files;
- independently recomputed SHA-256;
- exact model-file-size equality with `model_bytes`.

Any failure remains classified as `initial_reproduction_failure`.

## Regression coverage

`test_evaluation_contract_artifact_core.py` fixes the following cases:

- a complete six-method, three-seed, self-contained positive-measurement bundle passes;
- zero peak RSS fails closed;
- an absolute raw-log path fails closed;
- parent traversal fails closed;
- an empty artifact fails even when its SHA-256 is correct.

A short GitHub Actions workflow compiles the core contract and runs these tests without triggering the long SILG workflow.

## Research status

- accepted R0 bundle: 0
- accepted public baseline reproduction: 0
- accepted model/RSS/runtime/latency evidence bundle: 0
- capability progress: not recognized
- new intelligence principle: not recognized
- classification until a complete bundle passes: `initial_reproduction_failure`
