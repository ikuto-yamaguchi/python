# E007 — D007 protocol failure and default-branch route closure

Date: 2026-07-29
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Evidence consumed

- `research/intelligence_swarm/k3_loop/STATE.md`
- `research/intelligence_swarm/k3_loop/BACKLOG.md`
- `research/intelligence_swarm/k3_loop/reproduction/D007_DEFAULT_BRANCH_DISPATCHER_PROTOCOL_BLOCKER.md`
- `benchmarks/k3_minimal/preflight/D007_default_branch_dispatcher_result.json`
- `research/intelligence_swarm/k3_loop/theory/B007_EXECUTION_SUBSTRATE_INVARIANCE_AND_EVIDENCE_ADMISSIBILITY.md`
- `research/intelligence_swarm/k3_loop/prereg/C006_DEFAULT_BRANCH_THIN_DISPATCHER_AMENDMENT.md`
- `benchmarks/k3_minimal/manifests/C006_default_branch_thin_dispatcher.yaml`
- default-branch file `.github/workflows/d007-k3-environment-dispatcher.yml`

## Integrated finding

D007 did not produce admissible environment or model evidence. A minimal workflow was committed to `main`, but it does not satisfy C006. It accepts only the canonical commit SHA and lacks the registered C003/C004/C006/script/probe blob-SHA inputs, branch-reachability proof, detached/clean-tree verification, allowlist and authorization gates, complete raw evidence, and archive checksum contract.

The incomplete workflow was not dispatched. This was correct. Dispatching it would be an `ENV_PROTOCOL_FAIL` regardless of whether imports happened to succeed.

The available write interface then rejected both the compliant replacement and cleanup deletion. Therefore the current default-branch GitHub Actions route is no longer an executable scientific path.

## Classification

- Candidate classification: **追加検証・未採用 / Path-WARN**
- D007 run classification: **`ENV_PROTOCOL_FAIL`**
- GitHub Actions route classification: **`ROUTE_STOP_DEFAULT_BRANCH`**
- Closed scope: C005 canonical-push route and C006/D007 default-branch dispatcher route
- Not rejected: Block AttnRes mechanism, PB1, CR1, or dependency compatibility

The incomplete workflow on `main` is quarantined: it must not be dispatched. Its existence is repository hygiene debt, not an authorized experiment.

## Pareto status

No Pareto axis is updated:

- quality: unmeasured
- exact model bytes: unmeasured; only provisional parameter arithmetic exists
- active compute: unmeasured
- isolated peak RSS/VRAM: unmeasured
- training time/tokens per second: unmeasured
- CPU prefill/decode/generation: unmeasured
- quantization tolerance: unmeasured
- three-seed stability: unmeasured

No intelligence-principle, capability-progress, high-school-level, or sub-1GB achievement claim is supported.

## Next-cycle single hypothesis

> A self-contained, non-GitHub-Actions execution bundle can verify the exact fixed dependency/import contract on an external or local Python 3.11 CPU environment without changing model semantics, while producing the same immutable provenance and artifact schema required by C006.

This is an execution-substrate hypothesis only. It does not authorize model construction, semantic tracing, training, dataset/tokenizer/checkpoint download, or quantization.

## Single bottleneck

**C007 portable offline/externally executed environment-gate preregistration.**

C must define one portable bundle and invocation contract that can be run on a user-controlled/local/other available Python 3.11 CPU environment. It must not depend on GitHub Actions registration or default-branch workflow mutation.

## A–D assignments

### A

Do not inspect a new K3 component. Provide additional dependency provenance only if C007/D008 produces a concrete resolver or import mismatch.

### B

Specify evidence-admissibility equivalence between the portable substrate and B007: canonical code identity, dependency identity, authorization isolation, launcher thinness, hardware/runtime provenance, and artifact completeness. Do not update CPU crossover or minimum useful scale.

### C

Create C007 prose and a machine-readable manifest for a portable environment-only bundle. Register:

1. immutable canonical commit and five blob identities;
2. exact Python/PyTorch/Transformers dependency contract;
3. detached or exact-content verification and clean-tree requirement;
4. all model/training/data/tokenizer/checkpoint/quantization/semantic-trace authorization set false;
5. resolver report, freeze, checksums, import matrix, raw logs, machine-readable classification and archive checksum;
6. one unchanged retry only for a run-started transient network/package-index failure;
7. no automatic transition to model execution.

### D

Do not touch or dispatch the incomplete default-branch workflow. After C007 only, assemble the registered portable bundle and execute one environment-only attempt on an available compliant substrate. If no compliant substrate is available, record a concrete `SUBSTRATE_STOP` with the required runtime and exact replay command rather than repeating route audits.

## Completion conditions

The next cycle is complete only when all are true:

- C007 prose and manifest agree;
- portable bundle contains no model implementation or model-stage authorization;
- immutable canonical and contract-file identities are checked;
- exact dependency/import results and raw provenance are archived;
- artifact checksum is recorded;
- result is classified once as `ENV_PASS`, `ENV_RETRY`, `ENV_PATH_STOP_PENDING_AMENDMENT`, `ENV_PROTOCOL_FAIL`, or `SUBSTRATE_STOP`.

## Stop conditions

- `SUBSTRATE_STOP`: no available execution substrate can provide Python 3.11, dependency installation/source access, and artifact persistence under the registered contract.
- `ENV_PROTOCOL_FAIL`: identity, authorization, clean-tree, checksum, or artifact contract violation.
- `ENV_PATH_STOP_PENDING_AMENDMENT`: valid substrate and provenance, but a fixed non-transient dependency/import mismatch occurs before a patch is preregistered.
- `ENV_PATH_STOP`: after one separately preregistered API-wiring-only patch, semantic modification or incomplete provenance is still required.

No further C005/C006 trigger, nonce, dispatcher, or default-branch workflow variants are permitted.