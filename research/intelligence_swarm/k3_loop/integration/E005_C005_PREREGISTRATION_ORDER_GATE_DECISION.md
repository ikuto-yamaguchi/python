# E005 — C005 preregistration order gate

Date: 2026-07-29

D005 correctly returned `PREREG_BLOCKED`: C005 does not yet exist, so D must not modify or start the environment workflow. This is an experiment-order blocker, not evidence for or against Block AttnRes.

## Decision

- Block AttnRes: additional validation, not adopted, Path-WARN.
- Current execution state: `PREREG_BLOCKED`.
- Single bottleneck: create the C005 prose preregistration and machine-readable manifest.
- Repeating D before C005 exists is prohibited because it cannot add scientific evidence.

## Single next hypothesis

A branch- and path-restricted environment-only execution amendment can be fully preregistered without changing the model, candidate, dependency target, or scientific thresholds.

## C deliverables

Create:

- `research/intelligence_swarm/k3_loop/prereg/C005_D003_GHA_PUSH_ROUTE_AMENDMENT.md`
- `benchmarks/k3_minimal/manifests/C005_d003_gha_push_route.yaml`

The two files must fix the canonical branch restriction, environment-file path restriction, concurrency, false training/model authorization flags, provenance artifact schema, no automatic model-stage transition, one unchanged retry for transient service failure, and the `ENV_PASS` / `ENV_RETRY` / `ROUTE_STOP` / `ENV_PATH_STOP` classifications.

C005 must also carry forward the later PB1 trace contract: 1-based semantic sublayer indexing, `L_sub=24`, `N=4`, `S=6`, ordered boundaries `[3,6,9,12]`, rejection of odd or non-divisible `S`, source-slot bounds `84/5/89`, and `primary_evidence_geometry_matched=false`. These fields do not authorize model execution.

## Returns

- A: no new K3 component; investigate only a concrete resolver/import failure.
- B: no new CPU crossover or Pareto claim before exact traces.
- C: create C005 only.
- D: do not change the workflow until C005 exists; afterward apply only the registered amendment and collect environment provenance.
- E: classify only the execution/environment outcome after D returns.

## Completion

C005 is complete only when prose and manifest agree exactly and D can execute the amendment without inventing a field.

## Evidence boundary

Quality, model bytes, active compute, isolated RSS, training time, CPU generation, quantization tolerance, and three-seed stability remain unmeasured. No intelligence-principle, capability-progress, high-school-level, or 1GB-goal claim is supported.
