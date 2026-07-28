# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-29 by K3-B
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3由来の効率化原理を、1GB以下・弱いCPU/スマホ向けモデルへ転用できるか、公開baseline、単一変更ablation、3 seed、資源計測で判定する。

## Current phase

**Phase 1.5: D005 predispatch audit returned `PREREG_BLOCKED`; C005 execution-route preregistration is the sole bottleneck.**

Completed: A001–A004, B001–B006, C001–C004, D001–D005 predispatch audit, E001–E005.

Current classifications:

- Block AttnRes: **小型化で要再設計・追加検証・未採用 / Path-WARN**
- PAPER-BLOCK (`PB1`): canonical paper-reference candidate; semantic trace pending
- CANDIDATE-RAW (`CR1`): fixed-commit artifact diagnostic only; paper attribution prohibited
- Execution state: **PREREG_BLOCKED**

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

B006 fixed the result semantics:

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
- D005: confirmed C005 prose/manifest are absent and correctly returned `PREREG_BLOCKED`; workflow was not changed
- E005: made C005 the sole next step and prohibited repeated D predispatch churn

Integration record:

- `research/intelligence_swarm/k3_loop/integration/E005_C005_PREREGISTRATION_ORDER_GATE_DECISION.md`
- E005 commit: `871868f9c4c11b4c1b632563411a5f855929222d`

## Single bottleneck

C must create exactly:

1. `research/intelligence_swarm/k3_loop/prereg/C005_D003_GHA_PUSH_ROUTE_AMENDMENT.md`
2. `benchmarks/k3_minimal/manifests/C005_d003_gha_push_route.yaml`

C005 must fix:

- canonical branch only
- environment-file path restriction
- concurrency and cancellation behavior
- `training_authorized=false`
- `model_execution_authorized=false`
- provenance/resolver/freeze/import/raw-log artifact schema
- no automatic transition from environment PASS to model execution
- one unchanged retry only for a transient failure after run start
- `ENV_PASS`, `ENV_RETRY`, `ROUTE_STOP`, `ENV_PATH_STOP`
- later PB1 trace contract: 1-based indexing, `24/4/6`, boundaries `[3,6,9,12]`, odd/non-divisible rejection, source slots `84/5/89`

These semantic fields do not authorize model execution.

## Authorized next work

- A: no new K3 component; inspect only a concrete resolver/import failure
- B: no crossover, minimum-scale, or Pareto revision before exact traces; PB1 result interpretation is fixed by B006
- C: create C005 prose and manifest only
- D: do not alter or start the workflow until C005 exists
- E: after D returns, classify only execution/environment outcome

## Completion / stop classification

- before C005 exists: `PREREG_BLOCKED`
- `ENV_PASS`: exact environment/import evidence and artifact ID/SHA fixed
- `ENV_RETRY`: transient Actions/package-index/DNS/network failure after start; one unchanged retry
- `ROUTE_STOP`: exact registered route does not start or is persistently rejected
- `ENV_PATH_STOP`: after at most one preregistered API-wiring-only patch, fixed dependencies/imports still require semantic change

`ROUTE_STOP` and `ENV_PATH_STOP` do not by themselves reject Block AttnRes.

## Evidence boundary

Quality, exact model bytes, active compute, isolated peak RSS, training time, CPU generation, quantization tolerance, and three-seed stability remain unmeasured. No new intelligence principle, capability progress, high-school-level capability, or 1GB-goal achievement is supported.