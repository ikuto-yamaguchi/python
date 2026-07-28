# B008 — Portable Substrate Equivalence and Trust-Closure Audit

Date: 2026-07-29
Role: K3-B theory audit
Status: completed

## 1. Scope

This audit addresses the sole open B-side item after E007:

> Under what conditions can a non-GitHub-Actions portable environment-only run provide evidence equivalent to the B007 execution-substrate contract without changing the Block AttnRes model hypothesis?

This is not a CPU crossover, quality, minimum-scale, quantization, or Pareto audit. No model execution is authorized. The current model target, candidate commit, Transformers commit, PB1 geometry, and all model/data/training authorizations remain unchanged.

## 2. Compared substrates

### G — GitHub Actions environment route

Intended properties before closure:

- immutable canonical commit input
- clean detached checkout
- fixed dependency graph
- raw logs and archive checksum
- platform-controlled runner provenance

Observed result: both GitHub Actions routes were closed before admissible environment evidence was produced.

### P — portable external environment route

A portable route may be a local machine, container host, VM, CI provider, or manually invoked Linux CPU system. Unlike GitHub Actions, it does not inherit a trusted checkout, runner image, artifact service, or workflow event record. Therefore it is admissible only if the bundle itself closes those missing trust links.

## 3. Evidence-equivalence model

Let environment evidence be represented by

\[
E_{env}=G(I_c,I_f,S_r,A_z,P_h,R_l),
\]

where:

- `I_c`: canonical commit identity and reachability
- `I_f`: required file/blob identity
- `S_r`: resolved software state
- `A_z`: authorization state, all model-stage permissions false
- `P_h`: platform/hardware/runtime provenance
- `R_l`: replayable logs and artifact closure

A portable result is equivalent to the B007 contract only if each component is independently verifiable from the archived evidence. Merely running the same shell commands is not equivalence.

## 4. Trust-closure requirements

### 4.1 Canonical source closure

The bundle must record and verify before dependency installation:

1. requested canonical branch name
2. requested full 40-character canonical commit SHA
3. repository remote URL
4. proof that the commit is reachable from the canonical branch at acquisition time, or an explicitly archived repository bundle containing the commit and branch ref
5. checked-out commit SHA equals the requested SHA
6. detached HEAD or exact-content extraction with no branch-tip execution
7. clean working tree, including untracked-file rejection
8. no submodule or Git LFS pointer left unresolved unless separately hashed and preregistered

A source archive copied from an unknown workspace is insufficient even when its top-level files match, because omitted generated files, submodules, hooks, or local patches may alter execution.

### 4.2 Required-file closure

At minimum, C003, C004, C007, the environment runner, and the environment probe must each be bound by:

- Git blob SHA when obtained from a Git object database
- SHA256 of the exact bytes executed or parsed
- repository-relative path
- file size

C006 may be retained as historical provenance, but C007 must explicitly declare whether its identity is normative or only inherited context. No launcher may silently substitute C006 rules for C007 rules.

### 4.3 Software-state closure

The portable substrate must preserve:

- Python executable absolute path and full version
- interpreter build metadata
- exact PyTorch build and wheel/source hash
- exact Transformers commit `42791a34fdeae197f60f11ace3807c81f44b0729`
- exact tokenizers and all transitive package versions
- installer version and resolver command
- resolver report
- `pip freeze --all`
- `pip check`
- hashes for every downloaded wheel, sdist, Git archive, or locally provided package
- package-index URL or offline artifact origin

Installing from an editable working tree is prohibited unless the source tree itself is archived, clean, commit-bound, and included in the checksum closure.

### 4.4 Authorization closure

The portable launcher must make the following machine-readable and false:

- `model_execution_authorized`
- `semantic_trace_authorized`
- `training_authorized`
- `dataset_download_authorized`
- `tokenizer_download_authorized`
- `checkpoint_download_authorized`
- `quantization_authorized`
- `automatic_next_stage`

The launcher must also fail closed if any prohibited command, model import side effect, or automatic continuation is detected. Environment import probes may import modules but must not instantiate B0, PB1, or CR1.

### 4.5 Platform provenance closure

The archive must record enough of the execution substrate to distinguish software-compatibility evidence from later resource evidence:

- OS release and kernel
- architecture and endianness
- CPU model, visible logical CPUs, ISA flags
- total RAM and cgroup/container limits
- virtualization/container indicators
- libc version
- thread-related environment variables
- locale and timezone
- network availability mode

These values do not make environment success into a CPU benchmark. They prevent a later model run from being falsely treated as substrate-identical.

### 4.6 Artifact closure

The run must create a deterministic directory layout containing:

- command transcript
- stdout/stderr raw logs
- preflight identity report
- resolver report
- freeze and package check
- import matrix
- dependency/source checksum table
- authorization report
- platform provenance
- classification JSON
- replay command

The directory must contain `checksums.sha256` covering every evidence file except the outer archive. The final archive must then receive a separately recorded SHA256 and byte size. A checksum file stored outside the archive without a binding record is insufficient.

## 5. Portable-route overhead and model metrics

The portable launcher contributes zero admissible change to:

- parameter count
- active parameter count
- FLOPs/token
- KV/state memory
- training memory
- communication cost
- sequence-length dependence
- quantization behavior

It may alter wall-clock time, RSS, allocator behavior, or operator selection through the hardware/runtime substrate. Therefore D008 environment success cannot be used as resource evidence, and any later B0/PB1/CR1 comparison must either:

1. execute all variants on the identical recorded substrate, or
2. repeat the baseline on every substrate and prohibit cross-substrate deltas.

## 6. Equivalence decision table

| Condition | Portable result status | Scientific meaning |
|---|---|---|
| Full identity, dependency, authorization, provenance and artifact closure | `ENV_PASS` | exact candidate environment may proceed to a separately preregistered semantic trace |
| Run starts, then a clearly transient network/package service failure occurs | `ENV_RETRY` | no model evidence; one unchanged retry allowed |
| No available host satisfies Python/source/dependency/artifact requirements | `SUBSTRATE_STOP` | portable execution route unavailable; no mechanism inference |
| Fixed non-transient dependency/import mismatch with valid provenance | `ENV_PATH_STOP_PENDING_AMENDMENT` | one API-wiring-only amendment may be preregistered |
| Preregistered API-wiring-only patch still requires semantic change | `ENV_PATH_STOP` | current third-party candidate path stops |
| Any identity, clean-tree, authorization, checksum or archive omission | `ENV_PROTOCOL_FAIL` | run invalid even when imports pass |

## 7. Counterexamples and failure conditions

### Counterexample 1 — byte-identical scripts, non-identical dependency closure

Two hosts execute the same runner and probe. Host A installs the fixed Transformers commit from a hashed archive. Host B installs a locally cached editable checkout with the same reported commit but an untracked modification.

Both may report the same package version and pass imports. Host B is not equivalent because `S_r` is not closed. Its result is `ENV_PROTOCOL_FAIL`, not `ENV_PASS`.

### Counterexample 2 — complete inner checksums, unbound outer archive

A run creates correct raw logs and `checksums.sha256`, but the archive is later rebuilt after one file is replaced. Without an outer archive hash and byte size recorded outside the archive, the delivered artifact is not bound to the checked evidence set.

Imports may be genuine, but evidence transport is not closed. The result is inadmissible.

### Counterexample 3 — clean Git tree with generated import shadowing

The repository is clean, but `PYTHONPATH` contains an external directory with a module named like a required Transformers internal module. Imports pass against the shadow module rather than the fixed dependency.

Therefore C007/D008 must record `sys.path`, imported module file paths, and source hashes for required symbols. Package version and clean Git status alone are insufficient.

## 8. Minimum C007 specification handed to C

C007 must preregister:

1. one portable environment-only command with no GitHub Actions dependency
2. canonical commit plus normative file/blob/SHA256 identities
3. acquisition mode: online Git fetch or offline Git bundle/archive, with equivalent reachability and content checks
4. Python 3.11 exact-patch selection rule
5. exact PyTorch build selection and artifact hash rule
6. fixed Transformers commit and dependency-resolution rule
7. `sys.path`, module-origin and imported-source hash capture
8. all model-stage authorizations false and fail-closed behavior
9. evidence directory schema, inner checksum closure, outer archive SHA256 and size
10. unchanged one-retry boundary
11. the six result classes in Section 6
12. no automatic semantic/model continuation after `ENV_PASS`

## 9. Measurements handed to D

D008 must measure only environment/provenance facts:

- requested and actual commit/ref identities
- clean/exact-content status
- normative file blob SHA, SHA256 and size
- Python/PyTorch/Transformers/tokenizers and transitive dependency identities
- `sys.path` and required imported-module origin paths
- resolver/freeze/check results
- authorization flags
- platform provenance
- raw command exit codes and logs
- inner evidence checksums
- outer archive SHA256 and byte size

D008 must not report model bytes, parameters, FLOPs, RSS deltas, CPU inference latency, routing behavior, quality, quantization, or seeds as measured evidence because no model execution is authorized.

## 10. Adoption criteria handed to E

- `ENV_PASS` does not improve the Block AttnRes classification; it only unlocks consideration of a separately preregistered semantic trace.
- `SUBSTRATE_STOP` closes the available portable route, not the mechanism.
- `ENV_PATH_STOP` closes the fixed third-party candidate path, not paper Block AttnRes as a whole.
- `ENV_PROTOCOL_FAIL` contributes no evidence and must not be reframed as an implementation or mechanism failure.
- No adoption, narrowing, or rejection may be based on environment-only results.

## 11. Decision

A portable substrate is theoretically equivalent to the B007 environment-evidence contract only when it supplies a complete, independently verifiable trust closure across canonical source, required files, dependencies, authorizations, platform provenance, imported module origins, and archived evidence.

The key new condition beyond B007 is:

> portability removes the platform-provided chain of custody, so C007/D008 must create that chain explicitly, including module-origin verification and both inner-evidence and outer-archive checksum closure.

Current classification remains:

> **Block AttnRes: 小型化で要再設計・追加検証・未採用 / Path-WARN**

No CPU crossover, minimum effective scale, quality improvement, quantization tolerance, three-seed stability, intelligence principle, or 1GB-goal progress is established.