# D004 — D003-GHA workflow staging and dispatch blocker

Date: 2026-07-29
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

C003で許可されたenvironment/import stageだけをGitHub Actionsへ実装した。model execution、dataset、optimizer、training、benchmark、quantizationは追加していない。

## Added executable artifacts

- `.github/workflows/d003-k3-environment-gate.yml`
- `benchmarks/k3_minimal/preflight/d003_gha_environment.sh`

Fixed inputs:

- Python `3.11.x`
- PyTorch `2.7.1`（resolver reportで実体を保存）
- Transformers `42791a34fdeae197f60f11ace3807c81f44b0729`
- candidate `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`

The script records resolver report, full freeze, pip check, candidate commit, D003 internal-import probe, candidate module import log, summary and SHA256 checksums. It writes `training_authorized=false`, `model_execution_authorized=false`, and does not chain to C004 automatically.

## Static contract result

PASS:

- workflow is manual-dispatch only
- canonical branch is explicitly checked out
- Python 3.11 is fixed
- cache is not enabled by setup-python
- environment evidence is uploaded even on failure
- model/data/training steps are absent
- C004 is not automatically invoked

## Execution result

Status: `STAGED_NOT_DISPATCHED`

No workflow run exists for commit `3c19c0e7d6f5511322f6777504c8536cb44d99f2` at inspection time.

The available GitHub connector can create repository files and inspect/retry existing workflow runs, but it cannot start a new `workflow_dispatch` run. In addition, GitHub normally requires a manually dispatched workflow to be registered on the repository default branch; this workflow intentionally remains on the canonical reconstruction branch because the research contract forbids moving work to another branch.

This is an orchestration blocker, not evidence against Block AttnRes, PB1, CR1, or the dependency graph.

## Decision

- Block AttnRes: unchanged, **小型化で要再設計・追加検証・未採用 / Path-WARN**
- D003-GHA environment gate: executable definition completed, runtime evidence pending
- scientific classification: no change
- S1–S3, dataset, model stage, timing, quantization: still unauthorized

## Next minimal action

Run `.github/workflows/d003-k3-environment-gate.yml` against `research/intelligence-swarm-reconstruction-001` through a GitHub Actions dispatcher that can start `workflow_dispatch`, then preserve the environment artifact ID and artifact SHA. If GitHub refuses dispatch because the workflow is not present on `main`, do not silently add a push/PR trigger or copy the workflow to `main`; return to C/E for an explicit execution-route amendment.
