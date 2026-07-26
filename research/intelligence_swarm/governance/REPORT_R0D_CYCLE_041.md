# R0-D Cycle 041 — Bundle-contained artifact paths are mandatory

## Scope

This cycle advances only R0 benchmark reproducibility, statistics, leakage, and evidence-chain auditing. It adds no memory, replay, fast weights, sleep, forgetting, architecture, toy mechanism, intelligence principle, or capability claim.

## Defect

`audit_artifact_path_containment.py` already rejected absolute paths, `..` escapes, symlink traversal, empty files, and references resolving outside the evidence-bundle root. However, the canonical single acceptance gate did not invoke that auditor.

Consequently, an otherwise valid bundle could pass the unified acceptance path while its model, dataset, raw log, prediction, or statistics path referred to bytes outside the archived bundle. A matching checksum proves only which bytes were read; it does not prove those bytes were preserved inside the reproduction artifact.

## Change

`audit_r0_acceptance_bundle.py` now requires `artifact_path_containment_contract` in the same fail-closed invocation as:

1. dataset/split/leakage validation;
2. alias-normalized schema leakage validation;
3. prediction payload validation;
4. same-instance paired statistics;
5. model/data/raw-log/resource/checksum validation;
6. strictly positive measured resources;
7. prediction/statistics evidence checksums.

The bundle is rejected when any referenced artifact path is absolute, contains a parent-directory escape, traverses a symlink, resolves outside the bundle root, is not a regular file, or is empty.

## Regression coverage

The unified-gate tests now prove that:

- all contracts must pass for `reproduced`;
- path-containment failure alone rejects an otherwise valid bundle;
- a successful checksum/resource audit cannot hide an external artifact reference;
- path-containment failure is preserved alongside alias, payload, measurement, and statistics failures;
- every failure is classified as `initial_reproduction_failure`.

The unified short CI compiles the path-containment auditor and is triggered when that dependency changes.

## Research status

- Accepted real R0 bundle: **0**
- Accepted public baseline reproduction: **0**
- Accepted model/RSS/runtime/CPU-latency evidence bundle: **0**
- Capability progress: **not recognized**
- New intelligence principle: **not recognized**
- Failure classification until all contracts pass: **`initial_reproduction_failure`**
