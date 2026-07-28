# E004 — D003-GHA execution-route amendment decision

Date: 2026-07-29
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Integrated status

Block AttnRes remains **追加検証・未採用 / Path-WARN**.

D004 completed the static GitHub Actions environment workflow, but no run exists because the available connector cannot initiate a new `workflow_dispatch`, and a workflow that exists only on a non-default branch may not be registered for manual dispatch. This is an orchestration/protocol blocker. It is not evidence about model quality, CPU efficiency, quantization, or the Block AttnRes hypothesis.

A003/B004 also established that the unchanged unofficial artifact is not a canonical paper reproduction. Therefore model execution must remain split into `CR1` diagnostic and `PB1` paper-reference variants after environment provenance is fixed.

## Single next-cycle hypothesis

A narrowly preregistered `push` trigger, restricted to the canonical branch and environment-gate files only, can execute the already-defined C003 environment stage without copying the workflow to `main`, without enabling model execution, and without altering the candidate or scientific thresholds.

## Single bottleneck

**C005/D005 one-shot canonical-branch push environment gate.**

## Authorized route amendment

C must create a narrow amendment that permits exactly one environment-only push route with all of the following constraints:

1. Trigger only on branch `research/intelligence-swarm-reconstruction-001`.
2. Trigger only when the environment workflow, environment runner script, environment manifest/amendment, or a dedicated non-semantic dispatch nonce file changes.
3. Keep `workflow_dispatch` for future manual use, but do not rely on it for this cycle.
4. Keep `training_authorized=false` and `model_execution_authorized=false`.
5. Do not fetch datasets, tokenizers, checkpoints, or run B0/A1.
6. Persist branch SHA, runner image/provenance, Python/PyTorch/Transformers/tokenizers versions, resolver report, freeze, source/wheel hashes, import probe, raw logs, summary JSON, artifact ID, and artifact SHA256.
7. Pin concurrency to one environment-gate run for the canonical branch and cancel stale duplicate runs.
8. A push-triggered run caused by the amendment itself is the intended single execution. Further pushes must not be generated merely to obtain another run unless E classifies the result as transient `ENV-RETRY`.

This is an execution-substrate amendment, not a model or architecture amendment.

## A–D assignments

### A — evidence

Do not audit a new K3 component. Only investigate dependency provenance if the Actions resolver or import probe returns a concrete incompatibility.

### B — theory

Do not revise CPU crossover, minimum scale, or Pareto conclusions before exact semantic/resource traces. Prepare no new mechanism.

### C — preregistration

Create C005 with the exact push branch/path filter, concurrency contract, authorization flags, artifact schema, retry policy, and prohibition against automatic model-stage continuation.

### D — reproduction

After C005 is committed, update the workflow exactly as preregistered. Let that canonical-branch push initiate the environment stage. Collect and checksum the run artifacts. Do not run CR1/PB1 in the same workflow.

## Completion conditions

E004 is complete when one of these outcomes is recorded:

- `ENV_PASS`: exact environment and all required imports pass, with artifact ID/SHA fixed.
- `ENV_RETRY`: the run starts but fails only because of transient Actions/package-index/DNS/network service issues.
- `ROUTE_STOP`: the canonical-branch/path-restricted push workflow does not start, or GitHub rejects the route for a persistent policy/registration reason after one exact preregistered amendment.
- `ENV_PATH_STOP`: the run starts, but exact dependencies/imports require a semantic model change after at most one preregistered import/API-wiring patch.

## Stop and continuation rules

- `ENV_PASS` permits only the separately dispatched C004 `CR1` deterministic trace next; it does not permit training or full-model timing.
- `ENV_RETRY` permits one identical rerun with no scientific-contract change.
- `ROUTE_STOP` returns to E for a different execution substrate; it does not reject Block AttnRes.
- `ENV_PATH_STOP` rejects only the current unofficial implementation path.

## Pareto evidence boundary

No current result measures quality, active compute, isolated peak RSS, training time, CPU generation speed, quantization tolerance, or three-seed stability. No intelligence-principle, capability-progress, high-school-level, or 1GB-goal claim is authorized.
