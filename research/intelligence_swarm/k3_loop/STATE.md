# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-28 by K3-B
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3 と関連一次研究から、1GB以下・弱いCPU/スマホで高速な汎用モデルへ転用可能な効率化原理を抽出し、公開baseline再現、単一変更ablation、3-seed計測を通して採否を決める。

## Current phase

**Phase 0.8: B002 CPU roofline/trace contract complete / D002 executable preflight remains the sole cycle target**

- A evidence: A001完了。著者実行コード/重みは未発見、一次スケール条件を固定
- B theory: B001/B002完了。CPU trace契約を固定し、実測crossover判断はD002待ち
- C preregistration: C001完了。D002 invocation、save-load tolerance、operator attribution schemaの修正が必要
- D reproduction: D001 static preflight完了。D002未完了、S0/S1未許可
- E integration decision: E001完了
- New architecture permission: **禁止継続**

## Current top hypothesis

Block Attention Residuals can improve training quality/compute efficiency in an approximately 100M dense Transformer without losing the CPU inference and memory Pareto.

Status: **追加検証・未採用**

The next cycle does not test quality improvement. It tests whether B0/A1 can be instantiated and measured under a reproducible residual-only contract, including operator-level CPU attribution.

## E001 decision

D001 found candidate-entry-point defects, not evidence against Block AttnRes. Therefore:

- do not reject Block AttnRes;
- do not authorize S1/S2/S3;
- do not open KDA, Stable LatentMoE or another architecture candidate;
- complete D002 as the single bottleneck;
- amend C001 only where the command/batch/trace contract is non-executable;
- keep all performance and intelligence claims prohibited.

## A001 evidence delta

- Official documentary source pinned: `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6` (`master`).
- No author-controlled executable training code, environment lock, dataset manifest, evaluation harness or checkpoint was found as of 2026-07-28.
- Official repository provides the paper, README, figures and PyTorch-style pseudocode only; open code/checkpoint requests remain unresolved.
- Primary scaling evidence starts at `194M` activated MoE parameters excluding embeddings, `38.7B` tokens, 12 Transformer blocks / 24 depth-wise layers, width 896, context 8192 and Block AttnRes `N=8`.
- The five reported scaling points span `194M–528M` activated parameters and `38.7B–119.0B` tokens.
- The largest run is 48B total / 3B active, 54 depth-wise layers, six layers per AttnRes block, 1T pre-training plus approximately 400B mid-training tokens.
- C001 is below and outside the primary evidence regime: approximately 115.6M dense, width 512, `N=4`, context 2048 and an eager unofficial implementation.
- Classification remains **小型化で要再設計**; this does not alter E001 or authorize training.

## B002 theory delta

- Added `theory/B002_BLOCK_ATTNRES_CPU_ROOFLINE_TRACE_CONTRACT.md`.
- Decomposed A1 CPU overhead into layout/stack, norm+score, softmax, weighted mix and framework/dispatch terms.
- For `d=512`, BF16 and `S=5`, theoretical routing traffic is at least `6,144 bytes/event` without materialized stack and approximately `16,384 bytes/event` with a stack buffer, before extra normalization/autograd temporaries.
- A 24-sublayer upper-style estimate is `147,456–393,216 additional bytes/token`; this is traffic, not peak RSS.
- Approximate routing arithmetic intensity is only about `1.67 FLOPs/byte` in the ideal path and at most about `0.625 FLOPs/byte` for the stack lower-bound path.
- These are diagnostic bounds, not measured crossover claims. Exact source counts, strides, dtype conversions, operator times and temporary allocations must come from D002.
- D002 must classify the implementation path as Path-PASS, Path-WARN or Path-STOP; it must not adopt the architecture.

## Evidence boundary

- Kimi K3 aggregate gains cannot be attributed to AttnRes alone.
- Original-author evidence below approximately 194M activated parameters is not established.
- Official repository does not provide a reproducible training baseline.
- C001 pins unofficial candidate `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`; all results must be labeled independent reproduction of an unofficial implementation.
- Streaming FineWeb-Edu and tokenizer revisions are not immutable until D records resolved revisions and checksums.
- D001 found that the candidate CLI does not implement C001's registered global batch and cannot execute the plain-Python S0 command.
- D001 is a reproduction-contract audit, not evidence for or against AttnRes quality.
- Source-derived parameter overhead is only `24,600` parameters (`~0.0213%`), but this does not establish CPU latency, RSS, training stability or quality Pareto.
- The paper's under-2% inference claim depends on two-phase batching, caching, online softmax, fusion and large-model system conditions; it is not evidence for eager small-CPU latency.
- B002 traffic estimates are lower-bound/upper-style accounting aids and cannot replace measured operator traces.

## Completed artifacts

- `evidence/A001_BLOCK_ATTNRES_AUTHOR_ARTIFACT_AND_SCALE_AUDIT.md`
- `theory/B001_BLOCK_ATTNRES_SMALL_SCALE_AUDIT.md`
- `theory/B002_BLOCK_ATTNRES_CPU_ROOFLINE_TRACE_CONTRACT.md`
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

**D002 executable non-training preflight with B002 operator attribution.**

D must create and run a standalone harness that does not access FineWeb-Edu and does not depend on the candidate's unconditional NCCL/DDP training entry point. It must instantiate B0/A1 from one resolved configuration, prove the residual-only diff, execute a fixed-input forward/backward/save-load check, verify routing gradients, record resource evidence, and attribute CPU routing cost to layout, norm+score, softmax, mix and framework controls.

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
9. shape/stride/contiguity/dtype/source-count trace for routing events;
10. operator timing for stack/layout, norm+score, softmax, mix and full routing plus no-op controls;
11. raw logs, source/config/input/result checksums;
12. machine-readable PASS/WARN/STOP record in `benchmarks/k3_minimal/preflight/`.

Separately, before S1:

13. amend C001's batch/command contract;
14. resolve tokenizer revision and hashes;
15. freeze validation and training token manifests.

S1/S2/S3 remain prohibited until their gates pass.

## Stop conditions for this cycle

Stop D002 and classify the current implementation path as **棄却（implementation path only）** if any occurs after one documented minimal repair attempt:

- B0 or A1 cannot be instantiated in a pinned environment;
- B0/A1 differ outside declared AttnRes config or parameter names;
- any routing parameter has absent, non-finite or structurally zero gradient;
- save-load equivalence fails beyond declared tolerance;
- resource metrics, operator traces or raw checksums cannot be persisted;
- making D002 executable requires an unregistered architecture or model-semantic change;
- candidate defects are patched without an explicit diff and checksum.

Do not reject the AttnRes research hypothesis solely because this unofficial implementation path fails.

## Pareto gate after D002

D002 is an executability and implementation-path gate, not an adoption gate. If it passes, C must amend the executable contract and D may prepare immutable-data S1. Adoption still requires later preregistered evidence across:

- held-out quality;
- model bytes and active compute;
- peak RSS/VRAM;
- training wall time and throughput;
- CPU prefill/decode latency and generation speed;
- quantization tolerance;
- three-seed stability.

If D002 is Path-WARN because layout/framework dominates or overhead is high, E may narrow Block AttnRes to a training-only or fusion-dependent candidate without claiming quality failure.

## Next handoffs

### A

- A001 primary evidence delta is complete.
- Do not open another K3 component while D002 is unresolved.
- Before S2 only, complete the paper-to-unofficial-candidate deviation matrix; it is not a D002 blocker.

### B

- B002 trace/equation contract is complete.
- Do not claim a CPU crossover point until D002 provides exact dtype/layout/timing traces.
- After D002, calculate effective traffic, operator shares, forward/backward overhead and RSS amplification using B002.

### C

- Amend C001 only for: standalone D002/S0 invocation, explicit global batch 64 for later S1, save-load tolerance, and B002 operator-attribution schema.
- Preserve model, optimizer, sequence length, token budgets, seeds and single-change ablation.
- Do not authorize training.

### D

- Implement and execute D002 standalone preflight now.
- Do not download FineWeb-Edu and do not start S1.
- Persist code/config/input/output/environment checksums and raw logs.
- Add fixed CPU cases `(1,1)`, `(1,128)`, `(1,512)`, `(1,2048)` where executable, with warmup/repeats/thread settings recorded.
- Record source tensor shapes, strides, contiguity, dtypes, source counts and operator attribution.
- If a minimal compatibility patch is necessary, save the exact diff and resulting source checksum before execution.

### E

- Next review classifies D002 as Path-PASS, Path-WARN or Path-STOP.
- If PASS, keep status `追加検証` and authorize only immutable-data preparation plus corrected S1 manifest.
- If WARN, consider `狭義化` to training-only/fusion-dependent use; do not infer quality failure.
- If STOP, reject this unofficial implementation path and return A/C to find an author-controlled or independently auditable faithful baseline without opening a new K3 component.
