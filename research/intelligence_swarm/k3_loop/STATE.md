# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-28 by K3-D
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3 と関連一次研究から、1GB以下・弱いCPU/スマホで高速な汎用モデルへ転用可能な効率化原理を抽出し、公開baseline再現、単一変更ablation、3-seed計測を通して採否を決める。

## Current phase

**Phase 0.6: Block AttnRes static preflight complete / executable harness required**

- A evidence: 未投入
- B theory: B001完了
- C preregistration: C001完了、D001で実行契約修正が必要と判明
- D reproduction: D001 static preflight完了、S0/S1未許可
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
- D001 found that the candidate CLI does not implement C001's registered global batch and cannot execute the plain-Python S0 command.
- D001 is a reproduction-contract audit, not evidence for or against AttnRes quality.

## Completed artifacts

- `theory/B001_BLOCK_ATTNRES_SMALL_SCALE_AUDIT.md`
- `prereg/C001_BLOCK_ATTNRES_100M_PREREG.md`
- `benchmarks/k3_minimal/manifests/C001_block_attnres_100m.yaml`
- `reproduction/D001_C001_PREFLIGHT_CONTRACT_AUDIT.md`
- `benchmarks/k3_minimal/preflight/D001_candidate_contract_audit.json`

## Locked experiment

- B0: 12-layer Qwen3-style dense PreNorm baseline, d=512, heads=8, KV heads=4, FFN=1536
- A1: B0 plus Block AttnRes `N=4` only
- sequence length 2048
- intended global effective batch: 64 sequences/step; current candidate script does **not** implement this contract
- seeds `17/29/43`
- S1 smoke: 100 steps; S2 pilot: 2,000; S3 full: 20,000
- no KDA, MoE, Delta-V, Full AttnRes, curriculum or post-training

## D001 fixed static counts

- B0 total/active parameters: `115,554,304`
- A1 total/active parameters: `115,578,904`
- AttnRes addition: `24,600` parameters
- relative parameter overhead: approximately `0.0213%`
- B0 BF16 static weight bytes: `231,108,608`
- A1 BF16 static weight bytes: `231,157,808`

These values remain source-derived until D002 verifies them by model instantiation.

## Current single bottleneck

D must create and run a non-training reproducibility harness that instantiates B0/A1 from one resolved configuration, verifies exact config/parameter differences, performs one fixed-input forward/backward/save-load check, verifies AttnRes routing gradients, and records RSS/VRAM/wall time. S1 remains blocked independently by the immutable tokenizer and FineWeb-Edu token-stream requirement.

## Completion condition for next cycle

D002 must complete:

1. exact Python/PyTorch/Transformers environment resolution
2. fixed synthetic input and SHA256
3. exact instantiated B0/A1 parameter counts and parameter-name diff
4. serialized config diff showing no non-AttnRes architectural changes
5. one finite forward/backward optimizer step for both conditions
6. finite nonzero gradients for every Block AttnRes routing parameter
7. save-load and post-load logits equivalence check
8. peak RSS/VRAM and wall-time logging
9. raw logs and checksums

Separately, before S1:

10. amend C001's batch/command contract
11. resolve tokenizer revision and hashes
12. freeze validation and training token manifests

S1/S2/S3 remain prohibited until their gates pass.

## Stop conditions

- baseline is not reproducible
- token streams differ between B0/A1
- more than the residual path changes
- resource metrics cannot be recorded
- routing parameters receive no gradient
- smoke step time regresses >30% or peak VRAM >25% without a configuration error
- unofficial reported scores are copied without raw reproduction
- candidate entry-point defects are silently patched without documenting the patch and resulting source checksum

## Next handoffs

- A: identify author-controlled artifacts and exact primary-report scaling setup; do not open another architecture cycle.
- B: use D001's exact 24,600-parameter overhead; wait for D002/S1 traces before CPU roofline refinement.
- C: amend only the executable contract defects found by D001: global batch realization and S0 invocation. Do not change the experiment target.
- D: implement and execute D002 non-training preflight; do not start FineWeb-Edu training.
- E: keep status at `追加検証`; deny S1/S2 until D002 and immutable data gates pass.
