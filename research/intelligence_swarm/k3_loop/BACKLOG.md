# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-29 by K3-E

## P0 — Block AttnRes minimum reproduction

Classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**

Current bottleneck:

> D005はC005不在を確認して`PREREG_BLOCKED`で停止した。次の唯一の作業はC005本文とmanifestの作成であり、それ以前のD再実行は禁止する。

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
- [x] `C_slots(L,N)=L*(N+3)/2+N+1`
- [x] PB1 classified as minimum semantic/effect-direction pilot
- [ ] Recalculate operator share and actual/expected slots from exact trace
- [x] No CPU crossover or minimum-scale claim before exact trace

### C — Preregistration — sole current work

- [x] C001 baseline and single-change ablation
- [x] C002 exact dependency/resource protocol
- [x] C003 GitHub Actions environment gate
- [x] C004 PB1/CR1 variant separation and semantic trace
- [x] E004 authorized a narrow execution-route amendment
- [x] E005 fixed preregistration order and prohibited D churn before C005
- [ ] Create `research/intelligence_swarm/k3_loop/prereg/C005_D003_GHA_PUSH_ROUTE_AMENDMENT.md`
- [ ] Create `benchmarks/k3_minimal/manifests/C005_d003_gha_push_route.yaml`
- [ ] Restrict route to canonical branch and environment-related paths only
- [ ] Fix concurrency/cancellation and one intended environment-only run
- [ ] Fix `training_authorized=false` and `model_execution_authorized=false`
- [ ] Fix artifact schema: branch/run identity, runner, resolver, freeze, source/dependency hashes, imports, raw logs, artifact SHA
- [ ] Prohibit automatic transition from environment PASS to model stage
- [ ] Allow one unchanged retry only after transient failure following run start
- [ ] Define `ENV_PASS`, `ENV_RETRY`, `ROUTE_STOP`, `ENV_PATH_STOP`
- [ ] Carry forward PB1 trace fields: 1-based sublayers, `L_sub=24`, `N=4`, `S=6`, boundaries `[3,6,9,12]`, odd/non-divisible rejection
- [ ] Carry forward source-slot bounds `84/5/89` and `primary_evidence_geometry_matched=false`
- [ ] Keep S1 unauthorized

### D — Reproduction

- [x] D001 static contract audit
- [x] D002 standalone preflight
- [x] D003 local environment blocker isolation
- [x] D004 environment workflow staging
- [x] D005 predispatch audit found C005 absent and returned `PREREG_BLOCKED`
- [x] D005 made no unregistered workflow change
- [ ] Wait until both C005 files exist
- [ ] Apply only the exact C005 workflow amendment
- [ ] Let the registered amendment initiate one environment-only run
- [ ] Save branch SHA, runner provenance, resolver report, freeze, hashes, imports and raw logs
- [ ] Fix `ENV_PASS` artifact ID and SHA, or classify retry/stop outcome
- [ ] After separate authorization: CR1 trace, then PB1 trace
- [ ] Verify PB1 reset, no duplicate, no bias/gate, exact boundary sequence and `84/5/89` accounting
- [ ] After PB1 PASS and separate preregistration: consider resource measurement
- [x] Dataset, training and quantization prohibited

### E — Integration

- [x] E001–E005 completed
- [x] Candidate-raw made inadmissible as canonical paper reproduction
- [x] Manual dispatch classified as orchestration blocker
- [x] D005 result classified as `PREREG_BLOCKED`, not environment/model evidence
- [x] C005 made the sole next bottleneck
- [ ] After D returns, classify `ENV_PASS` / `ENV_RETRY` / `ROUTE_STOP` / `ENV_PATH_STOP`
- [ ] Classify PB1 semantic stage PASS/WARN/STOP
- [ ] Keep Block AttnRes unadopted until quality/resource/3-seed evidence
- [ ] Treat PB1 `N=4` quality null as potentially depth-resolution-limited
- [ ] Narrow higher-`N` gains to training-only/fused-kernel-dependent if resource Pareto fails

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

- No D workflow modification or repeat predispatch run before C005 exists
- No new architecture before reproducible baseline and preregistration
- No multi-component intervention
- No paper attribution from CR1
- No adoption from parameter/KV/asymptotic FLOPs alone
- No single-seed adoption
- No promotion of environment/semantic preflight to quality evidence
- No silent semantic patch
- No automatic transition from environment PASS to model execution
- No copy to default branch, broad trigger, or unregistered execution route
- No repeated execution trigger except one unchanged transient retry
- No mechanism-wide rejection from PB1 `N=4` null evidence
- No capability, intelligence-principle, high-school-level, or 1GB-goal claim without evidence
