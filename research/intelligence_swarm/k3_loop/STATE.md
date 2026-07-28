# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-29 by K3-E
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3由来の効率化原理を、1GB以下・弱いCPU/スマホ向けモデルへ転用できるか、公開baseline、単一変更ablation、3 seed、資源計測で判定する。

## Current phase

**Phase 1.9: C007/B008 complete. D008 is the only authorized next action: one portable environment-only attempt or one concrete `SUBSTRATE_STOP`.**

Completed: A001–A006, B001–B008, C001–C007, D001–D007, E001–E008.

Current classifications:

- Block AttnRes: **小型化で要再設計・追加検証・未採用 / Path-WARN**
- PAPER-BLOCK (`PB1`): canonical paper-reference candidate; semantic trace pending
- CANDIDATE-RAW (`CR1`): fixed-commit artifact diagnostic only; paper attribution prohibited
- C005 canonical-push route: **`ROUTE_STOP / closed`**
- C006/D007 default-branch route: **`ENV_PROTOCOL_FAIL + ROUTE_STOP_DEFAULT_BRANCH / closed`**
- Execution state: **`D008_EXECUTION_ONLY_PENDING`**

Frozen until P0 environment and semantic gates complete: new architecture, dataset download, optimizer step, S1–S3, quantization, KDA, Stable LatentMoE.

## Fixed references

- scientific source commit: `9edf4c7143ff1d62685ed893352df7a32090fe1e`
- candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- official: `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6`
- Transformers commit: `42791a34fdeae197f60f11ace3807c81f44b0729`
- official executable training baseline: not released
- C007 prose blob: `42ca0249037caecf855de98c978f4a50373d2e94`
- C007 manifest blob at creation: `26bdaaf2d67567e65fad847129719cc3a2cce071`

A005 found no author executable code, checkpoint, dependency lock, immutable data manifest or evaluation harness. A006 found a compact unofficial implementation, but it has one-event-late block visibility, missing divisibility guards and a non-paper final sum; it cannot replace PB1/CR1.

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
- canonical source slots: sublayer `84`, final `5`, total `89`
- `primary_evidence_geometry_matched=false`

PB1 is a minimum semantic/effect-direction pilot. PB1 null is not mechanism-wide falsification, and PB1 positive is not sufficient for adoption.

## Existing executable evidence

D002 standalone reconstruction passed instantiate, forward/backward, routing-gradient and save/load gates, but it was not the exact candidate Transformers runtime.

Standalone routing medians:

- T=1: `0.112487 ms`
- T=128: `0.627961 ms`
- T=512: `2.252197 ms`
- T=2048: `35.944465 ms`

The 2048-token result was about 4.13x the short-sequence fit and remains unconfirmed in the exact runtime.

## Closed execution routes

- D003 local exact-runtime attempt: `BLOCKED_ENV`
- C005/D006 canonical-branch push route: `ROUTE_STOP`, closed
- C006/D007 default-branch route: `ENV_PROTOCOL_FAIL`, closed
- incomplete `.github/workflows/d007-k3-environment-dispatcher.yml` is quarantined and must never be dispatched

## C007 portable environment contract

Records:

- `research/intelligence_swarm/k3_loop/prereg/C007_PORTABLE_ENVIRONMENT_GATE_PREREGISTRATION.md`
- `benchmarks/k3_minimal/manifests/C007_portable_environment_gate.yaml`

C007 fixes:

- GitHub-Actions-independent online-Git or offline-Git-bundle acquisition
- scientific source commit and canonical-ref reachability
- detached checkout, clean tree, untracked/submodule/LFS rejection
- C003/C004/C007/runner/probe Git blob, byte SHA256, path and size evidence
- Python `3.11.x`, exact CPU PyTorch build, fixed Transformers commit and complete dependency artifact hashes
- `sys.path`, module-origin paths and imported-source hashes
- all model-stage authorization flags `false`
- OS/CPU/libc/container/runtime provenance
- inner evidence-file checksums and outer deterministic archive SHA256/size
- exact replay command, one unchanged transient retry and six result classes

Environment success remains non-model evidence and cannot update quality, CPU, memory, quantization, scale or Pareto claims.

## E008 integration decision

C007 and B008 already close the portable protocol and evidence-admissibility questions. No D008 result exists. Further evidence, theory, preregistration, trigger, dispatcher or substrate audits are prohibited because they do not test the hypothesis.

## Single next hypothesis

One C007-compliant portable environment-only attempt can produce one admissible classified result without model execution or semantic changes.

## Single bottleneck

**D008 portable environment-only execution or one concrete `SUBSTRATE_STOP`.**

## Authorized next work

- A: no work unless D008 exposes a concrete dependency/source mismatch
- B: no new theory, CPU crossover, minimum-scale or Pareto update before exact trace
- C: no amendment unless D008 exposes one specific protocol defect
- D: create the thin launcher and execute one portable attempt; if no compliant substrate exists, record one concrete `SUBSTRATE_STOP` and do not repeat substrate discovery
- E: classify the actual D008 outcome

## Prohibitions

1. no further C005/C006 trigger, nonce, dispatcher or default-branch workflow variants
2. never dispatch the incomplete D007 workflow on `main`
3. no replacement audits for D008 execution
4. no model implementation on an orchestration branch or launcher
5. no B0/PB1/CR1 instantiate, semantic trace, dataset/tokenizer/checkpoint download, training or quantization
6. no silent dependency, API or semantic patch
7. no automatic transition from environment PASS to model execution
8. no mechanism-wide rejection from PB1 `N=4` null evidence
9. no `ENV_PASS` unless imported module origins and both inner/outer checksum closures are complete

## Next completion / stop classification

- `ENV_PASS`: registered portable run, immutable identity, exact dependencies/imports, imported-module origins, raw provenance and archive checksum all pass
- `ENV_RETRY`: one unchanged retry after a run-started transient network/package-index failure
- `SUBSTRATE_STOP`: no available substrate can provide Python 3.11, required source/dependency access and artifact persistence
- `ENV_PATH_STOP_PENDING_AMENDMENT`: valid substrate/provenance but fixed non-transient dependency/import mismatch before a patch is preregistered
- `ENV_PATH_STOP`: one separately preregistered API-wiring-only patch still requires semantic change or leaves provenance incomplete
- `ENV_PROTOCOL_FAIL`: identity, clean-tree, allowlist, authorization, module-origin, checksum or artifact violation

None of these environment outcomes alone rejects Block AttnRes.

## Evidence boundary

Quality, exact model bytes, active compute, isolated peak RSS, training time, CPU generation, quantization tolerance and three-seed stability remain unmeasured. No new intelligence principle, capability progress, high-school-level capability or 1GB-goal achievement is supported.
