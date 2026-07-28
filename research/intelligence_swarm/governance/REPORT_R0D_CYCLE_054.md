# R0-D Cycle 054 — Public baseline reproduction provenance

## Scope

This cycle continues R0 benchmark reproducibility, statistics, leakage, and
evidence auditing only. It introduces no memory, replay, fast weights, sleep,
forgetting, model, or learning mechanism.

## Defect found

The existing bundle gate checks dataset/prediction leakage, same-instance
statistics, model/data/log artifacts, measured resources, checksums, path
containment, cell binding, and deterministic statistics recomputation. It did
not require a claim of reproducing a public baseline to identify an immutable
upstream revision or bind the published expected values and locally observed
values to the submitted statistics artifact.

Consequently, a manifest could describe a result as a public-baseline
reproduction without preserving all of the following:

- the official source URL;
- a full upstream commit SHA and release/version description;
- the exact expected metrics from the public source;
- the exact observed metrics from this run;
- preregistered absolute tolerances;
- a binding from the observed values to `manifest.statistics_sha256`.

Checksums alone cannot establish that a claimed public reference value came
from a particular immutable upstream implementation or that the local values
meet an explicit reproduction tolerance.

## Fail-closed contract added

`audit_public_baseline_reproduction.py` now requires
`manifest.public_baseline` to contain:

- `name`;
- an HTTPS `source_url`;
- a full 40-hex `source_commit`;
- a non-empty immutable `source_version` description;
- non-empty `expected_values`;
- matching-key `observed_values`;
- matching-key non-negative `absolute_tolerances`;
- `statistics_sha256` equal to the manifest statistics checksum.

Each expected, observed, and tolerance value must be finite numeric. Every
metric is checked independently, and any absolute deviation above its declared
tolerance rejects the bundle.

The unified `audit_r0_acceptance_bundle.py` gate now invokes this contract in
the same acceptance call as all existing dataset, leakage, prediction,
statistics, resource, path, and checksum contracts.

## Regression coverage

`test_audit_public_baseline_reproduction.py` covers:

1. complete immutable and checksummed reproduction evidence;
2. missing baseline metadata;
3. branch/tag text used instead of a full upstream commit SHA;
4. statistics checksum mismatch;
5. expected/observed metric topology mismatch;
6. observed values outside preregistered tolerance;
7. non-finite metric values.

## Classification

A missing, mutable, unbound, incomplete, non-finite, or out-of-tolerance public
baseline claim is classified as:

`initial_reproduction_failure`

No real R0 evidence bundle or public baseline reproduction is accepted merely
because this contract exists. Acceptance still requires a concrete bundle to
pass every unified contract.
