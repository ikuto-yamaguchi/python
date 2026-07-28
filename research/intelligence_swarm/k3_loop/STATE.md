# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-29 by K3-B
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3由来の効率化原理を、1GB以下・弱いCPU/スマホ向けモデルへ転用できるか、公開baseline、単一変更ablation、3 seed、資源計測で判定する。

## Current phase

**Phase 1.8: D007 ended in `ENV_PROTOCOL_FAIL`; both GitHub Actions routes are closed. C007 portable environment-gate preregistration is the sole next step.**

Completed: A001–A006, B001–B008, C001–C006, D001–D007, E001–E007.

Current classifications:

- Block AttnRes: **小型化で要再設計・追加検証・未採用 / Path-WARN**
- PAPER-BLOCK (`PB1`): canonical paper-reference candidate; semantic trace pending
- CANDIDATE-RAW (`CR1`): fixed-commit artifact diagnostic only; paper attribution prohibited
- C005 canonical-push route: **`ROUTE_STOP / closed`**
- C006/D007 default-branch route: **`ENV_PROTOCOL_FAIL + ROUTE_STOP_DEFAULT_BRANCH / closed`**
- Execution state: **`C007_PREREGISTRATION_REQUIRED`**

Frozen until P0 environment and semantic gates complete: new architecture, dataset download, optimizer step, S1–S3, quantization, KDA, Stable LatentMoE.

## Fixed references

- candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- official: `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6`
- Transformers commit: `42791a34fdeae197f60f11ace3807c81f44b0729`
- official executable training baseline: not released

A005 found no author executable code, checkpoint, dependency lock, immutable data manifest, or evaluation harness. A community Megatron implementation remains an independent reproduction lead only and cannot replace PB1/CR1 during P0.

A006 audited `kyegomez/attn_res@b634f0d9bcc6a925f118f828e07f79679b70ed6f` as a compact public small-model scaffold. It is unofficial and has paper-semantic deviations: completed blocks become visible one routing event late, equal block divisibility is not enforced, and the final output uses an unlearned source sum instead of the paper-consistent final router. It provides no controlled small-model quality, CPU, quantization, long-context or multi-seed evidence and is not admissible as a PB1 replacement.

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

PB1 is a minimum semantic/effect-direction pilot, not a reproduction of the primary `N≈8–9` evidence geometry. PB1 null is not mechanism-wide falsification, and PB1 positive is not sufficient for adoption.

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
- D004 workflow staged; manual dispatch unavailable
- C005/D006 canonical-branch push route: no environment workflow run generated; `ROUTE_STOP`, closed
- C006 preregistered a default-branch thin dispatcher
- D007 committed an incomplete minimal workflow to `main` at `0091e002dfb965e59adda99d7319ceba03e565e6`
- the workflow lacks mandatory C006 immutable-input, identity, authorization, raw-evidence and archive-checksum gates
- no workflow run was dispatched
- the available interface rejected compliant replacement and cleanup deletion
- E007 classifies the run `ENV_PROTOCOL_FAIL` and closes the default-branch GitHub Actions route as `ROUTE_STOP_DEFAULT_BRANCH`
- the incomplete workflow is quarantined and must not be dispatched

Records:

- `research/intelligence_swarm/k3_loop/reproduction/D007_DEFAULT_BRANCH_DISPATCHER_PROTOCOL_BLOCKER.md`
- `benchmarks/k3_minimal/preflight/D007_default_branch_dispatcher_result.json`
- `research/intelligence_swarm/k3_loop/integration/E007_D007_PROTOCOL_FAIL_AND_ROUTE_CLOSURE_DECISION.md`
- `research/intelligence_swarm/k3_loop/evidence/A006_SMALL_PUBLIC_IMPLEMENTATION_SEMANTIC_AND_EVIDENCE_AUDIT.md`
- `research/intelligence_swarm/k3_loop/theory/B008_PORTABLE_SUBSTRATE_EQUIVALENCE_AND_TRUST_CLOSURE_AUDIT.md`

## Portable-substrate evidence contract

B008 fixed the conditions under which a non-GitHub-Actions environment run is evidence-equivalent to B007. Portability removes the platform-provided chain of custody, so C007/D008 must explicitly close:

- canonical commit/ref reachability and clean/exact source identity
- normative file Git-blob SHA, byte SHA256, path and size
- exact dependency artifacts and resolver state
- all model-stage authorization flags as false
- OS/CPU/libc/container/runtime provenance
- `sys.path`, imported-module origin paths and source hashes
- inner evidence-file checksums plus outer archive SHA256 and byte size

Environment success remains non-model evidence and cannot update quality, CPU, memory, quantization, scale, or Pareto claims.

## Single next hypothesis

A self-contained portable environment-only bundle can validate the exact canonical/dependency/import contract on a compliant non-GitHub-Actions substrate while preserving B007/B008 evidence-admissibility requirements and keeping every model-stage authorization false.

## Single bottleneck

**C007 portable offline/externally executed environment-gate preregistration.**

C007 must define the immutable identities, exact dependency contract, clean/exact-content verification, imported-module origin verification, authorization isolation, artifact schema, replay command, retry boundary and result classes for one portable environment-only attempt.

## Authorized next work

- A: no new K3 component; add provenance only after a concrete resolver/import failure
- B: portable-substrate equivalence completed in B008; no CPU crossover, minimum-scale or Pareto update before exact trace
- C: create C007 prose and machine-readable manifest only, including B008 trust-closure requirements
- D: do not touch or dispatch the incomplete default-branch workflow; after C007, build and run one portable environment-only attempt on an available compliant substrate
- E: classify the C007/D008 substrate and environment outcome

## Prohibitions

1. no further C005/C006 trigger, nonce, dispatcher or default-branch workflow variants
2. do not dispatch `.github/workflows/d007-k3-environment-dispatcher.yml` in its current form
3. no model implementation on an orchestration branch or launcher
4. no B0/PB1/CR1 instantiate, semantic trace, dataset/tokenizer/checkpoint download, training or quantization before separate authorization
5. no silent dependency, API or semantic patch
6. no automatic transition from environment PASS to model execution
7. no mechanism-wide rejection from PB1 `N=4` null evidence
8. no `ENV_PASS` unless imported module origins and both inner/outer checksum closures are complete

## Next completion / stop classification

- `ENV_PASS`: registered portable run, immutable identity, exact dependencies/imports, imported-module origins, raw provenance and archive checksum all pass
- `ENV_RETRY`: one unchanged retry after a run-started transient network/package-index failure
- `SUBSTRATE_STOP`: no available substrate can provide Python 3.11, required source/dependency access and artifact persistence
- `ENV_PATH_STOP_PENDING_AMENDMENT`: valid substrate/provenance but fixed non-transient dependency/import mismatch before a patch is preregistered
- `ENV_PATH_STOP`: one separately preregistered API-wiring-only patch still requires semantic change or leaves provenance incomplete
- `ENV_PROTOCOL_FAIL`: identity, clean-tree, allowlist, authorization, module-origin, checksum or artifact violation

None of these environment outcomes alone rejects Block AttnRes.

## Evidence boundary

Quality, exact model bytes, active compute, isolated peak RSS, training time, CPU generation, quantization tolerance, and three-seed stability remain unmeasured. No new intelligence principle, capability progress, high-school-level capability, or 1GB-goal achievement is supported.