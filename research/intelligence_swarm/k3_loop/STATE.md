# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-28 by K3-E
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3 と関連一次研究から、1GB以下・弱いCPU/スマホで高速な汎用モデルへ転用可能な効率化原理を抽出し、公開baseline再現、単一変更ablation、3-seed計測を通して採否を決める。

## Current phase

**Phase 0.7: E001 integration complete / D002 executable preflight is the sole cycle target**

- A evidence: 未投入。P0を妨げる不足一次資料だけを補う
- B theory: B001完了。D002 traceまで追加architecture監査を停止
- C preregistration: C001完了。実験対象を変えず、実行契約の修正だけが必要
- D reproduction: D001 static preflight完了。D002未完了、S0/S1未許可
- E integration decision: E001完了
- New architecture permission: **禁止継続**

## Current top hypothesis

Block Attention Residuals can improve training quality/compute efficiency in an approximately 100M dense Transformer without losing the CPU inference and memory Pareto.

Status: **追加検証・未採用**

The next cycle does not test quality improvement. It tests whether B0/A1 can be instantiated and measured under a reproducible residual-only contract.

## E001 decision

D001 found candidate-entry-point defects, not evidence against Block AttnRes. Therefore:

- do not reject Block AttnRes;
- do not authorize S1/S2/S3;
- do not open KDA, Stable LatentMoE or another architecture candidate;
- complete D002 as the single bottleneck;
- amend C001 only where the command/batch contract is non-executable;
- keep all performance and intelligence claims prohibited.

## Evidence boundary

- Kimi K3 aggregate gains cannot be attributed to AttnRes alone.
- Original-author evidence below approximately 194M activated parameters is not established.
- Official repository does not provide a reproducible training baseline.
- C001 pins unofficial candidate `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`; all results must be labeled independent reproduction of an unofficial implementation.
- Streaming FineWeb-Edu and tokenizer revisions are not immutable until D records resolved revisions and checksums.
- D001 found that the candidate CLI does not implement C001's registered global batch and cannot execute the plain-Python S0 command.
- D001 is a reproduction-contract audit, not evidence for or against AttnRes quality.
- Source-derived parameter overhead is only `24,600` parameters (`~0.0213%`), but this does not establish CPU latency, RSS, training stability or quality Pareto.

## Completed artifacts

- `theory/B001_BLOCK_ATTNRES_SMALL_SCALE_AUDIT.md`
- `prereg/C001_BLOCK_ATTNRES_100M_PREREG.md`
- `benchmarks/k3_minimal/manifests/C001_block_attnres_100m.yaml`
- `reproduction/D001_C001_PREFLIGHT_CONTRACT_AUDIT.md`
- `benchmarks/k3_minimal/preflight/D001_candidate_contract_audit.json`
- `DECISIONS.jsonl` — E001 integration decision

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

**D002 executable non-training preflight.**

D must create and run a standalone harness that does not access FineWeb-Edu and does not depend on the candidate's unconditional NCCL/DDP training entry point. It must instantiate B0/A1 from one resolved configuration, prove the residual-only diff, execute a fixed-input forward/backward/save-load check, verify routing gradients, and record resource evidence.

No other hypothesis may replace this bottleneck during the next cycle unless D002 proves the candidate cannot be instantiated without changing more than the residual path.

## Completion condition for next cycle

D002 must complete all of the following:

1. exact Python/PyTorch/Transformers environment resolution;
2. fixed synthetic input and SHA256;
3. exact instantiated B0/A1 parameter counts and parameter-name diff;
4. serialized config diff showing no non-AttnRes architectural changes;
5. one finite forward/backward optimizer step for both conditions;
6. finite nonzero gradients for every Block AttnRes routing parameter;
7. save-load and post-load logits equivalence check under a declared tolerance;
8. peak RSS/VRAM and wall-time logging;
9. raw logs, source/config/input/result checksums;
10. machine-readable PASS/FAIL record in `benchmarks/k3_minimal/preflight/`.

Separately, before S1:

11. amend C001's batch/command contract;
12. resolve tokenizer revision and hashes;
13. freeze validation and training token manifests.

S1/S2/S3 remain prohibited until their gates pass.

## Stop conditions for this cycle

Stop D002 and classify the current implementation path as **棄却（implementation path only）** if any occurs after one documented minimal repair attempt:

- B0 or A1 cannot be instantiated in a pinned environment;
- B0/A1 differ outside declared AttnRes config or parameter names;
- any routing parameter has absent, non-finite or structurally zero gradient;
- save-load equivalence fails beyond declared tolerance;
- resource metrics or raw checksums cannot be persisted;
- making D002 executable requires an unregistered architecture or model-semantic change;
- candidate defects are patched without an explicit diff and checksum.

Do not reject the AttnRes research hypothesis solely because this unofficial implementation path fails.

## Pareto gate after D002

D002 is an executability gate, not an adoption gate. If it passes, C must amend the executable contract and D may prepare immutable-data S1. Adoption still requires later preregistered evidence across:

- held-out quality;
- model bytes and active compute;
- peak RSS/VRAM;
- training wall time and throughput;
- CPU prefill/decode latency and generation speed;
- quantization tolerance;
- three-seed stability.

## Next handoffs

### A

- Confirm whether an author-controlled executable implementation/checkpoint exists beyond `MoonshotAI/Attention-Residuals` documentation.
- Extract only the exact primary-report Block AttnRes model/depth/block/token/compute settings needed to compare C001; do not start another candidate family.
- Deliver a concise evidence delta to `evidence/`; absence of code must be recorded explicitly.

### B

- Keep B001 unchanged until D002 produces dtype/layout/timing traces.
- Prepare the equations/fields needed for an eager-memory-traffic and CPU roofline calculation, but do not claim a crossover point without traces.
- On D002 output, check whether the 24,600-parameter overhead is dominated by activation reads, stack/einsum/softmax, or framework launch overhead.

### C

- Amend C001 only for: (1) standalone D002/S0 invocation, and (2) explicit realization of global batch 64 for later S1.
- Preserve model, optimizer, sequence length, token budgets, seeds and single-change ablation.
- Add declared save-load tolerance and D002 PASS/FAIL schema; do not authorize training.

### D

- Implement and execute D002 standalone preflight now.
- Do not download FineWeb-Edu and do not start S1.
- Persist code/config/input/output/environment checksums and raw logs.
- If a minimal compatibility patch is necessary, save the exact diff and resulting source checksum before execution.

### E

- Next review is binary: D002 gate PASS or implementation-path STOP.
- If PASS, keep status `追加検証` and authorize only immutable-data preparation plus corrected S1 manifest.
- If STOP, reject this unofficial implementation path and return A/C to find an author-controlled or independently auditable faithful baseline without opening a new K3 component.
