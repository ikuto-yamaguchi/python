# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-28 by K3-E

## P0 — Current cycle: Block AttnRes minimum reproduction

### A — Evidence

- [ ] Confirm whether any author-controlled executable implementation/checkpoint exists beyond `MoonshotAI/Attention-Residuals` documentation.
- [ ] Extract exact primary-report Block AttnRes model sizes, depths, widths, block counts, token budgets and compute budgets required to compare C001.
- [x] Pin one unofficial implementation commit as a reproduction candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`.
- [ ] Record an evidence delta in `evidence/`, explicitly including negative findings such as absence of executable author code.
- [ ] Record all candidate-code deviations from the paper before S2.
- [ ] Do not audit another K3 component or Low-Rank AttnRes until P0 passes or stops.

### B — Theory

- [x] Complete parameter/FLOPs/state-memory/communication/sequence/quantization/CPU comparison.
- [x] Record small-scale counterexample and failure conditions.
- [x] Consume D001 static parameter overhead: A1 adds exactly 24,600 source-derived parameters.
- [ ] Prepare trace fields and equations for eager memory-traffic and CPU roofline analysis.
- [ ] Refine CPU roofline only after D002 supplies exact dtype/layout/timing traces.
- [ ] Determine whether activation reads, stack/einsum/softmax, or framework launch overhead dominates; do not infer from parameter count alone.

### C — Preregistration

- [x] Pin 12-layer d=512 dense PreNorm baseline candidate.
- [x] Specify Block AttnRes `N=4` as the only architectural change.
- [x] Fix optimizer, schedule, sequence length, token budgets and seeds `17/29/43`.
- [x] Define equal-token, near-equal-parameter and measured-active-compute comparisons.
- [x] Define routing, CPU, RSS/VRAM and quantization measurements.
- [x] Add preregistration `prereg/C001_BLOCK_ATTNRES_100M_PREREG.md`.
- [x] Add executable manifest `benchmarks/k3_minimal/manifests/C001_block_attnres_100m.yaml`.
- [ ] Amend C001 S0/D002 invocation to use a standalone non-training harness rather than the unconditional NCCL/DDP entry point.
- [ ] Add explicit save-load tolerance and machine-readable D002 PASS/FAIL schema.
- [ ] Amend C001 global batch realization: the candidate ignores `--batch_size`; later S1 must explicitly realize 64 sequences/step.
- [ ] Preserve model, optimizer, sequence length, token budgets, seeds and single-change ablation while making these amendments.
- [ ] Do not authorize S1 in the amendment.

### D — Reproduction: sole current priority

- [x] Pin candidate commit and audited source blob SHAs.
- [x] Complete D001 static CLI/data/model contract audit.
- [x] Derive source-level B0/A1 parameter and static weight-byte counts.
- [x] Record why the current entry point cannot satisfy S0/S1.
- [ ] Create D002 standalone non-training preflight harness with no FineWeb-Edu access.
- [ ] Pin exact Python/PyTorch/Transformers and CUDA/CPU environment.
- [ ] Generate fixed synthetic token input and SHA256.
- [ ] Instantiate B0/A1 and verify exact parameter counts and parameter-name diff.
- [ ] Generate serialized B0/A1 config diff proving only AttnRes fields differ.
- [ ] Run one finite forward/backward optimizer step for both conditions.
- [ ] Verify every routing parameter receives finite nonzero gradient.
- [ ] Run save-load and verify post-load logits under the declared tolerance.
- [ ] Record peak RSS/VRAM and wall time.
- [ ] Persist raw logs plus code/config/input/output/environment checksums.
- [ ] Write machine-readable D002 PASS/FAIL result under `benchmarks/k3_minimal/preflight/`.
- [ ] If compatibility repair is necessary, persist exact patch diff and resulting source checksum before execution.
- [ ] Stop this implementation path after one documented minimal repair if D002 requires a semantic/model architecture change or cannot satisfy the gate.
- [ ] Resolve and hash tokenizer snapshot only after D002 PASS.
- [ ] Replace ambiguous streaming input with immutable shard/token manifest, or prove resolved streaming shards are fixed, only after D002 PASS.
- [ ] Run B0 seed-17 100-step smoke only after E authorizes corrected S1.
- [ ] Run A1 seed-17 smoke only after B0 passes.
- [ ] Verify routing entropy and non-collapse diagnostics during smoke.
- [ ] Do not start S2/S3 without E gate.

### E — Integration

- [x] Complete E001 review of D001 evidence.
- [x] Keep Block AttnRes at `追加検証・未採用`.
- [x] Deny S1/S2/S3 until D002, C001 executable-contract amendment and immutable tokenizer/data gates pass.
- [x] Lock D002 as the only next-cycle hypothesis; prohibit opening KDA, Stable LatentMoE or another architecture candidate.
- [x] Define binary next review: D002 PASS or implementation-path STOP.
- [x] Define that failure of the unofficial implementation path does not by itself reject the AttnRes research hypothesis.
- [ ] Review D002 output and either authorize immutable-data/S1 preparation or stop the current implementation path.
- [ ] Review later smoke evidence and authorize or deny paired S2 pilot.
- [ ] Keep `採用 / 追加検証 / 狭義化 / 棄却` based on preregistered Pareto thresholds.

## P1 — Candidate queue after P0

1. Kimi Delta Attention: recurrent state size, stability, short-context overhead and CPU kernels.
2. Stable LatentMoE: routing overhead and total-weight memory under sub-1GB constraints.
3. MXFP4-aware training: separate hardware throughput benefit from quality benefit and CPU portability.
4. Attention Residuals low-rank routing: only after original Block AttnRes baseline.
5. Data curriculum/post-training efficiency: only with a fixed architecture baseline.

P1 remains frozen while D002 is unresolved.

## Global prohibitions

- No new architecture before reproducible baseline and preregistration.
- No simultaneous multi-component K3 transplant.
- No claims of intelligence principle, high-school-level capability or capability progress without evidence.
- No adoption based only on parameter count or GPU FLOPs; CPU wall time and RSS are mandatory.
- No success report from one seed.
- No post-hoc promotion of S1/S2 to full evidence.
- No silent patching of candidate code; every patch must have a documented purpose, diff and checksum.
- No replacement of the current bottleneck with literature review or a new candidate merely because execution is inconvenient.
