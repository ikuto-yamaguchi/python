# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-28 by K3-D

## P0 — Current cycle: Block AttnRes minimum reproduction

### A — Evidence

- [x] Confirm author-controlled executable implementation/checkpoint status. None found as of 2026-07-28.
- [x] Extract primary-report model sizes, depths, widths, block counts and token budgets.
- [x] Pin unofficial candidate `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`.
- [x] Record A001 evidence audit.
- [ ] Record paper-to-candidate deviation matrix before S2.
- [x] Keep other K3 components frozen while P0 is unresolved.

### B — Theory

- [x] Complete parameter/FLOPs/state-memory/communication/sequence/quantization/CPU comparison.
- [x] Record small-scale counterexample and failure conditions.
- [x] Prepare B002 CPU roofline/operator trace contract.
- [x] Consume D002 corrected parameter delta: `25,625`, including final router.
- [ ] Recompute effective traffic/operator shares from D002 raw routing traces.
- [ ] Do not claim a CPU crossover until fresh-process paired timing and isolated RSS exist.

### C — Preregistration

- [x] Pin 12-layer d=512 dense PreNorm baseline.
- [x] Specify Block AttnRes `N=4` as the only architectural change.
- [x] Fix optimizer, schedule, sequence length, token budgets and seeds `17/29/43`.
- [x] Define equal-token, near-equal-parameter and measured-active-compute comparisons.
- [x] Add C001 preregistration and manifest.
- [ ] Correct A1 parameter count from `115,578,904` to `115,579,929`.
- [ ] Correct AttnRes delta from `24,600` to `25,625`.
- [ ] Add standalone D002/D003 invocation and explicit save-load tolerance.
- [ ] Add machine-readable PASS/WARN/STOP schema.
- [ ] Add B002 operator-attribution fields and fixed CPU cases.
- [ ] Amend later S1 global batch realization to explicit 64 sequences/step.
- [ ] Preserve all model/data/optimizer/schedule/single-change constraints.
- [ ] Do not authorize S1 in the amendment.

### D — Reproduction

- [x] D001 static CLI/data/model contract audit.
- [x] D002 standalone parameter-faithful preflight harness created and executed.
- [x] Fixed synthetic input generated from seed 17.
- [x] B0 instantiated at `115,554,304` parameters.
- [x] A1 instantiated at corrected `115,579,929` parameters.
- [x] Parameter-name diff proved routing-only in the standalone harness.
- [x] Finite forward/backward completed for B0/A1.
- [x] All 75 routing parameter tensors received finite nonzero gradients.
- [x] Save/load output equality passed with max absolute difference `0.0`.
- [x] Routing source shape/stride/contiguity/dtype and operator timing persisted.
- [x] Machine-readable D002 summary added.
- [x] D002 classified `Path-WARN`: executability passed, adoption/training not authorized.
- [ ] Persist exact full 53KB raw result externally or regenerate from committed harness; committed summary/checksums currently preserve the evidence digest.
- [ ] Obtain a pinned runtime with the candidate's exact `transformers` dependency.
- [ ] Run D003 in fresh processes with alternating B0/A1 order after warm-up.
- [ ] Isolate RSS per condition.
- [ ] Add no-op/list traversal/stack-only/norm+score/softmax/mix controls.
- [ ] Do not download FineWeb-Edu or start S1 before E review and C amendment.
- [ ] Resolve tokenizer and immutable token manifests only after explicit authorization.

### E — Integration

- [x] E001 locked D002 as the only bottleneck.
- [ ] Review D002 as Path-WARN versus implementation-path STOP.
- [ ] Decide whether D003 exact-dependency fresh-process preflight is required.
- [ ] Keep Block AttnRes at `追加検証・未採用` unless later preregistered quality/resource evidence passes.
- [ ] Keep KDA, Stable LatentMoE and other candidates frozen until this decision.

## D002 evidence summary

- Corrected parameter overhead: `25,625` (`~0.02218%`).
- FP32 bytes: B0 `462,217,216`; A1 `462,319,716`.
- Process max RSS: `2,203,936 KiB` across sequential run and serialization; not isolated.
- Routing median time, five sources, width 512, one CPU thread:
  - seq 1: `0.112 ms`
  - seq 128: `0.628 ms`
  - seq 512: `2.252 ms`
  - seq 2048: `35.944 ms`
- Full-model timing is order-contaminated and must not be used for Pareto judgment.
- No quality, training throughput, generation, quantization or 3-seed evidence exists.

## P1 — Candidate queue after P0

1. Kimi Delta Attention
2. Stable LatentMoE
3. MXFP4-aware training
4. Low-rank Attention Residuals
5. Data curriculum/post-training efficiency

P1 remains frozen.

## Global prohibitions

- No new architecture before reproducible baseline and preregistration.
- No simultaneous multi-component K3 transplant.
- No claims of intelligence principle, high-school-level capability or capability progress without evidence.
- No adoption based only on parameter count or GPU FLOPs; CPU wall time and RSS are mandatory.
- No success report from one seed.
- No post-hoc promotion of preflight or smoke runs to full evidence.
- No silent patching; every patch requires purpose, diff and checksum.
- No replacing the current bottleneck with literature review or another candidate because execution is inconvenient.
