# R0-D Cycle 021 — runtime/artifact cell binding audit

## Scope

This cycle advances reproducibility/statistics/leakage auditing only. It adds no
memory, replay, fast-weight, sleep, forgetting, architecture, or toy mechanism.
All work is accumulated on `research/intelligence-swarm-reconstruction-001`.

## Newly closed audit gap

The existing evaluation contract binds predictions to immutable dataset rows and
checks method coverage, paired cells, shuffle provenance, leakage, and statistics.
A remaining gap was that resource and reproduction metadata could still be
reported as aggregate values disconnected from the exact
`method × seed × domain × split × condition` evaluation cell.

That gap allowed, in principle:

- one aggregate RSS/runtime value copied to every method;
- a checkpoint changed between in-distribution and holdout conditions;
- methods in the same evaluation cell scored against different dataset files;
- prediction, model, data, or raw-log files changed after manifest creation;
- a method missing one canonical seed while aggregate seed counts still looked complete;
- truncated hashes or short commit identifiers.

## Added implementation

`audit_runtime_artifact_cells.py` now requires one manifest row for every evaluated
cell and verifies:

1. exact method set: correct, random, language-blind, state-only,
   target-label shuffle, outcome shuffle;
2. exact canonical seeds `1 / 7 / 19` for every method;
3. identical cell coverage across all methods;
4. full SHA-256 for predictions, data, raw logs, and checkpoints;
5. full 40-hex code commit;
6. file existence and checksum equality against the manifest;
7. checkpoint byte size equality;
8. positive peak RSS and CPU inference latency, finite non-negative training time;
9. one dataset hash shared by all methods in the same evaluation cell;
10. one code commit and one checkpoint per method/seed across conditions;
11. rejection of identical full resource/artifact tuples copied across methods.

Random has no checkpoint requirement but still requires immutable predictions,
data, raw logs, code provenance, RSS, runtime, and CPU latency.

Any failure is classified as:

`initial_reproduction_failure`

## Regression coverage added

`test_audit_runtime_artifact_cells.py` fixes four cases:

- a complete six-method, three-seed bundle passes;
- post-manifest prediction mutation fails by checksum;
- one missing state-only seed/cell fails;
- a checkpoint switch between conditions fails.

The tests are committed but no GitHub Actions completion is claimed in this cycle.
The real R0 bundle has not yet passed this audit.

## Current classification

- Real public-baseline bundle: **not audited by this new contract**
- Reproduction status: **`initial_reproduction_failure`**
- Public capability baseline: **not reproduced**
- Capability progress: **not recognized**
- Novel intelligence principle: **not claimed**
- High-school-level intelligence: **not reached**
