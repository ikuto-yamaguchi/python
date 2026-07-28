# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-28 by K3-B

## P0 — Current cycle: Block AttnRes minimum reproduction

Classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**

Current single bottleneck:

> D003 exact-dependency, fresh-process, order-balanced resource/operator preflight

### A — Evidence

- [x] Confirm author-controlled executable implementation/checkpoint status. None found as of 2026-07-28.
- [x] Extract primary-report model sizes, depths, widths, block counts and token budgets.
- [x] Pin unofficial candidate `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`.
- [x] Record A001 evidence audit.
- [x] Pin dependency lower bound: Python 3.11, exact PyTorch satisfying `>=2.4`, Transformers `42791a34fdeae197f60f11ace3807c81f44b0729`.
- [ ] Record paper-to-candidate deviation matrix before S2.
- [x] Keep all other K3 components frozen while P0 is unresolved.

### B — Theory

- [x] Complete parameter/FLOPs/state-memory/communication/sequence/quantization/CPU comparison.
- [x] Record small-scale counterexample and failure conditions.
- [x] Prepare B002 CPU roofline/operator trace contract.
- [x] Consume corrected parameter delta `25,625`, including final router.
- [x] Complete B003 D002 scaling-breakpoint audit.
- [x] Fit T=1/128/512 routing model: `t≈0.100753+0.004197T ms/event`.
- [x] Record T=2048 actual/predicted ratio `≈4.13x` as an unresolved breakpoint candidate.
- [x] Define D003 hypotheses for stack/layout, allocator, kernel selection, softmax/layout and measurement artifact.
- [ ] Recompute fit, residual, operator shares and temporary-byte thresholds from D003 exact-runtime traces.
- [ ] Do not claim CPU crossover before fresh-process paired timing and isolated RSS exist.

### C — Preregistration amendment

- [x] Pin 12-layer d=512 dense PreNorm baseline.
- [x] Specify Block AttnRes `N=4` as the only architectural change.
- [x] Fix optimizer, schedule, sequence length, token budgets and seeds `17/29/43`.
- [x] Add C001 preregistration and manifest.
- [ ] Correct A1 parameter count to `115,579,929` and delta to `25,625`.
- [ ] Add exact D003 invocation and environment lock.
- [ ] Add explicit save/load tolerance.
- [ ] Add machine-readable PASS/WARN/STOP schema.
- [ ] Fix CPU cases `T=1,128,512,2048`.
- [ ] Require separate fresh processes and AB/BA order balance.
- [ ] Record warmup, repetitions, median, p95 and MAD.
- [ ] Add short-sequence linear fit and `actual_2048/predicted_2048` fields.
- [ ] Add operator attribution, temporary bytes and allocation fields.
- [ ] Amend later S1 global batch realization to exactly 64 sequences/step.
- [ ] Do not authorize S1 in the amendment.

### D — Reproduction

- [x] D001 static CLI/data/model contract audit.
- [x] D002 standalone parameter-faithful preflight executed.
- [x] Fixed synthetic input from seed 17.
- [x] B0=`115,554,304`, A1=`115,579,929`.
- [x] Routing-only parameter-name diff in standalone harness.
- [x] Finite forward/backward for B0/A1.
- [x] All 75 routing tensors received finite nonzero gradients.
- [x] Save/load max absolute difference `0.0`.
- [x] Routing trace and machine-readable D002 summary persisted.
- [x] E002 retained Path-WARN and authorized D003 only.
- [ ] Pin exact runtime using A002 snapshot and all resolved hashes.
- [ ] Record any minimal compatibility patch with diff/checksum.
- [ ] Execute B0/A1 in separate fresh processes with AB/BA order balance.
- [ ] Isolate peak RSS and timing per condition.
- [ ] Add no-op/list traversal/stack-only/norm+score/softmax/mix controls.
- [ ] Persist temporary tensor bytes, allocation counts and operator-call evidence.
- [ ] Recompute T<=512 fit and T=2048 breakpoint ratio in exact runtime.
- [ ] Persist raw logs, machine-readable result and checksums.
- [ ] Do not download FineWeb-Edu or start S1.

### E — Integration

- [x] E001 locked D002 as the bottleneck.
- [x] E002 reviewed D002 and retained Path-WARN.
- [x] E002 selected D003 as the only next experiment.
- [ ] After D003, classify implementation path as PASS/WARN/STOP.
- [ ] If `actual_2048/predicted_2048 >= 2.0` persists, or CPU/RSS overhead is `>=10%`, consider training-only/fusion-dependent narrowing.
- [ ] Keep Block AttnRes unadopted until preregistered quality/resource evidence passes.
- [ ] Keep KDA, Stable LatentMoE and other candidates frozen.

## D002 evidence summary

- Corrected parameter overhead: `25,625` (`~0.02218%`).
- FP32 bytes: B0 `462,217,216`; A1 `462,319,716`.
- Process max RSS: `2,203,936 KiB`; not isolated.
- Routing median, five sources, width512, CPU one thread:
  - T=1 `0.112487 ms`
  - T=128 `0.627961 ms`
  - T=512 `2.252197 ms`
  - T=2048 `35.944465 ms`
- T=1/128/512 fit predicts T=2048 at about `8.696 ms`; actual is about `4.13x` larger.
- Full-model timing is order-contaminated and unusable for Pareto judgment.
- No quality, training throughput, CPU generation, quantization or 3-seed evidence exists.

## D003 completion conditions

- [ ] exact environment lock and provenance
- [ ] candidate commit and compatibility patch checksum
- [ ] exact counts and residual-only diff
- [ ] fixed input SHA256
- [ ] finite forward/backward/routing gradients
- [ ] save/load within preregistered tolerance
- [ ] fresh-process AB/BA repeated timing
- [ ] isolated peak RSS
- [ ] operator controls and temporary/allocation evidence
- [ ] T=1/128/512 fit and T=2048 breakpoint ratio
- [ ] raw logs, machine-readable summary and checksums

## D003 classification rules

- **PASS:** exact runtime and residual-only diff hold; timing/RSS/operator evidence is reproducible; breakpoint disappears or is explained; A1/B0 full-model overhead is below 10%.
- **WARN:** semantics hold but A1 CPU time/RSS worsens by `>=10%`, stack/layout plus framework is `>=50%` of added routing time, or fresh-process `actual_2048/predicted_2048 >= 2.0`. Narrow to training-only or fusion-dependent investigation.
- **STOP:** after one documented minimal repair, execution remains impossible, residual-only equivalence breaks, gradient/save-load fails, measurements cannot be isolated, or semantic change is required.

## P1 — Candidate queue after P0

1. Kimi Delta Attention
2. Stable LatentMoE
3. MXFP4-aware training
4. Low-rank Attention Residuals
5. Data curriculum/post-training efficiency

P1 remains frozen.

## Global prohibitions

- No new architecture before reproducible baseline and preregistration.
- No simultaneous multi-component transplant.
- No claims of intelligence principle, high-school-level capability or capability progress without evidence.
- No adoption based only on parameter count, KV-cache behavior or asymptotic FLOPs.
- No success report from one seed.
- No post-hoc promotion of preflight/smoke runs.
- No silent patching.
- No replacing the current bottleneck with literature review or another candidate because execution is inconvenient.
