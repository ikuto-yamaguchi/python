# R0-D Cycle 040 — Artifact bundle path-containment audit

## Scope

This cycle changes no model, memory mechanism, replay policy, fast weights, sleep,
forgetting mechanism, benchmark task or research hypothesis.  It strengthens only
the reproducibility evidence boundary for the canonical R0 benchmark bundle.

## Defect found

The existing artifact audit verifies file existence, SHA-256 and selected resource
metadata after constructing each path as `base_dir / manifest_path`.  It did not
establish that the resolved artifact was actually contained by the submitted bundle.
Consequently, a manifest could reference:

- an absolute path outside the bundle;
- a `../` parent-directory escape;
- a symlink inside the bundle that resolves to an external model, dataset, log,
  prediction or statistics file.

A matching checksum proves which external bytes were read, but does not make those
bytes part of the archived reproduction evidence.  Such a bundle is not portable,
immutable or independently replayable.

## Added fail-closed audit

`audit_artifact_path_containment.py` now requires every declared artifact path to:

1. be non-empty and relative;
2. contain no parent-directory component;
3. traverse no symlink component;
4. resolve inside the canonical bundle root;
5. resolve to a non-empty regular file.

The audit covers run-level model, dataset, raw-log and prediction paths and
bundle-level prediction/statistics paths when present.  Any failure is classified as
`initial_reproduction_failure`.

This audit is complementary to SHA-256 validation: path containment proves the
artifact was shipped in the evidence bundle; checksums prove the shipped bytes match
the manifest.

## Regression cases

The focused tests fix the following behavior:

- a self-contained bundle passes;
- an absolute external model path fails;
- a `../` raw-log escape fails;
- a symlink to an external artifact fails;
- an empty artifact fails;
- a manifest with no auditable artifact references fails.

A short GitHub Actions workflow was added for compilation and focused tests.  It does
not trigger the long SILG/RTFM training workflow.

## Research status

- Accepted real R0 bundle: 0
- Accepted public-baseline reproduction: 0
- Accepted model/RSS/runtime/latency evidence bundle: 0
- New architecture or mechanism: none
- Capability progress: not established
- Intelligence principle: not established
- Failure classification until all contracts pass: `initial_reproduction_failure`
