# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-28 by K3-C

## P0 — Current cycle: Block AttnRes minimum reproduction

### A — Evidence

- [ ] Extract exact primary-report model sizes, depths, widths, block counts, token and compute budgets.
- [ ] Confirm whether any author-controlled executable code/checkpoint exists beyond the paper repository.
- [x] Pin one unofficial implementation commit as a reproduction candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`.
- [ ] Record all candidate-code deviations from the paper before S2.
- [ ] Audit Low-Rank Attention Residuals only after original Block AttnRes reproduction.

### B — Theory

- [x] Complete parameter/FLOPs/state-memory/communication/sequence/quantization/CPU comparison.
- [x] Record small-scale counterexample and failure conditions.
- [ ] Refine CPU roofline after D fixes exact dtype, source layout and profiler trace.
- [ ] Derive eager/fused memory traffic from D traces.

### C — Preregistration

- [x] Pin 12-layer d=512 dense PreNorm baseline candidate.
- [x] Specify Block AttnRes `N=4` as the only architectural change.
- [x] Fix optimizer, schedule, sequence length, token budgets and seeds `17/29/43`.
- [x] Define equal-token, near-equal-parameter and measured-active-compute comparisons.
- [x] Define routing, CPU, RSS/VRAM and quantization measurements.
- [x] Add preregistration `prereg/C001_BLOCK_ATTNRES_100M_PREREG.md`.
- [x] Add executable manifest `benchmarks/k3_minimal/manifests/C001_block_attnres_100m.yaml`.
- [ ] Amend only if D identifies an executable-contract defect; do not open a second candidate.

### D — Reproduction: current priority

- [ ] Checkout pinned candidate commit and record clean/dirty state.
- [ ] Pin Python/PyTorch/Transformers/Datasets/CUDA dependency environment.
- [ ] Resolve and hash tokenizer snapshot.
- [ ] Replace ambiguous streaming input with immutable shard/token manifest, or prove resolved streaming shards are fixed.
- [ ] Generate exact B0/A1 config diff and parameter counts.
- [ ] Run S0 one-step forward/backward/save-load validation.
- [ ] Run B0 seed-17 100-step smoke with model bytes, RSS/VRAM, wall time and tokens/sec.
- [ ] Run A1 seed-17 smoke only after B0 passes.
- [ ] Verify routing gradients and non-collapse diagnostics.
- [ ] Do not start S2/S3 without E gate.

### E — Integration

- [ ] Review D preflight and smoke evidence.
- [ ] Authorize or deny paired S2 pilot.
- [ ] Keep `採用 / 追加検証 / 狭義化 / 棄却` based on preregistered Pareto thresholds.
- [ ] Do not open KDA or Stable LatentMoE until P0 is completed or explicitly stopped.

## P1 — Candidate queue after P0

1. Kimi Delta Attention: recurrent state size, stability, short-context overhead and CPU kernels.
2. Stable LatentMoE: routing overhead and total-weight memory under sub-1GB constraints.
3. MXFP4-aware training: separate hardware throughput benefit from quality benefit and CPU portability.
4. Attention Residuals low-rank routing: only after original Block AttnRes baseline.
5. Data curriculum/post-training efficiency: only with a fixed architecture baseline.

## Global prohibitions

- No new architecture before reproducible baseline and preregistration.
- No simultaneous multi-component K3 transplant.
- No claims of intelligence principle, high-school-level capability or capability progress without evidence.
- No adoption based only on parameter count or GPU FLOPs; CPU wall time and RSS are mandatory.
- No success report from one seed.
- No post-hoc promotion of S1/S2 to full evidence.
