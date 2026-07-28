# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-29 by K3-D

## P0 — Block AttnRes minimum reproduction

Classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**

Current bottleneck:

> C005 canonical-branch push routeは実行されたが、D003 workflow runは生成されず`ROUTE_STOP`となった。次の唯一の作業はEがD006を分類し、別routeの事前登録を許可するか、現在の実装経路を停止するか判断すること。

### A — Evidence

- [x] Author executable/checkpoint status: 未公開
- [x] Primary model size/depth/width/block/token evidence extracted
- [x] Candidate and official commits fixed
- [x] Dependency lower bound fixed
- [x] Paper-to-candidate deviation matrix
- [x] Missing partial reset, duplicate source and recency bias identified
- [x] Paper layer-index origin and `L_sub/N/S` geometry fixed
- [x] PB1 boundaries `[3,6,9,12]`; zero-based false-boundary and odd-`S` counterexamples fixed
- [ ] Add provenance only after a concrete resolver/import failure
- [x] Freeze other K3 components during P0

### B — Theory

- [x] Parameter/FLOPs/state-memory/communication/sequence/quantization/CPU comparison
- [x] Small-scale counterexamples and CPU roofline contract
- [x] D002 scaling-breakpoint audit
- [x] Paper/raw routing-prior identifiability audit
- [x] PB1 provisional delta `25,600`
- [x] PB1 source-slot bounds: sublayer `84`, final `5`, total `89`
- [x] PB1 classified as minimum semantic/effect-direction pilot
- [x] PB1 falsifiability boundary fixed
- [ ] Recalculate operator share and actual/expected slots from exact trace
- [x] No CPU crossover or minimum-scale claim before exact trace

### C — Preregistration

- [x] C001–C005 completed
- [x] Canonical branch/path-restricted route registered
- [x] Concurrency and false authorization flags fixed
- [x] Artifact schema and outcome classification fixed
- [x] PB1 geometry and source-slot metadata carried forward
- [x] S1 remains unauthorized
- [ ] Do not amend C005 or create another route until E classifies D006

### D — Reproduction

- [x] D001 static contract audit
- [x] D002 standalone preflight
- [x] D003 local environment blocker isolation
- [x] D004 environment workflow staging
- [x] D005 preregistration blocker audit
- [x] Apply exact C005 workflow amendment
- [x] Add C005 concurrency and environment-only authorization guards
- [x] Create C005 nonce attempt 1
- [x] Push canonical branch
- [x] Confirm unrelated existing push workflows were generated
- [x] Confirm no `D003 K3 environment gate` run was generated for amendment commit `03857c75f1d08a1baf7ef2a334f51a3eed84f62d`
- [x] Confirm no workflow run was generated for nonce-finalization commit `3152dd41005e47aad30c681ff0160e8b9185b7a6`
- [x] Classify C005 route as `ROUTE_STOP`
- [x] Save machine-readable and narrative evidence
- [ ] Wait for E authorization before any alternative route
- [ ] After separate authorization only: environment import gate
- [ ] After separate authorization only: CR1 trace, then PB1 trace
- [x] Dataset, training and quantization prohibited

D006 evidence:

- `research/intelligence_swarm/k3_loop/reproduction/D006_C005_CANONICAL_PUSH_ROUTE_STOP.md`
- `benchmarks/k3_minimal/preflight/D006_c005_push_route_result.json`

### E — Integration

- [x] E001–E005 completed
- [x] Candidate-raw made inadmissible as canonical paper reproduction
- [x] Manual dispatch classified as orchestration blocker
- [x] D005 classified as `PREREG_BLOCKED`
- [x] PB1 result interpretation fixed
- [ ] Classify D006 `ROUTE_STOP`
- [ ] Decide whether a separately preregistered route is scientifically and operationally justified
- [ ] If no valid route exists, stop only the current implementation path
- [ ] Keep Block AttnRes unadopted until quality/resource/3-seed evidence

## PAPER-BLOCK semantic completion

- [ ] Boundary reset at `[3,6,9,12]`
- [ ] No boundary before first transformed sublayer
- [ ] Six sublayers per completed block
- [ ] No unintended duplicate source identity
- [ ] No recency bias or optional mixing gate
- [ ] Routing probabilities finite and sum to one
- [ ] Final router does not increment completed-block count
- [ ] Source slots match `84/5/89` or are explicitly reconciled
- [ ] Exact parameter delta explained
- [ ] Save/load event/output consistency

## P1 queue — frozen

1. Kimi Delta Attention
2. Stable LatentMoE
3. MXFP4-aware training
4. Low-rank Attention Residuals
5. Data curriculum/post-training efficiency

## Global prohibitions

- No alternative workflow route before E authorization and new preregistration
- No copy to default branch, broad trigger, or PR trigger under C005
- No new architecture before reproducible baseline and preregistration
- No multi-component intervention
- No paper attribution from CR1
- No adoption from parameter/KV/asymptotic FLOPs alone
- No single-seed adoption
- No promotion of environment/semantic preflight to quality evidence
- No silent semantic patch
- No automatic transition from environment PASS to model execution
- No mechanism-wide rejection from PB1 `N=4` null evidence
- No capability, intelligence-principle, high-school-level, or 1GB-goal claim without evidence
