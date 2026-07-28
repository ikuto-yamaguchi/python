# B007 — Execution Substrate Invariance and Evidence Admissibility Audit

Date: 2026-07-29
Role: K3-B theory audit
Status: completed

## 1. Scope

This audit does not revise the Block AttnRes CPU crossover, minimum effective scale, or Pareto classification. Those remain blocked on exact runtime traces.

The audited question is narrower:

> Can a default-branch thin dispatcher execute an exact canonical-commit environment probe without becoming a model intervention or contaminating later B0/PB1/CR1 comparisons?

The current bottleneck is C006 preregistration of that dispatcher. The model target, candidate commit, Transformers commit, PB1 geometry, and all training/model authorizations remain unchanged.

## 2. Compared execution paths

### Path L — local/sandbox path

Observed properties:

- Python and dependency mismatch
- fixed Transformers snapshot unavailable
- no exact candidate import
- no admissible exact-runtime trace

Scientific status: environment blocker only. It provides no quality or resource evidence.

### Path C005 — canonical-branch push workflow

Observed properties:

- registered environment-only workflow was committed on the canonical branch
- ordinary push workflows ran
- the newly added environment workflow produced no run

Scientific status: `ROUTE_STOP`. It tests workflow discoverability, not Block AttnRes.

### Path C006 — proposed default-branch thin dispatcher

Permitted role:

- exist on the default branch only as a launcher
- accept immutable canonical branch/commit and manifest/script hashes
- detached-checkout the exact canonical commit
- run only the environment/import probe
- produce provenance artifacts

Prohibited role:

- contain or duplicate model code
- patch model semantics
- select a different candidate, baseline, dependency snapshot, or geometry
- authorize model execution, dataset/tokenizer/checkpoint retrieval, training, or quantization

## 3. Invariance conditions

Let an experimental result be represented as

\[
R = F(M, D, H, S, E, O),
\]

where:

- `M`: model code and parameterization
- `D`: data/input bytes
- `H`: hyperparameters and seeds
- `S`: software dependency state
- `E`: execution hardware/runtime state
- `O`: orchestration path

Changing the dispatcher changes `O`. It is scientifically separable from the model intervention only if the dispatcher proves that `M`, `D`, `H`, and `S` are immutable and records `E` rather than silently altering it.

For the environment-only stage, admissibility requires all of the following:

1. **Canonical-code identity**
   - detached checkout equals the preregistered canonical commit SHA
   - dirty tree is rejected
   - environment script and C003/C004/C006 manifests match required SHA values

2. **Dependency identity**
   - exact Python, PyTorch, Transformers commit, tokenizers, and transitive dependencies are recorded
   - resolver report, `pip freeze --all`, `pip check`, source/wheel hashes are retained
   - silent API substitution is forbidden

3. **Authorization isolation**
   - `model_execution_authorized=false`
   - `training_authorized=false`
   - dataset/tokenizer/checkpoint/quantization actions are absent and rejected

4. **Launcher thinness**
   - dispatcher contains no model implementation, model patch, architecture branch, or experiment-specific numerical threshold beyond route/provenance validation

5. **Artifact completeness**
   - raw logs, import matrix, runner provenance, artifact ID, and final archive SHA256 are retained

If any condition fails, the result is `ENV_PROTOCOL_FAIL` and is inadmissible even if imports appear successful.

## 4. Assumption comparison

### Standard Transformer / MoE / linear-attention baseline experiments

All architecture classes require environment provenance, but internal-library dependence differs:

- public-API Transformer baseline: lower sensitivity to a single library commit
- MoE baseline: higher sensitivity to distributed/runtime and expert-routing kernels
- linear-attention baseline: often sensitive to custom kernels and recurrence-state implementations
- current Block AttnRes candidate: unusually sensitive to internal Transformers APIs and therefore requires commit-level provenance

Thus the C006 route is not an advantage granted to Block AttnRes. It is a stricter reproducibility requirement caused by the candidate implementation's internal API dependency.

## 5. Resource and scaling implications

The dispatcher itself has no admissible contribution to:

- model parameter count
- active parameter count
- FLOPs/token
- KV/state memory
- training memory
- communication cost
- sequence-length dependence
- quantization behavior
- CPU inference suitability

Those quantities must be measured only after a separately authorized exact model stage.

Runner CPU model, ISA, kernel versions, thread settings, and memory capacity may alter wall time and RSS. Therefore environment-stage success cannot be promoted to a resource comparison. Later B0/PB1/CR1 measurements must use the same recorded execution substrate or explicitly normalize/repeat across substrates.

## 6. Counterexample / failure condition

A dispatcher can appear thin while cloning the canonical commit and then installing an unpinned released Transformers package that merely exposes similarly named APIs.

Imports may pass, but `S` has changed. Subsequent routing behavior, mask construction, cache semantics, serialization, or operator selection may differ. Any resulting B0/PB1 comparison would not be an exact reproduction, even if parameter counts match.

This counterexample establishes:

> successful import is necessary but not sufficient; commit- and artifact-level dependency identity is required.

A second failure mode is checking out the requested SHA and then applying a compatibility patch not represented by a preregistered patch hash. That changes `M` or `S` after the identity gate and invalidates the result.

## 7. Handoffs

### To C

C006 must preregister:

- immutable inputs: canonical branch/SHA, C003/C004/C006 manifest SHA, environment script SHA
- detached checkout and dirty-tree rejection
- exact dependency provenance and hashes
- launcher allowlist proving no model-code duplication
- all model/data/training/quantization authorizations false
- no automatic transition after `ENV_PASS`
- result classification: `ENV_PASS`, `ENV_RETRY`, `ROUTE_STOP_DEFAULT_BRANCH`, `ENV_PATH_STOP`, `ENV_PROTOCOL_FAIL`

### To D

D must measure and store only environment/provenance facts in this stage. It must not instantiate B0, PB1, or CR1.

Required checks include:

- requested SHA equals checked-out SHA
- required file blob hashes match
- working tree clean
- exact dependency/import matrix
- raw logs and archive checksum

### To E

Adoption status must not change on any route/environment outcome.

- `ENV_PASS`: permits consideration of a separately preregistered semantic trace; no quality/resource inference
- `ENV_RETRY`: no scientific inference
- `ROUTE_STOP_DEFAULT_BRANCH`: stops the current orchestration path only
- `ENV_PATH_STOP`: stops the current third-party implementation path only
- `ENV_PROTOCOL_FAIL`: invalid run; no evidence

## 8. Decision

The default-branch thin-dispatcher approach is theoretically admissible **only under the invariance conditions above**. It is an orchestration substitution, not an architecture substitution.

Current Block AttnRes classification remains:

> **小型化で要再設計・追加検証・未採用 / Path-WARN**

No CPU crossover, minimum scale, quality improvement, quantization tolerance, three-seed stability, intelligence principle, or 1GB-goal progress is established by this audit.
