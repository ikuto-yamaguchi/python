# D002 — Standalone Block AttnRes executable preflight

Date: 2026-07-28  
Branch: `research/intelligence-swarm-reconstruction-001`  
Candidate reference: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`  
Candidate source blob: `649aa0067e5b9d0fc2a3cc68784a6794090a26a4`

## Scope

D002 is a non-training executability gate. It does not test language-model quality and does not authorize S1. FineWeb-Edu, tokenizer downloads, NCCL and DDP are not used.

Because the runtime had PyTorch but no installable `transformers` package and no external network access, the harness implements a standalone, parameter-faithful Qwen3-style dense decoder and copies only the candidate's declared Block AttnRes computation: `stack -> RMSNorm -> pseudo-query score -> softmax -> weighted sum`, including the candidate's final model-level Block AttnRes router. This is an independently auditable faithful preflight, not a claim that the exact Hugging Face implementation was executed.

## Pinned runtime

- Python: 3.13.5
- PyTorch: 2.10.0+cpu
- CUDA available: false
- CPU threads: 1
- Platform: Linux x86_64
- Executed harness SHA256: `5cff2119df1e57faf8e529631a02f2a19f602ef7ad939994df2d35cbc91e24f7`
- Result JSON SHA256: `a80f622028a9643ad3bbec06a04c8e3e4be905a5817dbcfbce3b9c48d91d0bd6`
- Fixed input: seed 17, shape `[1,4]`

## Critical correction to D001

D001 counted only the 12 layer-local routing modules, totaling 24,600 parameters. The candidate's block-mode backbone also defines a final router:

- `final_res_proj.weight`: 512
- `final_res_norm.weight`: 512
- `final_res_bias`: 1

Therefore the executable candidate delta is **25,625**, not 24,600 parameters.

| Condition | Parameters | FP32 parameter bytes |
|---|---:|---:|
| B0 | 115,554,304 | 462,217,216 |
| A1 | 115,579,929 | 462,319,716 |
| Delta | 25,625 | 102,500 |

Relative parameter overhead is approximately **0.02218%**.

## Executability checks

- B0 instantiated with exactly 115,554,304 parameters.
- A1 instantiated with exactly 115,579,929 parameters.
- Parameter-name diff contains 75 A1-only tensors and no B0-only tensors.
- Every A1-only tensor is an `attn_res_*`, `mlp_res_*`, or `final_res_*` routing tensor.
- Both conditions completed finite forward/backward.
- All 75 routing parameters had finite and non-zero gradients.
- Save/load produced exact output equality in this runtime (`max_abs_diff = 0.0`).
- Source count, shape, stride, contiguity, dtype, temporary-byte estimate and operator timings were persisted for all 25 routing events.
- Process maximum RSS was 2,203,936 KiB. This is a process-level high-water mark across sequential B0/A1 execution and checkpoint serialization, not isolated per-condition steady-state RSS.

## Operator microbenchmark

Standalone routing, FP32, batch 1, width 512, five sources, one CPU thread; two warmups and five measured repetitions:

| Sequence | Median full routing time |
|---:|---:|
| 1 | 0.112 ms |
| 128 | 0.628 ms |
| 512 | 2.252 ms |
| 2048 | 35.944 ms |

The 2048-token point rises sharply and supports B002's warning that materialized stack/layout and memory traffic can dominate on CPU. These timings are operator microbenchmarks, not end-to-end decode or prefill latency.

## Timing caveat

The first full-model B0 forward/backward took 8.13 s while the subsequently executed A1 took 0.518 s. This ordering is contaminated by first-use kernel/runtime warm-up and checkpoint page-cache effects. It must not be interpreted as A1 being faster. A later paired benchmark must alternate conditions after warm-up in fresh processes.

## Decision

**Path-WARN / executable preflight passed with measurement limitations.**

The residual-only parameter contract, gradients and save/load gate pass. However:

1. the exact third-party Hugging Face implementation was not executable in the pinned runtime because `transformers` was unavailable;
2. process RSS is not isolated per condition;
3. full-model B0/A1 timing is order-contaminated;
4. operator controls do not yet separately time no-op/list traversal versus stack-only in fresh processes;
5. no quality, training throughput, CPU generation, or quantization evidence exists.

Therefore Block AttnRes remains **追加検証・未採用**. S1/S2/S3 remain prohibited.

## Next minimal step

C should amend C001 with the corrected A1 parameter count and an executable S0 schema. D should run D003 as a fresh-process paired preflight using an environment with the pinned candidate dependencies, alternating B0/A1 after warm-up, isolating RSS, and adding explicit no-op/list/stack controls. Only after E review may immutable tokenizer/data preparation begin.
