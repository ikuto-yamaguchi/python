# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-29 by K3-B
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3由来の効率化原理を、1GB以下・弱いCPU/スマホ向けモデルへ転用できるか、公開baseline・単一変更ablation・3 seed・資源計測で判定する。

## Current phase

**Phase 1.4: D003-GHA dependency/import gateとPAPER-BLOCK semantic gate。**

Completed: A001–A003, B001–B004, C001–C002, D001–D002, E001–E003.

Current classifications:

- Block AttnRes: **小型化で要再設計・追加検証・未採用 / Path-WARN**
- PAPER-BLOCK: canonical candidate pending C004 and deterministic semantic trace
- CANDIDATE-RAW: artifact diagnostic only; not a paper reproduction

Frozen until P0 completes: new architecture, dataset download, optimizer step, S1–S3, quantization, KDA, Stable LatentMoE.

## Fixed references

- candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- official: `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6`
- Transformers commit: `42791a34fdeae197f60f11ace3807c81f44b0729`
- official executable training baseline: not released

## B004 result

A003の未resetとrecency biasは、routing prior、gradient allocation、effective depth diversityを同時に変える複合介入である。biasだけを除いてもduplicate priorが残り、resetだけ直してもrecency priorが残るため、CANDIDATE-RAWのB0差分からpaper Block AttnRes単独効果は識別できない。

4個の旧source、default bias 3の例では、duplicated latest prefixのsemantic probability massは約0.8007、checksum-collapsed effective semantic source countは約1.55。nominal source数が多くても、実質的に最新prefix bypassへcollapseし得る。

Parameter contract:

- B0: `115,554,304`
- CANDIDATE-RAW: `115,579,929`, delta `25,625`
- PAPER-BLOCK provisional: `115,579,904`, delta `25,600`
- PAPER-BLOCK relative overhead: approximately `0.02215%`

PAPER-BLOCK countはexact executable state dictで確認する。parameter数やKV cache非増加だけでCPU軽量性を主張しない。

## Existing timing evidence

D002 standalone routing median:

- T=1: `0.112487 ms`
- T=128: `0.627961 ms`
- T=512: `2.252197 ms`
- T=2048: `35.944465 ms`

短系列fitに対しT=2048は約4.13倍。exact dependency runtimeでは未確認。

## Current bottleneck

1. D003-GHA environment/import gateをPASS
2. C004でPAPER-BLOCKとCANDIDATE-RAWを別ID・別manifestへ分離
3. tiny deterministic source traceを実行
4. PAPER-BLOCK semantic PASS後のみfull-model resource measurementへ進む

Semantic trace must record variant, layer/sublayer, boundary, source role/checksum, duplicate groups, raw and checksum-collapsed probabilities, entropy/effective source count, recency bias, and partial reset status.

PAPER-BLOCK PASS requires boundary reset, no unintended duplicate source, no recency-bias parameter, no optional mixing gate, preregistered source identities, and explained parameter delta.

## Evidence boundary

Kimi K3全体の利得をAttnRes単独へ帰属しない。著者一次証拠は約194M active未満で未確立。品質、CPU Pareto、量子化、3-seed安定性、知能原理、高校生級、能力進歩、1GB目標達成は未主張。