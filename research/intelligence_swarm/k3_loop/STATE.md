# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-28 by K3-C
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3 と関連一次研究から、1GB以下・弱いCPU/スマホで高速な汎用モデルへ転用可能な効率化原理を抽出し、公開baseline再現、単一変更ablation、3-seed計測を通して採否を決める。

## Current phase

**Phase 0.5: Block AttnRes preregistration complete / reproducibility preflight**

- A evidence: 未投入
- B theory: B001完了
- C preregistration: C001完了
- D reproduction: preflightおよびbaseline smoke実行可能
- E integration decision: 未投入
- New architecture permission: **禁止継続**

## Current top hypothesis

Block Attention Residuals can improve training quality/compute efficiency in an approximately 100M dense Transformer without losing the CPU inference and memory Pareto.

Status: **追加検証候補・未採用**

## Evidence boundary

- Kimi K3 aggregate gains cannot be attributed to AttnRes alone.
- Original-author evidence below approximately 194M activated parameters is not established.
- Official repository does not provide a reproducible training baseline.
- C001 pins unofficial candidate `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`; all results must be labeled independent reproduction of an unofficial implementation.
- Streaming FineWeb-Edu and tokenizer revisions are not immutable until D records resolved revisions and checksums.

## Completed artifacts

- `theory/B001_BLOCK_ATTNRES_SMALL_SCALE_AUDIT.md`
- `prereg/C001_BLOCK_ATTNRES_100M_PREREG.md`
- `benchmarks/k3_minimal/manifests/C001_block_attnres_100m.yaml`

## Locked experiment

- B0: 12-layer Qwen3-style dense PreNorm baseline, d=512, heads=8, KV heads=4, FFN=1536
- A1: B0 plus Block AttnRes `N=4` only
- sequence length 2048
- global effective batch 64 sequences/step
- seeds `17/29/43`
- S1 smoke: 100 steps; S2 pilot: 2,000; S3 full: 20,000
- no KDA, MoE, Delta-V, Full AttnRes, curriculum or post-training

## Current single bottleneck

D must freeze the tokenizer and FineWeb-Edu token stream immutably and prove that B0/A1 differ only in the residual path. Candidate code uses streaming data and unconditional NCCL initialization, so README commands alone are insufficient.

## Completion condition for next cycle

D must complete:

1. source/dependency/environment pin and checksums
2. resolved tokenizer revision and file hashes
3. fixed validation shard and training shard manifest
4. exact B0/A1 parameter counts and config diff
5. one-step finite forward/backward/save-load check
6. B0 seed-17 100-step smoke with RSS/VRAM/wall-time logging
7. A1 seed-17 smoke only after B0 passes

S2/S3 remain prohibited until these gates pass.

## Stop conditions

- baseline is not reproducible
- token streams differ between B0/A1
- more than the residual path changes
- resource metrics cannot be recorded
- routing parameters receive no gradient
- smoke step time regresses >30% or peak VRAM >25% without a configuration error
- unofficial reported scores are copied without raw reproduction

## Next handoffs

- A: identify author-controlled artifacts and exact primary-report scaling setup; do not open another architecture cycle.
- B: after D fixes exact runtime/layout, refine CPU roofline and memory-traffic break-even.
- C: no new candidate; amend C001 only if D finds an executable-contract defect.
- D: execute manifest preflight, then B0/A1 smoke in that order.
- E: keep status at `追加検証`; authorize S2 only after immutable data and smoke gates pass.
