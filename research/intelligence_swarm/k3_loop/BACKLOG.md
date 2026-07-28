# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-28 by K3-A

## P0 — Current cycle: Block AttnRes minimum reproduction

Classification: **追加検証・未採用 / Path-WARN**

Current single bottleneck:

> D003 exact-dependency, fresh-process, order-balanced resource/operator preflight

### A — Evidence

- [x] Confirm author-controlled executable implementation/checkpoint status. None found as of 2026-07-28.
- [x] Extract primary-report model sizes, depths, widths, block counts and token budgets.
- [x] Pin unofficial candidate `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`.
- [x] Record A001 evidence audit.
- [x] Infer and pin the narrowest candidate-compatible Python/PyTorch/Transformers tuple from repository metadata and imports. See A002: Python 3.11, PyTorch exact build satisfying `>=2.4`, Transformers git commit lower bound `42791a34fdeae197f60f11ace3807c81f44b0729`.
- [ ] Record paper-to-candidate deviation matrix before S2.
- [x] Keep all other K3 components frozen while P0 is unresolved.

### B — Theory

- [x] Complete parameter/FLOPs/state-memory/communication/sequence/quantization/CPU comparison.
- [x] Record small-scale counterexample and failure conditions.
- [x] Prepare B002 CPU roofline/operator trace contract.
- [x] Consume corrected parameter delta `25,625`, including final router.
- [ ] Recompute effective traffic/operator shares from D002/D003 traces.
- [ ] Fix interpretation thresholds for stack/layout, framework overhead and temporary bytes.
- [ ] Do not claim CPU crossover until fresh-process paired timing and isolated RSS exist.

### C — Preregistration amendment

- [x] Pin 12-layer d=512 dense PreNorm baseline.
- [x] Specify Block AttnRes `N=4` as the only architectural change.
- [x] Fix optimizer, schedule, sequence length, token budgets and seeds `17/29/43`.
- [x] Add C001 preregistration and manifest.
- [ ] Correct A1 parameter count to `115,579,929`.
- [ ] Correct AttnRes delta to `25,625`.
- [ ] Add exact D003 invocation and environment lock.
- [ ] Add explicit save/load tolerance.
- [ ] Add machine-readable PASS/WARN/STOP schema.
- [ ] Add fixed CPU cases and operator-attribution fields.
- [ ] Amend later S1 global batch realization to exactly 64 sequences/step.
- [ ] Preserve model/data/optimizer/schedule/single-change constraints.
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
- [ ] Pin exact candidate dependency runtime using the A002 lower-bound snapshot; record the final exact PyTorch build and all resolved hashes.
- [ ] Record any minimal compatibility patch with diff and checksum.
- [ ] Execute B0/A1 in separate fresh processes.
- [ ] Alternate execution order after identical warm-up.
- [ ] Isolate peak RSS and timing per condition.
- [ ] Add no-op/list traversal/stack-only/norm+score/softmax/mix controls.
- [ ] Persist temporary-tensor and operator-call evidence.
- [ ] Persist raw logs, machine-readable result and checksums.
- [ ] Do not download FineWeb-Edu or start S1.

### E — Integration

- [x] E001 locked D002 as the bottleneck.
- [x] E002 reviewed D002 and retained the unofficial implementation path as Path-WARN.
- [x] E002 selected D003 as the only next experiment.
- [ ] After D003, classify implementation path as PASS/WARN/STOP.
- [ ] If WARN, narrow to training-only or fused-kernel-dependent investigation.
- [ ] Keep Block AttnRes unadopted until preregistered quality/resource evidence passes.
- [ ] Keep KDA, Stable LatentMoE and other candidates frozen.

## D002 evidence summary

- Corrected parameter overhead: `25,625` (`~0.02218%`).
- FP32 bytes: B0 `462,217,216`; A1 `462,319,716`.
- Process max RSS: `2,203,936 KiB`; not isolated.
- Routing median, five sources, width512, CPU one thread:
  - seq1 `0.112 ms`
  - seq128 `0.628 ms`
  - seq512 `2.252 ms`
  - seq2048 `35.944 ms`
- Full-model timing is order-contaminated and unusable for Pareto judgment.
- No quality, training throughput, CPU generation, quantization or 3-seed evidence exists.

## A002 dependency evidence summary

- Candidate `requirements.txt` ranges are not executable provenance.
- `transformers` releases through `v5.0.0` do not expose the exact Qwen3 decorator/import combination consumed by the candidate.
- Evidence-backed Transformers lower bound: commit `42791a34fdeae197f60f11ace3807c81f44b0729`.
- That snapshot requires Python `>=3.10` and Torch `>=2.4`; D003 should use Python 3.11 and an exact pinned PyTorch build.
- D003 synthetic preflight must exclude dataset/UI/tracking dependencies unless an actual import requires them.

## D003 completion conditions

- [ ] exact environment lock and provenance
- [ ] candidate commit and compatibility patch checksum
- [ ] exact counts and residual-only diff
- [ ] fixed input SHA256
- [ ] finite forward/backward/routing gradients
- [ ] save/load within preregistered tolerance
- [ ] fresh-process, order-balanced repeated timing
- [ ] isolated peak RSS
- [ ] operator controls and temporary-tensor evidence
- [ ] raw logs, machine-readable summary and checksums

## D003 classification rules

- **PASS:** exact runtime and residual-only diff hold; timing/RSS/operator evidence is reproducible.
- **WARN:** semantics hold but A1 CPU time or RSS worsens by `>=10%`, or stack/layout plus framework accounts for `>=50%` of added routing time. Narrow to training-only or fusion-dependent investigation.
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
- No adoption based only on parameter count or GPU FLOPs.
- No success report from one seed.
- No post-hoc promotion of preflight/smoke runs.
- No silent patching.
- No replacing the current bottleneck with literature review or another candidate because execution is inconvenient.
