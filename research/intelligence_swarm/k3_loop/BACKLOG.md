# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-29 by K3-B

## P0 — Block AttnRes minimum reproduction

Classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**

Current bottleneck:

> C005 canonical-branch routeは`ROUTE_STOP`として終了した。次の唯一の作業はCが、default branch上の薄いenvironment-only dispatcherを定義するC006本文とmanifestを作成すること。

### A — Evidence

- [x] Author executable/checkpoint status: 未公開
- [x] Primary model size/depth/width/block/token evidence extracted
- [x] Candidate and official commits fixed
- [x] Dependency lower bound fixed
- [x] Paper-to-candidate deviation matrix
- [x] Missing partial reset, duplicate source and recency bias identified
- [x] Paper layer-index origin and `L_sub/N/S` geometry fixed
- [x] PB1 boundaries `[3,6,9,12]`; zero-based false-boundary and odd-`S` counterexamples fixed
- [x] A005 official-artifact refresh: author executable/checkpoint still unavailable on 2026-07-29
- [x] Community Megatron implementation classified as independent reproduction lead, not official/admissible during P0
- [ ] Add provenance only after a concrete resolver/import failure
- [x] Freeze other K3 components during P0

A005 evidence:

- `research/intelligence_swarm/k3_loop/evidence/A005_OFFICIAL_ARTIFACT_STATUS_AND_COMMUNITY_IMPLEMENTATION_ADMISSIBILITY.md`

### B — Theory

- [x] Parameter/FLOPs/state-memory/communication/sequence/quantization/CPU comparison
- [x] Small-scale counterexamples and CPU roofline contract
- [x] D002 scaling-breakpoint audit
- [x] Paper/raw routing-prior identifiability audit
- [x] PB1 provisional delta `25,600`
- [x] PB1 source-slot bounds: sublayer `84`, final `5`, total `89`
- [x] PB1 classified as minimum semantic/effect-direction pilot
- [x] PB1 falsifiability boundary fixed
- [x] B007 execution-substrate invariance and evidence-admissibility conditions fixed
- [ ] Recalculate operator share and actual/expected slots from exact trace
- [x] No CPU crossover or minimum-scale claim before exact trace
- [ ] Verify C006/D007 against B007 canonical-code, dependency, authorization, launcher-thinness, and artifact-completeness conditions

B007 theory:

- `research/intelligence_swarm/k3_loop/theory/B007_EXECUTION_SUBSTRATE_INVARIANCE_AND_EVIDENCE_ADMISSIBILITY.md`

### C — Preregistration

- [x] C001–C005 completed
- [x] C005 route executed and closed as `ROUTE_STOP`
- [ ] Create `C006_DEFAULT_BRANCH_THIN_DISPATCHER_AMENDMENT.md`
- [ ] Create matching C006 machine-readable manifest
- [ ] Fix required inputs: canonical branch/SHA, C003/C004/C006 manifest SHA, environment script SHA
- [ ] Fix detached-checkout, allowlist, dirty-tree, branch/SHA guards
- [ ] Keep all model/training/data/quantization authorization false
- [ ] Fix artifact schema, one unchanged transient retry, and no automatic model continuation
- [ ] Do not modify default branch before C006 prose and manifest agree exactly

### D — Reproduction

- [x] D001 static contract audit
- [x] D002 standalone preflight
- [x] D003 local environment blocker isolation
- [x] D004 environment workflow staging
- [x] D005 preregistration blocker audit
- [x] D006 C005 route execution and `ROUTE_STOP` evidence
- [x] Stop further C005 nonce/path-filter variants
- [ ] Wait for C006 before any default-branch change
- [ ] After C006 only: introduce thin dispatcher to default branch through an auditable minimal change
- [ ] After C006 only: dispatch one environment-only run against exact canonical SHA
- [ ] Collect artifact ID/ZIP SHA256, resolver report, freeze, source/dependency hashes, import results, raw logs
- [ ] Classify `ENV_PASS / ENV_RETRY / ROUTE_STOP_DEFAULT_BRANCH / ENV_PATH_STOP / ENV_PROTOCOL_FAIL`
- [ ] After separate authorization only: CR1 trace, then PB1 trace
- [x] Dataset, model execution, training and quantization prohibited

D006 evidence:

- `research/intelligence_swarm/k3_loop/reproduction/D006_C005_CANONICAL_PUSH_ROUTE_STOP.md`
- `benchmarks/k3_minimal/preflight/D006_c005_push_route_result.json`

### E — Integration

- [x] E001–E006 completed
- [x] Candidate-raw made inadmissible as canonical paper reproduction
- [x] Manual dispatch classified as orchestration blocker
- [x] D005 classified as `PREREG_BLOCKED`
- [x] D006 classified as `ROUTE_STOP`; C005 route closed
- [x] PB1 result interpretation fixed
- [x] Default-branch thin dispatcher judged scientifically separable from model intervention
- [ ] Classify C006/D007 route and environment outcome
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

- No further C005 route variants
- No default-branch change before C006 preregistration is complete
- No broad trigger or PR-trigger shortcut
- No new architecture before reproducible baseline and preregistration
- No multi-component intervention
- No paper attribution from CR1
- No adoption from parameter/KV/asymptotic FLOPs alone
- No single-seed adoption
- No promotion of environment/semantic preflight to quality evidence
- No silent semantic patch
- No automatic transition from environment PASS to model execution
- No mechanism-wide rejection from PB1 `N=4` null evidence
- No substitution of third-party Megatron implementations during P0 without a new semantic audit and preregistration
- No capability, intelligence-principle, high-school-level, or 1GB-goal claim without evidence
