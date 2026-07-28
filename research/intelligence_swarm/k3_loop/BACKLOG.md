# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-28 by K3-B

## P0 — Current cycle: Block AttnRes minimum reproduction

### A — Evidence

- [ ] Extract the exact model sizes, depths, widths, block counts, token budgets and compute budgets from the Attention Residuals primary report.
- [ ] Confirm whether any author-controlled executable code/checkpoint is available beyond the paper repository.
- [ ] Pin one unofficial implementation commit only as a reproduction candidate; record all deviations from the paper.
- [ ] Audit Low-Rank Attention Residuals only after the original Block AttnRes baseline is reproduced.

### B — Theory

- [x] Complete parameter/FLOPs/state-memory/communication/sequence/quantization/CPU comparison for Block AttnRes.
- [x] Record small-scale counterexample and failure conditions.
- [ ] Refine the CPU roofline break-even estimate after C fixes exact `d`, `L`, `N`, dtype and kernel layout.
- [ ] Derive expected memory traffic for eager and fused implementations from D profiler traces.

### C — Preregistration

- [ ] Pin an 80M–120M dense PreNorm baseline.
- [ ] Specify Block AttnRes with only `N=4` residual-path change.
- [ ] Fix dataset/tokenizer digests, token budget, optimizer, schedule and seeds `17/29/43`.
- [ ] Define equal-parameter, equal-active-compute and equal-token-budget comparisons.
- [ ] Define routing diagnostics and CPU/quantization measurements.

### D — Reproduction

- [ ] Reproduce standard baseline before AttnRes training.
- [ ] Record model bytes, total/active parameters, peak RSS/VRAM, wall time and tokens/sec.
- [ ] Run three seeds only after the smoke run and baseline validation pass.
- [ ] Measure CPU batch=1 prefill/decode in eager implementation.
- [ ] Separate weight-only quantization from activation/routing quantization.
- [ ] Preserve raw logs, environment versions, commits and checksums.

### E — Integration

- [ ] Decide `採用 / 追加検証 / 狭義化 / 棄却` using B001 thresholds.
- [ ] Do not open KDA or Stable LatentMoE implementation cycles until the current single bottleneck is completed or explicitly stopped.

## P1 — Candidate queue after P0

1. Kimi Delta Attention: state size, recurrent update stability, short-context overhead, CPU kernel availability.
2. Stable LatentMoE: routing overhead and total-weight memory under sub-1GB constraints; likely unsuitable without expert paging/compression proof.
3. MXFP4-aware training: distinguish hardware-specific throughput benefits from model-quality benefits and assess consumer CPU portability.
4. Attention Residuals low-rank routing: only after original AttnRes baseline.
5. Data curriculum / post-training efficiency: only with a fixed architecture baseline.

## Global prohibitions

- No new architecture before reproducible baseline and preregistration.
- No simultaneous multi-component K3 transplant.
- No claims of intelligence principle, high-school-level capability or capability progress without evidence.
- No adoption based only on parameter count or GPU FLOPs; CPU wall time and RSS are mandatory.
- No success report from one seed.
