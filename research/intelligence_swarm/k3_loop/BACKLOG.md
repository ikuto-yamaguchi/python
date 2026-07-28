# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-29 by K3-C

## P0 — Block AttnRes minimum reproduction

Classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**

Current bottleneck:

> C005本文とmanifestは完成した。次の唯一の作業は、Dが登録済みworkflow差分だけを適用し、canonical branch限定のenvironment-only push runを1件起動してprovenance artifactを固定すること。

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
- [x] PB1 falsifiability boundary fixed: null is not mechanism-wide rejection; positive is not adoption
- [x] Higher-`N` escalation slot lower bounds fixed: `185` (`N=8,S=4,L=32`) and `334` (`N=9,S=6,L=54`)
- [ ] Recalculate operator share and actual/expected slots from exact trace
- [x] No CPU crossover or minimum-scale claim before exact trace

### C — Preregistration

- [x] C001 baseline and single-change ablation
- [x] C002 exact dependency/resource protocol
- [x] C003 GitHub Actions environment gate
- [x] C004 PB1/CR1 variant separation and semantic trace
- [x] E004 authorized a narrow execution-route amendment
- [x] E005 fixed preregistration order and prohibited D churn before C005
- [x] Create `research/intelligence_swarm/k3_loop/prereg/C005_D003_GHA_PUSH_ROUTE_AMENDMENT.md`
- [x] Create `benchmarks/k3_minimal/manifests/C005_d003_gha_push_route.yaml`
- [x] Restrict route to canonical branch and environment-related paths only
- [x] Fix concurrency/cancellation and one intended environment-only run
- [x] Fix `training_authorized=false` and `model_execution_authorized=false`
- [x] Fix artifact schema: branch/run identity, runner, resolver, freeze, source/dependency hashes, imports, raw logs, artifact SHA
- [x] Prohibit automatic transition from environment PASS to model stage
- [x] Allow one unchanged retry only after transient failure following run start
- [x] Define `ENV_PASS`, `ENV_RETRY`, `ROUTE_STOP`, `ENV_PATH_STOP`, `ENV_PROTOCOL_FAIL`
- [x] Carry forward PB1 trace fields: 1-based sublayers, `L_sub=24`, `N=4`, `S=6`, boundaries `[3,6,9,12]`, odd/non-divisible rejection
- [x] Carry forward source-slot bounds `84/5/89` and `primary_evidence_geometry_matched=false`
- [x] Carry forward B006 interpretation fields: PB1 null non-falsifying, PB1 positive non-adoptive, higher-`N` separate preregistration
- [x] Keep S1 unauthorized
- [ ] Do not amend C005 unless D returns a concrete result and E authorizes a change

### D — Reproduction — sole current work

- [x] D001 static contract audit
- [x] D002 standalone preflight
- [x] D003 local environment blocker isolation
- [x] D004 environment workflow staging
- [x] D005 predispatch audit found C005 absent and returned `PREREG_BLOCKED`
- [x] D005 made no unregistered workflow change
- [x] Both C005 files now exist
- [ ] Apply only the exact C005 workflow amendment
- [ ] Add C005 concurrency and false authorization guards
- [ ] Verify the trigger commit changes only C005 allowlisted files
- [ ] Create `research/intelligence_swarm/k3_loop/execution/C005_D003_GHA_PUSH_NONCE.txt` attempt `1`
- [ ] Let the registered amendment initiate exactly one environment-only run
- [ ] Save branch SHA, workflow/script/manifest/nonce blob SHA, runner provenance, resolver report, freeze, hashes, imports and raw logs
- [ ] Fix `ENV_PASS` artifact ID/name/ZIP SHA and summary SHA, or classify retry/stop/protocol outcome
- [ ] Use at most one unchanged retry only after a run-started transient failure
- [ ] After separate authorization: CR1 trace, then PB1 trace
- [ ] Verify PB1 reset, no duplicate, no bias/gate, exact boundary sequence and `84/5/89` accounting
- [ ] If a PB1 quality pilot is later authorized, save routing health metrics needed by B006
- [ ] After PB1 PASS and separate preregistration: consider resource measurement
- [x] Dataset, training and quantization prohibited

### E — Integration

- [x] E001–E005 completed
- [x] Candidate-raw made inadmissible as canonical paper reproduction
- [x] Manual dispatch classified as orchestration blocker
- [x] D005 result classified as `PREREG_BLOCKED`, not environment/model evidence
- [x] C005 made the sole preregistration bottleneck
- [x] PB1 result interpretation fixed: null defaults inconclusive; positive permits only additional validation
- [ ] After D returns, classify `ENV_PASS` / `ENV_RETRY` / `ROUTE_STOP` / `ENV_PATH_STOP` / `ENV_PROTOCOL_FAIL`
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

- No workflow change beyond the exact C005 amendment
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
