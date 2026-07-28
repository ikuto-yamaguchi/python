# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-29 by K3-E
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3由来の効率化原理を、1GB以下・弱いCPU/スマホ向けモデルへ転用できるか、公開baseline、単一変更ablation、3 seed、資源計測で判定する。

## Current phase

**Phase 1.6: C005 canonical-branch route is closed as `ROUTE_STOP`; C006 must preregister a default-branch thin dispatcher before any further execution.**

Completed: A001–A004, B001–B006, C001–C005, D001–D006, E001–E006.

Current classifications:

- Block AttnRes: **小型化で要再設計・追加検証・未採用 / Path-WARN**
- PAPER-BLOCK (`PB1`): canonical paper-reference candidate; semantic trace pending
- CANDIDATE-RAW (`CR1`): fixed-commit artifact diagnostic only; paper attribution prohibited
- C005 route: **`ROUTE_STOP / closed`**
- Execution state: **`C006_PREREG_REQUIRED`**

Frozen until P0 completes: new architecture, dataset download, optimizer step, S1–S3, quantization, KDA, Stable LatentMoE.

## Fixed references

- candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- official: `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6`
- Transformers commit: `42791a34fdeae197f60f11ace3807c81f44b0729`
- official executable training baseline: not released

## Candidate separation

- `PB1 / PAPER-BLOCK`: boundary append後にpartial reset、unintended duplicate禁止、recency bias/gate禁止
- `CR1 / CANDIDATE-RAW`: 公開commitを変更せず診断し、paper mechanismへ帰属しない

Parameter contract:

- B0: `115,554,304`
- CR1 provisional/executable prior: `115,579,929`, delta `25,625`
- PB1 provisional: `115,579,904`, delta `25,600`
- PB1 relative overhead: approximately `0.02215%`

Exact executable state dictで再確認する。parameter数やKV cache非増加だけでCPU軽量性を主張しない。

## PB1 semantic geometry

- `L_transformer = 12`
- `L_sub = 24`
- `N = 4`
- `S = 6` Attention/MLP sublayers per completed block
- ordered boundaries after Transformer blocks `[3, 6, 9, 12]`
- semantic sublayer index is 1-based
- embedding is one separate source
- final router does not increment completed-block count
- odd `S` or non-divisible `L_sub/S` must be rejected

Canonical source-slot contract:

- sublayer routing slots: `84`
- final-router sources: `5`
- total slots: `89`
- `primary_evidence_geometry_matched=false`

PB1 is a minimum semantic/effect-direction pilot, not a reproduction of the primary `N≈8–9` evidence geometry.

## PB1 interpretation boundary

- PB1 null is not mechanism-wide falsification without resolution, optimization, scale, and implementation invariance.
- PB1 positive is not sufficient for adoption.
- healthy-routing null defaults to `PB1 inconclusive / possible depth-resolution limit`.
- higher-`N` escalation requires a separate preregistration and resource budget.
- source-slot lower bounds: `N=8,S=4,L=32 -> 185` (`2.079x PB1`); `N=9,S=6,L=54 -> 334` (`3.753x PB1`).

Record: `research/intelligence_swarm/k3_loop/theory/B006_PB1_FALSIFIABILITY_AND_ESCALATION_BOUNDARY.md`

## Existing executable evidence

D002 standalone reconstruction passed instantiate, forward/backward, routing-gradient and save/load gates, but it was not the exact candidate Transformers runtime.

Standalone routing medians:

- T=1: `0.112487 ms`
- T=128: `0.627961 ms`
- T=512: `2.252197 ms`
- T=2048: `35.944465 ms`

The 2048-token result was about 4.13x the short-sequence fit and remains unconfirmed in the exact runtime.

## Execution-route history

- D003 local exact-runtime attempt: `BLOCKED_ENV`
- D004 GitHub Actions environment workflow: staged, manual dispatch not started
- E004: authorized a narrow one-shot canonical-branch environment-only route, subject to C005 preregistration
- D005: confirmed C005 prose/manifest were absent and correctly returned `PREREG_BLOCKED`; workflow was not changed
- E005: made C005 the sole next step and prohibited repeated D predispatch churn
- C005: preregistered the canonical-branch/path-restricted one-shot push route
- D006: applied the registered workflow amendment and nonce attempt 1; existing push workflows ran, but no `D003 K3 environment gate` run was generated for either the amendment or nonce-finalization commit
- D006 classification: **`ROUTE_STOP`**. C005 route is closed; no further nonce/path-filter variants are allowed.
- E006: authorized only a separately preregistered default-branch thin dispatcher that accepts fixed canonical SHA inputs and runs the environment probe without model execution.

D006 records:

- `research/intelligence_swarm/k3_loop/reproduction/D006_C005_CANONICAL_PUSH_ROUTE_STOP.md`
- `benchmarks/k3_minimal/preflight/D006_c005_push_route_result.json`

E006 record:

- `research/intelligence_swarm/k3_loop/integration/E006_DEFAULT_BRANCH_THIN_DISPATCHER_DECISION.md`

## Single bottleneck

C must create C006 prose and manifest for a default-branch thin `workflow_dispatch` dispatcher.

Until C006 exists and is internally consistent, D must not:

1. modify the default branch
2. add or dispatch another workflow
3. dispatch a model stage
4. download dataset/tokenizer/checkpoint
5. train or quantize

## Authorized next work

- A: no new K3 component; inspect only a concrete resolver/import failure
- B: no crossover, minimum-scale, or Pareto revision before exact traces
- C: create C006 default-branch thin-dispatcher prose and manifest only
- D: wait for C006; afterward implement only the registered dispatcher and environment-only run
- E: classify C006/D007 route and environment outcome

## C006 required contract

- dispatcher file exists on default branch only as a thin launcher
- required inputs include canonical branch, canonical commit SHA, C003/C004/C006 manifest SHA, and environment script SHA
- detached checkout of the exact canonical SHA
- no model code duplication in the dispatcher
- `training_authorized=false`
- `model_execution_authorized=false`
- dataset/tokenizer/checkpoint/quantization prohibited
- environment PASS cannot auto-transition to model execution
- SHA, branch, dirty-tree, and allowlist guards are mandatory
- resolver report, freeze, hashes, raw logs, artifact ID and ZIP SHA256 are mandatory
- transient retry is limited to one unchanged attempt

## Completion / stop classification

- `ENV_PASS`: registered run, guards, exact provenance/imports, required artifacts, artifact ID/SHA all fixed
- `ENV_RETRY`: run-started transient Actions/package-index/DNS/network failure; one unchanged retry only
- `ROUTE_STOP_DEFAULT_BRANCH`: minimal default-branch dispatcher cannot be introduced or dispatched under repository policy/permissions
- `ENV_PATH_STOP`: after at most one preregistered API-wiring-only patch, fixed dependencies/imports still require semantic change or provenance cannot be saved
- `ENV_PROTOCOL_FAIL`: branch/SHA/allowlist/authorization/hash/artifact/prohibited-action violation; result invalid and no retry without amendment

None of these route/environment outcomes alone rejects Block AttnRes. `ROUTE_STOP_DEFAULT_BRANCH` pauses the current GitHub Actions implementation path until another explicit execution substrate becomes available.

## Evidence boundary

Quality, exact model bytes, active compute, isolated peak RSS, training time, CPU generation, quantization tolerance, and three-seed stability remain unmeasured. No new intelligence principle, capability progress, high-school-level capability, or 1GB-goal achievement is supported.
