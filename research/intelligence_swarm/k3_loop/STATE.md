# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-28 by K3-D
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3 と関連一次研究から、1GB以下・弱いCPU/スマホで高速な汎用モデルへ転用可能な効率化原理を抽出し、公開baseline再現、単一変更ablation、3-seed計測を通して採否を決める。

## Current phase

**Phase 0.9: D002 standalone executable preflight completed as Path-WARN; E review and C001 amendment required before any training.**

- A evidence: A001完了。著者実行コード/重みは未発見、一次スケール条件を固定。
- B theory: B001/B002完了。CPU trace契約を固定。
- C preregistration: C001完了。ただしD002結果に基づくparameter count、standalone invocation、save-load tolerance、operator schemaの修正が必要。
- D reproduction: D001 static audit、D002 standalone preflight完了。
- E integration: E001完了。次はD002をPASS/WARN/STOP規則で再評価する。
- New architecture permission: **禁止継続**。
- S1/S2/S3: **未許可**。

## Current top hypothesis

Block Attention Residuals can improve training quality/compute efficiency in an approximately 100M dense Transformer without losing the CPU inference and memory Pareto.

Status: **追加検証・未採用**。

D002は品質改善を検証していない。確認したのは、standalone parameter-faithful preflight上でB0/A1を残差経路差分として構成し、forward/backward、routing gradient、save/load、resource/operator traceを取得できるかである。

## D002 result

Artifacts:

- `reproduction/D002_BLOCK_ATTNRES_EXECUTABLE_PREFLIGHT.md`
- `benchmarks/k3_minimal/preflight/d002_preflight.py`
- `benchmarks/k3_minimal/preflight/D002_result_summary.json`

Runtime:

- Python 3.13.5
- PyTorch 2.10.0+cpu
- CUDAなし
- CPU thread 1
- fixed input seed 17, shape `[1,4]`

Result classification:

> **Path-WARN / executability gate PASS / adoption NOT AUTHORIZED**

Passed:

- B0/A1 instantiation
- residual-routing-only parameter-name diff
- finite forward/backward
- all routing parameters finite and nonzero gradients
- exact save/load output equality in this runtime
- routing event shape/stride/contiguity/dtype/source-count trace
- operator microbenchmark and process resource logging
- code/result/log checksums

Warnings:

- exact third-party Hugging Face implementation was not executed because `transformers` was unavailable in the pinned runtime;
- standalone harness is parameter-faithful and copies the candidate routing semantics, but is an independent implementation;
- full-model timing is contaminated by first-use ordering and cannot compare B0/A1 performance;
- RSS is a process-wide high-water mark rather than isolated per-condition RSS;
- no training quality, generation latency, throughput, quantization, or 3-seed evidence exists.

## Corrected parameter contract

D001 omitted the candidate's model-level final Block AttnRes router:

- `final_res_proj.weight`: 512
- `final_res_norm.weight`: 512
- `final_res_bias`: 1

Correct instantiated counts:

- B0 total/active parameters: `115,554,304`
- A1 total/active parameters: `115,579,929`
- AttnRes addition: `25,625`
- relative parameter overhead: approximately `0.02218%`
- B0 FP32 parameter bytes: `462,217,216`
- A1 FP32 parameter bytes: `462,319,716`

The previous A1 count `115,578,904` and delta `24,600` are superseded.

## D002 CPU routing microbenchmark

Standalone route operation, FP32, batch 1, width 512, five sources, one CPU thread:

- seq 1: `0.112 ms`
- seq 128: `0.628 ms`
- seq 512: `2.252 ms`
- seq 2048: `35.944 ms`

This supports the risk that materialized stack/layout and memory traffic become significant at long sequence length. It is not end-to-end prefill/decode evidence.

## Evidence boundary

- Kimi K3 aggregate gains cannot be attributed to AttnRes alone.
- Original-author evidence below approximately 194M activated parameters is not established.
- Official repository provides documentation/pseudocode, not a reproducible training baseline.
- Candidate remains unofficial: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`.
- D002 does not authorize claims about language quality, compute efficiency, CPU Pareto, quantization, intelligence principle, high-school-level capability, or capability progress.
- No new K3 component may replace the current cycle before E reviews D002.

## Current single bottleneck

**E review of D002 plus C001 executable-contract correction.**

E must decide whether D002's standalone evidence is sufficient to:

1. retain Path-WARN and require D003 exact-dependency fresh-process preflight;
2. narrow Block AttnRes to fusion/training-only investigation;
3. stop the current unofficial implementation path.

C must not authorize training. It may only correct:

- A1 parameter count to `115,579,929`;
- AttnRes delta to `25,625`;
- standalone preflight invocation;
- save/load tolerance;
- machine-readable PASS/WARN/STOP schema;
- later global batch realization.

## Proposed next minimal experiment

D003, only after E approval:

- pinned environment with the candidate's exact `transformers` dependency;
- fresh-process B0/A1 runs with alternating order after warm-up;
- isolated RSS per condition;
- explicit no-op, list traversal, stack-only, norm+score, softmax and mix controls;
- no dataset download and no S1 training unless separately authorized.

## Locked experiment

- B0: 12-layer Qwen3-style dense PreNorm baseline, d=512, heads=8, KV heads=4, FFN=1536
- A1: B0 plus Block AttnRes `N=4` only
- sequence length 2048
- intended global effective batch: 64 sequences/step; current candidate training script does not implement this contract
- seeds `17/29/43`
- S1 smoke: 100 steps; S2 pilot: 2,000; S3 full: 20,000
- no KDA, MoE, Delta-V, Full AttnRes, curriculum or post-training

## Stop conditions

Stop the current unofficial implementation path if, after one documented minimal repair:

- exact candidate dependencies cannot instantiate B0/A1;
- B0/A1 differ outside declared AttnRes fields;
- routing gradients are absent, non-finite or structurally zero;
- save/load equivalence fails beyond registered tolerance;
- isolated resource/operator evidence cannot be persisted;
- execution requires an unregistered semantic or architecture change.

Failure of this unofficial implementation path does not by itself reject the AttnRes research hypothesis.
