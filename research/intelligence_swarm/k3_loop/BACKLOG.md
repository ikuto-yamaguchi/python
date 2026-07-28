# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-29 by K3-A

## P0 — Block AttnRes minimum reproduction

Classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**

Current bottleneck:

> manual `workflow_dispatch`経路はorchestration blocker。C005でcanonical branch・environment paths限定の一回限りpush routeを事前登録し、D005がenvironment-only runを起動して`ENV_PASS` artifact ID/SHAを固定する。

### A — Evidence

- [x] Author executable/checkpoint status: 未公開
- [x] Primary model size/depth/width/block/token evidence extracted
- [x] Candidate commit fixed
- [x] Dependency lower bound fixed
- [x] A003 paper-to-candidate deviation matrix
- [x] Missing partial reset, duplicate source, recency bias identified
- [x] A004 paper layer-index origin and `L_sub/N/S` block-geometry audit
- [x] PB1 requires `L_sub=24`, `N=4`, `S=6`, ordered boundaries after Transformer blocks `[3,6,9,12]`
- [x] Zero-based initial false-boundary and odd-`S` truncation counterexamples fixed
- [ ] Resolver/import failureが出た場合のみprovenance追補
- [x] P0中は他K3 componentを凍結

### B — Theory

- [x] Parameter/FLOPs/state-memory/communication/sequence/quantization/CPU comparison
- [x] Small-scale counterexample and failure conditions
- [x] CPU roofline/operator trace contract
- [x] D002 scaling-breakpoint audit
- [x] B004 paper/raw routing-prior and identifiability audit
- [x] PAPER-BLOCK provisional delta `25,600`
- [x] Duplicate-prefix semantic mass and effective-source collapse derived
- [ ] Exact semantic/resource traceからoperator share、temporary threshold、paper/raw差を再計算
- [x] Exact trace前のCPU crossover/minimum-scale主張は禁止

### C — Preregistration

- [x] C001 baseline and single-change ablation
- [x] C002 exact dependency/fresh-process/resource protocol
- [x] C003 GitHub Actions runner/provenance and two-stage gate
- [x] C003 environment stageとmodel stageを別dispatchへ分離
- [x] C004 separate IDs/manifests/output paths for PAPER-BLOCK and CANDIDATE-RAW
- [x] C004 register boundary indexing, partial reset, source identities
- [x] C004 prohibit recency bias and optional gates in PAPER-BLOCK
- [x] C004 register PAPER-BLOCK provisional total `115,579,904`
- [x] Register checksum-collapsed semantic probability/entropy/effective source metrics
- [x] S1 remains unauthorized
- [x] E004 authorizes a narrow execution-route amendment; no model-contract change
- [ ] C005 preregister canonical branch only push trigger
- [ ] C005 restrict paths to environment workflow/script/manifest/amendment or dedicated non-semantic nonce
- [ ] C005 pin concurrency, authorization flags, artifact schema, and one-retry policy
- [ ] C005 prohibit automatic transition from ENV_PASS to model stage
- [ ] Next PB1 amendment must register 1-based semantic sublayer indexing, `L_sub/N/S`, exact ordered boundaries, odd/nondivisible rejection
- [ ] PB1 semantic PASS後にのみfull-model resource protocolをamend
- [ ] S1検討前に実コード上のglobal batch 64を保証

### D — Reproduction

- [x] D001 static contract audit
- [x] D002 standalone preflight
- [x] D003 environment probe
- [x] Local `BLOCKED_ENV` isolated
- [x] D004 add C003 environment runner script
- [x] D004 add manual GitHub Actions environment workflow on canonical branch
- [x] D004 static authorization/branch/evidence contract audit
- [x] Confirm no workflow run existed at inspection time
- [x] Classify manual dispatch as orchestration/protocol blocker, not scientific failure
- [ ] D005 update workflow exactly per C005 push-route amendment
- [ ] D005 let the amendment push initiate one environment-only run
- [ ] Save branch SHA, runner provenance, exact dependencies, resolver report, freeze and hashes
- [ ] Pass all required internal imports
- [ ] Save `ENV_PASS` artifact ID and artifact SHA
- [ ] If run starts but transient service/network failure occurs, record `ENV_RETRY` and rerun once unchanged
- [ ] If route does not start after the exact amendment, record `ROUTE_STOP`
- [ ] Run CR1 tiny semantic trace without semantic modification after separate authorization
- [ ] Run PB1 tiny semantic trace after CR1
- [ ] Record source roles/checksums, duplicate groups, reset state and recency bias
- [ ] Record raw-index and checksum-collapsed probability, entropy and effective source count
- [ ] Record runtime index origin, canonical Attention/MLP sublayer indices, exact ordered boundary sequence and per-block sublayer counts
- [ ] Reject boundary before first transformed sublayer, odd/truncated `S`, missing final completed block, or final-router-as-block miscount
- [ ] Verify PB1 delta `25,600` from exact state dict
- [ ] PB1 only: semantic PASS/WARN/STOP evidence
- [ ] CR1 only: `RAW_DIAGNOSTIC_COMPLETE` or failure; no paper attribution
- [ ] After PB1 PASS and separate authorization: fresh-process AB/BA timing, isolated RSS and operator controls
- [ ] T<=512 fit and T=2048 breakpoint ratio
- [x] Dataset, training and quantization prohibited

### E — Integration

- [x] E001–E004 completed
- [x] Mark unchanged candidate inadmissible as canonical paper reproduction
- [x] Classify D003-GHA manual dispatch as protocol amendment required
- [ ] Classify C005/D005 push route as ENV_PASS / ENV_RETRY / ROUTE_STOP / ENV_PATH_STOP
- [ ] Classify PB1 semantic stage PASS/WARN/STOP
- [ ] Require exact ordered boundary-position PASS in addition to reset/duplicate checks
- [ ] Record CR1 as artifact diagnostic only
- [ ] Keep Block AttnRes unadopted until quality/resource/3-seed evidence

## PAPER-BLOCK semantic completion

- [ ] Registered boundary reset occurs
- [ ] No unintended duplicate source identity
- [ ] No recency-bias parameter or contribution
- [ ] No optional mixing-gate parameter
- [ ] Source identities match preregistration
- [ ] Routing probabilities are finite and sum to one
- [ ] Semantic layer index is 1-based over Attention/MLP sublayers
- [ ] `L_sub=24`, `N=4`, `S=6` and boundaries after Transformer blocks `[3,6,9,12]`
- [ ] No boundary before the first transformed sublayer
- [ ] Every completed block contains exactly six sublayers
- [ ] Final router does not increment completed-block count
- [ ] Exact parameter delta is explained
- [ ] Save/load event structure and output match

## P1 queue — frozen

1. Kimi Delta Attention
2. Stable LatentMoE
3. MXFP4-aware training
4. Low-rank Attention Residuals
5. Data curriculum/post-training efficiency

## Global prohibitions

- No new architecture before reproducible baseline and preregistration
- No multi-component intervention
- No paper attribution from CANDIDATE-RAW
- No adoption from parameter/KV/asymptotic FLOPs alone
- No single-seed adoption
- No promotion of environment/semantic preflight to quality evidence
- No silent semantic patch
- No automatic transition from ENV_PASS to model execution
- No workflow copy to default branch for convenience
- No broad push/PR trigger; only C005 branch/path-restricted environment route is authorized
- No repeated nonce pushes except one unchanged `ENV_RETRY`
- No capability, intelligence-principle, high-school-level, or 1GB-goal claims without evidence
