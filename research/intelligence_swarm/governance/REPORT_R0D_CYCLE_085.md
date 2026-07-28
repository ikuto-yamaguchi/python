# R0-D Cycle 085 — strict resource and seed identity

## Scope

This cycle remains limited to R0 benchmark reproducibility, statistics, leakage, and artifact auditing. It does not add memory, replay, fast weights, sleep, or forgetting mechanisms.

## Defect

The dataset scorer already required `type(seed) is int`, but artifact manifests still used `int(run["seed"])`, and raw-log binding used `int(expected)` / `int(observed)`. Consequently `true`, `1.0`, `"1"`, and related aliases could be accepted as canonical seed 1 in resource evidence.

`model_bytes` and `peak_rss_bytes` were also accepted through a generic finite-positive numeric predicate and compared after float conversion. Byte counts are discrete measurements and must not accept floats, booleans, or strings.

## Fail-closed change

- Artifact manifest seed uses `strict_seed`.
- Raw-log manifest/record seed binding uses `strict_seed` on both values.
- `model_bytes` and `peak_rss_bytes` must satisfy `type(value) is int and value > 0` in both manifest and raw log.
- Training wall time and CPU inference latency remain finite positive numeric measurements.
- Audit output records `strict_resource_integer_identity_required=true` and the integer-only fields.

Any violation is classified as `initial_reproduction_failure`.

## Evidence state

No public baseline or real R0 artifact bundle is accepted by this cycle. Until the focused workflow applies the patch and passes regression, core integration remains unverified.
