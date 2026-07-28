# E003 — D003 exact-runtime route after BLOCKED_ENV

Date: 2026-07-29
Canonical branch: `research/intelligence-swarm-reconstruction-001`
Candidate: Block Attention Residuals N=4 on the 115M Qwen3-style dense baseline

## Evidence consumed

- `STATE.md` and `BACKLOG.md` after D003 environment probe
- `evidence/A002_BLOCK_ATTNRES_EXACT_DEPENDENCY_LOWER_BOUND_AUDIT.md`
- `theory/B003_BLOCK_ATTNRES_D002_SCALING_BREAKPOINT_AUDIT.md`
- `prereg/C002_D003_EXACT_RUNTIME_PREFLIGHT_PREREG.md`
- `reproduction/D003_ENVIRONMENT_GATE_BLOCKER_ISOLATION.md`
- `benchmarks/k3_minimal/preflight/D003_environment_probe_summary.json`

## Integrated finding

The present sandbox is unsuitable for the preregistered D003 experiment because it exposes Python 3.13, lacks Transformers/tokenizers, and cannot resolve GitHub. This is an execution-environment failure, not evidence about Block AttnRes quality or the unofficial implementation path.

Waiting for the same sandbox to change would create a non-scientific scheduling bottleneck. The repository already uses GitHub as the canonical execution and evidence surface, so the smallest controlled continuation is a dedicated GitHub Actions CPU workflow that performs the exact dependency/import gate and, only after it passes, the preregistered fresh-process resource/operator preflight.

## Decision

- Classification: **追加検証**
- Implementation path: **Path-WARN / BLOCKED_ENV locally**
- Adoption: **未採用**
- P0 remains Block AttnRes. KDA, Stable LatentMoE, MXFP4 and other candidates remain frozen.
- The experiment target, model semantics, thresholds and candidate commit do not change.
- Only the execution substrate changes from the blocked sandbox to a reproducible GitHub Actions runner.

## Single next hypothesis

> A pinned GitHub Actions CPU job with Python 3.11 can resolve and lock the exact candidate-compatible dependency graph, pass every required internal-API import, and persist provenance artifacts; the same workflow can then run exact B0/A1 fresh-process AB/BA measurements without semantic changes.

## Single bottleneck

**D003-GHA: exact dependency/import gate on GitHub Actions.**

## Authorized work for the next cycle

### A

No new component audit. Check dependency provenance only if the Actions resolver or import probe exposes a concrete incompatibility.

### B

Do not revise the CPU crossover claim. Prepare interpretation only after exact workflow traces exist.

### C

Create one narrow amendment/manifest for the Actions execution substrate:

- Ubuntu runner image and image provenance
- Python 3.11 exact patch as observed by the runner
- exact PyTorch build
- Transformers commit `42791a34fdeae197f60f11ace3807c81f44b0729`
- resolver report, freeze and downloaded artifact hashes
- cache prohibition or cache-key provenance
- artifact retention paths
- explicit two-stage gate: environment PASS before model measurement

No threshold, architecture or candidate changes.

### D

Implement and run a manually dispatchable workflow. Stage 1 must:

1. checkout the canonical branch and record commit SHA;
2. install Python 3.11;
3. resolve the preregistered dependency snapshot without silent substitution;
4. save `pip --report`, `pip freeze`, downloaded wheel/source hashes and environment metadata;
5. run `d003_environment_probe.py`;
6. upload all logs and summaries even on failure.

Only after Stage 1 passes may Stage 2 run the existing C002 semantic gate and fresh-process AB/BA resource/operator protocol. Dataset, optimizer step and training remain prohibited.

## Completion conditions

D003-GHA environment stage completes only if:

- Python is 3.11.x;
- exact PyTorch build and Transformers commit are recorded;
- all required internal imports pass;
- candidate source and compatibility patch, if any, have checksums;
- resolver report, freeze, environment metadata, raw logs and artifact checksums are persisted;
- no semantic fallback or silent API substitution occurs.

## Stop conditions

The current unofficial implementation path becomes STOP only if, on the pinned Actions environment and after at most one preregistered import/API-wiring patch:

- the required dependency graph cannot be installed;
- required internal APIs cannot be made available without semantic change;
- B0/A1 cannot be instantiated as a residual-only diff;
- evidence artifacts cannot be persisted reproducibly.

A transient package-index, Actions-service or network failure is retried and is not scientific STOP evidence.

## Pareto status

- quality: unmeasured
- model bytes: standalone reconstruction only
- active compute: unmeasured
- isolated peak RSS: unmeasured
- training time: unmeasured
- CPU generation: unmeasured
- quantization: unmeasured
- 3-seed stability: unmeasured

No intelligence-principle, capability-progress, high-school-level or sub-1GB-goal claim is authorized.