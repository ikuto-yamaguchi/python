# D001 — C001 Block AttnRes candidate contract preflight

Date: 2026-07-28  
Branch: `research/intelligence-swarm-reconstruction-001`  
Candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`  
Status: **static preflight completed; S0/S1 blocked pending reproducibility harness**

## Scope completed in this run

This run did not start training. It completed the smallest prerequisite failure-isolation step:

1. pinned the exact candidate source blobs;
2. audited `train_scratch.py` against C001;
3. audited the Block AttnRes model construction;
4. derived exact B0/A1 parameter counts;
5. identified execution-contract defects that would invalidate a smoke comparison;
6. defined the next executable minimum action.

Machine-readable record:

- `benchmarks/k3_minimal/preflight/D001_candidate_contract_audit.json`

## Pinned source

| File | Blob SHA |
|---|---|
| `train_scratch.py` | `b077ee2e2bdfa93f67e98a30bbf971e016726cf6` |
| `Attention-Residuals/modeling_qwen3_attnres.py` | `649aa0067e5b9d0fc2a3cc68784a6794090a26a4` |
| `requirements.txt` | `f53a7aa56250d3eadc0a04313c0fe43514d96cd6` |

The candidate is unofficial. No score from its README is treated as reproduced evidence.

## Exact static parameter counts

For the preregistered configuration:

- vocabulary: 151,936
- hidden width: 512
- layers: 12
- attention heads: 8
- KV heads: 4
- head dimension: 64
- FFN intermediate size: 1,536
- tied token embeddings

### B0 baseline

| Component | Parameters |
|---|---:|
| tied embedding / LM head | 77,791,232 |
| each attention block | 786,560 |
| each MLP | 2,359,296 |
| two layer RMSNorms | 1,024 |
| all 12 decoder layers | 37,762,560 |
| final RMSNorm | 512 |
| **total** | **115,554,304** |

Static weight bytes:

- FP32: 462,217,216 bytes
- BF16: 231,108,608 bytes

### A1 Block AttnRes

Each layer adds:

- attention pseudo-query: 512
- attention routing RMSNorm: 512
- MLP pseudo-query: 512
- MLP routing RMSNorm: 512
- two scalar recency biases: 2

Total addition per layer: 2,050 parameters.  
Total addition across 12 layers: **24,600 parameters**.

| Metric | Value |
|---|---:|
| total parameters | **115,578,904** |
| AttnRes addition | 24,600 |
| relative overhead | approximately 0.0213% |
| FP32 weight bytes | 462,315,616 |
| BF16 weight bytes | 231,157,808 |

These are source-derived static counts. D002 must verify them by model instantiation and persist the exact parameter-name diff.

## Blocking findings

### D001-F1 — preregistered global batch is not implemented

C001 fixes 64 sequences per optimizer step. The candidate parser exposes `--batch_size`, but the training loop never uses it: each rank receives one sequence for each microstep. With 8 ranks and the default `grad_accum=2`, the realized global batch is:

`1 sequence × 8 ranks × 2 accumulation steps = 16 sequences`

not 64.

Consequences:

- nominal token budgets are incorrect;
- optimizer-step and warmup comparisons are altered;
- throughput accounting is inconsistent with C001;
- the README-like command cannot be used as the registered smoke command.

### D001-F2 — C001 S0 command is not executable

`train_scratch.py` unconditionally:

- initializes `torch.distributed` with NCCL;
- selects a CUDA device;
- wraps the model in DDP.

Therefore the registered plain `python train_scratch.py ...` preflight cannot run as written. A one-process `torchrun` still requires CUDA/NCCL and does not provide the intended CPU-capable save/load preflight.

### D001-F3 — token-stream equality is not established

The candidate loads FineWeb-Edu using unpinned streaming input, then applies:

- per-rank shuffle with `seed + rank`;
- `skip(rank)` at the example level;
- local token buffering;
- `world_size * seq_len` buffer advancement.

This does not establish an immutable, disjoint, byte-identical token stream for B0 and A1. The central C001 fairness condition is therefore unmet.

### D001-F4 — dependency environment is not reproducible

`requirements.txt` contains only broad lower bounds or unpinned package names. The implementation imports Qwen3 internals and several version-sensitive Transformers APIs. A clean environment may resolve to a behaviorally different stack.

### D001-F5 — required resource evidence is absent

The candidate logs aggregate training loss, gradient norm and tokens/sec, but does not persist the complete C001 contract:

- peak RSS;
- peak VRAM;
- model bytes;
- package and hardware versions;
- raw checksums;
- CPU prefill/decode latency;
- AttnRes gradient presence;
- routing entropy and collapse diagnostics.

An external measurement harness is required before smoke training.

### D001-F6 — residual-only difference remains statically plausible, not proven

The intended A1 configuration is:

- `mode=block`;
- `gate_type=bias`;
- `attnres_recency_bias_init=0`;
- no null source;
- four blocks.

The source reuses Qwen3 attention and MLP components, and adds two routing queries, two routing RMSNorms and two scalar biases per layer. This is consistent with the intended residual-path-only ablation, but runtime/config equivalence outside the AttnRes fields has not yet been proven.

## Gate decision

| Stage | Decision |
|---|---|
| S0 finite forward/backward/save-load | not passed |
| S1 B0 seed-17 smoke | prohibited |
| S1 A1 seed-17 smoke | prohibited |
| S2 pilot | prohibited |
| S3 three-seed full comparison | prohibited |

This is not a negative result for Block AttnRes. It is a reproduction-contract failure in the candidate entry point.

## D002 — next minimum action

Create a non-training preflight harness that:

1. resolves one exact package environment;
2. instantiates B0 and A1 from one common configuration;
3. writes serialized config and parameter-name diffs;
4. verifies the static counts above;
5. generates one fixed synthetic token tensor and records its SHA256;
6. runs one finite forward/backward optimizer step for each condition;
7. verifies nonzero finite gradients on all AttnRes routing parameters;
8. saves and reloads both models;
9. verifies post-load logits against the pre-save logits within a preregistered tolerance;
10. records process RSS, CUDA memory when available, wall time and environment metadata.

It must not download FineWeb-Edu or start S1. This keeps the next run small, executable and causally interpretable.

## Handoff

### C

C001 requires amendment because the registered global batch and S0 command do not match the candidate implementation. The experiment target itself does not change.

### E

Keep Block AttnRes at **追加検証・未採用**. Do not authorize S1/S2 until D002 passes and an immutable dataset/token manifest exists.

### B

The exact static weight overhead is now fixed at 24,600 parameters. CPU roofline refinement still requires D002/S1 traces; parameter overhead alone cannot establish a CPU Pareto improvement.
