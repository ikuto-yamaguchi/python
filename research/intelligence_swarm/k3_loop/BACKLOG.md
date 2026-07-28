# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-28 by K3-D

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
- [x] Consume D001 static parameter overhead: A1 adds exactly 24,600 source-derived parameters.
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
- [ ] Amend C001 S0 invocation: candidate requires distributed CUDA/NCCL and the plain-Python command is not executable.
- [ ] Amend C001 global batch realization: candidate ignores `--batch_size`; 8 ranks × grad_accum 2 realizes 16, not 64, sequences/step.
- [ ] Amend only these executable-contract defects; do not open a second candidate.

### D — Reproduction: current priority

- [x] Pin candidate commit and audited source blob SHAs.
- [x] Complete D001 static CLI/data/model contract audit.
- [x] Derive source-level B0/A1 parameter and static weight-byte counts.
- [x] Record why the current entry point cannot satisfy S0/S1.
- [ ] Create D002 non-training preflight harness with no FineWeb-Edu access.
- [ ] Pin Python/PyTorch/Transformers/Datasets/CUDA dependency environment.
- [ ] Generate fixed synthetic token input and SHA256.
- [ ] Instantiate B0/A1 and verify exact parameter counts and parameter-name diff.
- [ ] Generate serialized B0/A1 config diff proving only AttnRes fields differ.
- [ ] Run one finite forward/backward optimizer step for both conditions.
- [ ] Verify all routing parameters receive finite nonzero gradients.
- [ ] Run save-load and post-load logits equivalence check.
- [ ] Record peak RSS/VRAM, wall time, raw logs, environment and checksums.
- [ ] Resolve and hash tokenizer snapshot.
- [ ] Replace ambiguous streaming input with immutable shard/token manifest, or prove resolved streaming shards are fixed.
- [ ] Run B0 seed-17 100-step smoke only after D002 and data gates pass.
- [ ] Run A1 seed-17 smoke only after B0 passes.
- [ ] Verify routing entropy and non-collapse diagnostics during smoke.
- [ ] Do not start S2/S3 without E gate.

### E — Integration

- [ ] Review D001 preflight evidence and keep status at `追加検証・未採用`.
- [ ] Deny S1 until D002, C001 executable-contract amendment and immutable tokenizer/data gates pass.
- [ ] Review later smoke evidence and authorize or deny paired S2 pilot.
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
- No silent patching of candidate code; every patch must have a documented purpose, diff and checksum.
