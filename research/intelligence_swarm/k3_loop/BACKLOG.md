# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-29 by K3-C

## P0 — Block AttnRes minimum reproduction

Classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**

Current bottleneck:

> D003-GHA environment/import workflowを実行して`ENV_PASS` artifact SHAを固定し、その後にCR1/PB1を分離したtiny deterministic semantic traceを通す。

### A — Evidence

- [x] Author executable/checkpoint status: 未公開
- [x] Primary model size/depth/width/block/token evidence extracted
- [x] Candidate commit fixed
- [x] Dependency lower bound fixed
- [x] A003 paper-to-candidate deviation matrix
- [x] Missing partial reset, duplicate source, recency bias identified
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
- [ ] PB1 semantic PASS後にのみfull-model resource protocolをamend
- [ ] S1検討前に実コード上のglobal batch 64を保証

### D — Reproduction

- [x] D001 static contract audit
- [x] D002 standalone preflight
- [x] D003 environment probe
- [x] Local `BLOCKED_ENV` isolated
- [ ] Add and run D003 GitHub Actions environment workflow from C003 manifest
- [ ] Save branch SHA, runner provenance, exact dependencies, resolver report, freeze and hashes
- [ ] Pass all required internal imports
- [ ] Save `ENV_PASS` artifact SHA
- [ ] Run CR1 tiny semantic trace without semantic modification
- [ ] Run PB1 tiny semantic trace after CR1
- [ ] Record source roles/checksums, duplicate groups, reset state and recency bias
- [ ] Record raw-index and checksum-collapsed probability, entropy and effective source count
- [ ] Verify PB1 delta `25,600` from exact state dict
- [ ] PB1 only: semantic PASS/WARN/STOP evidence
- [ ] CR1 only: `RAW_DIAGNOSTIC_COMPLETE` or failure; no paper attribution
- [ ] After PB1 PASS and separate authorization: fresh-process AB/BA timing, isolated RSS and operator controls
- [ ] T<=512 fit and T=2048 breakpoint ratio
- [x] Dataset, training and quantization prohibited

### E — Integration

- [x] E001–E003 completed
- [x] Mark unchanged candidate inadmissible as canonical paper reproduction
- [ ] Classify D003-GHA environment stage PASS/RETRY/path failure
- [ ] Classify PB1 semantic stage PASS/WARN/STOP
- [ ] Record CR1 as artifact diagnostic only
- [ ] Keep Block AttnRes unadopted until quality/resource/3-seed evidence

## PAPER-BLOCK semantic completion

- [ ] Registered boundary reset occurs
- [ ] No unintended duplicate source identity
- [ ] No recency-bias parameter or contribution
- [ ] No optional mixing-gate parameter
- [ ] Source identities match preregistration
- [ ] Routing probabilities are finite and sum to one
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
- No capability, intelligence-principle, high-school-level, or 1GB-goal claims without evidence
