# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-29 by K3-C

## P0 — Block AttnRes minimum reproduction

Classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**

Current bottleneck:

> C007 portable environment-gate preregistration is complete. The only next work is one D008 environment-only portable attempt on a compliant Python 3.11 CPU substrate, or one concrete `SUBSTRATE_STOP` if no such substrate is available.

### A — Evidence

- [x] Author executable/checkpoint status: 未公開
- [x] Primary scale/depth/width/block/token evidence extracted
- [x] Candidate and official commits fixed
- [x] Dependency lower bound fixed
- [x] Paper-to-candidate deviation matrix
- [x] Missing partial reset, duplicate source and recency bias identified
- [x] Paper layer-index origin and `L_sub/N/S` geometry fixed
- [x] PB1 boundaries `[3,6,9,12]`; zero-based false-boundary and odd-`S` counterexamples fixed
- [x] A005 official-artifact refresh and community implementation admissibility audit
- [x] A006 compact public implementation audit
- [ ] Add provenance only after a concrete D008 resolver/import failure
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
- [x] B007 execution-substrate invariance and evidence-admissibility conditions fixed
- [x] B008 portable-substrate equivalence and trust-closure requirements fixed
- [ ] Recalculate operator share and actual/expected slots from exact trace
- [x] No CPU crossover or minimum-scale claim before exact trace

### C — Preregistration

- [x] C001–C006 completed
- [x] C005 canonical-push route closed as `ROUTE_STOP`
- [x] C006 default-branch dispatcher route closed as `ENV_PROTOCOL_FAIL`
- [x] Create `C007_PORTABLE_ENVIRONMENT_GATE_PREREGISTRATION.md`
- [x] Create `benchmarks/k3_minimal/manifests/C007_portable_environment_gate.yaml`
- [x] Fix immutable scientific source commit `9edf4c7143ff1d62685ed893352df7a32090fe1e`
- [x] Fix C003/C004/C007/script/probe identity requirements
- [x] Fix Python 3.11, exact CPU PyTorch, fixed Transformers commit and replay command
- [x] Fix online-Git/offline-Git-bundle acquisition and canonical-ref reachability
- [x] Fix detached checkout, clean-tree, untracked/submodule/LFS rejection
- [x] Fix all model-stage authorizations false and no automatic continuation
- [x] Fix resolver/freeze/checksum/import/raw-log/platform schema
- [x] Fix `sys.path`, module-origin hashes and external-shadow rejection
- [x] Fix inner evidence checksum and outer deterministic archive checksum/size
- [x] Fix `ENV_PASS / ENV_RETRY / SUBSTRATE_STOP / ENV_PATH_STOP_PENDING_AMENDMENT / ENV_PATH_STOP / ENV_PROTOCOL_FAIL`
- [ ] Amend C007 only if D008 exposes one specific preregistration defect

### D — Reproduction

- [x] D001 static contract audit
- [x] D002 standalone preflight
- [x] D003 local environment blocker isolation
- [x] D004 environment workflow staging
- [x] D005 preregistration blocker audit
- [x] D006 canonical-push route execution and `ROUTE_STOP`
- [x] D007 default-branch attempt completed as `ENV_PROTOCOL_FAIL`
- [x] Close both GitHub Actions routes
- [x] Quarantine incomplete `.github/workflows/d007-k3-environment-dispatcher.yml`; never dispatch it
- [ ] Create thin `benchmarks/k3_minimal/preflight/d008_portable_environment.sh` launcher with no model or dependency substitution logic
- [ ] Record launcher Git blob SHA, byte SHA256 and size before execution
- [ ] Run one environment-only attempt on a compliant Python 3.11 CPU substrate
- [ ] Persist replay command, source/ref reachability, clean-tree evidence and normative file identities
- [ ] Persist resolver report, `pip freeze --all`, `pip check` and all dependency artifact hashes
- [ ] Persist `sys.path`, imported module origins and imported source hashes
- [ ] Persist platform provenance and all authorization flags false
- [ ] Produce sorted inner `checksums.sha256`
- [ ] Produce deterministic outer archive plus separate SHA256 and byte size
- [ ] If no compliant substrate exists, record one concrete `SUBSTRATE_STOP`; do not repeat substrate audits
- [ ] After separate authorization only: CR1 trace, then PB1 trace
- [x] Dataset, model execution, semantic trace, training and quantization remain prohibited

### E — Integration

- [x] E001–E007 completed
- [x] D007 classified `ENV_PROTOCOL_FAIL`
- [x] Both GitHub Actions routes closed
- [x] Block AttnRes/PB1/CR1 not rejected by orchestration failure
- [x] Single next hypothesis moved to portable environment gate
- [ ] Classify D008 as `ENV_PASS`, `ENV_RETRY`, `SUBSTRATE_STOP`, `ENV_PATH_STOP_PENDING_AMENDMENT`, `ENV_PATH_STOP` or `ENV_PROTOCOL_FAIL`
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

- No further C005/C006 trigger, nonce, dispatcher or default-branch workflow variants
- Never dispatch the incomplete D007 workflow on `main`
- No broad push or PR trigger shortcut
- No model code on an orchestration branch or launcher
- No new architecture before reproducible baseline and preregistration
- No multi-component intervention
- No paper attribution from CR1
- No adoption from parameter/KV/asymptotic FLOPs alone
- No single-seed adoption
- No promotion of environment/semantic preflight to quality evidence
- No silent semantic or compatibility patch
- No automatic transition from environment PASS to model execution
- No mechanism-wide rejection from PB1 `N=4` null evidence
- No substitution of third-party Megatron or compact public implementations during P0 without a new semantic audit and preregistration
- No capability, intelligence-principle, high-school-level or 1GB-goal claim without evidence
