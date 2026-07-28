# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-29 by K3-B

## P0 — Block AttnRes minimum reproduction

Classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**

Current bottleneck:

> D003-GHA dependency/import gateをPASSし、C004でPAPER-BLOCKとCANDIDATE-RAWを分離した後、tiny deterministic semantic traceを通す。

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
- [ ] Exact D003 traceからfit、operator share、temporary threshold、paper/raw差を再計算
- [x] Exact trace前のCPU crossover/minimum-scale主張は禁止

### C — Preregistration

- [x] C001 baseline and single-change ablation
- [x] C002 exact dependency/fresh-process/resource protocol
- [ ] C003 GitHub Actions runner/provenance and two-stage gate
- [ ] C004 separate IDs/manifests/output paths for PAPER-BLOCK and CANDIDATE-RAW
- [ ] C004 register boundary indexing, partial reset, source identities
- [ ] C004 prohibit recency bias and optional gates in PAPER-BLOCK
- [ ] C004 register PAPER-BLOCK provisional total `115,579,904`
- [ ] Register checksum-collapsed semantic probability/entropy/effective source metrics
- [x] S1 remains unauthorized

### D — Reproduction

- [x] D001 static contract audit
- [x] D002 standalone preflight
- [x] D003 environment probe
- [x] Local `BLOCKED_ENV` isolated
- [ ] Add and run D003 GitHub Actions environment workflow
- [ ] Save branch SHA, runner provenance, exact dependencies, resolver report, freeze and hashes
- [ ] Pass all required internal imports
- [ ] Run tiny semantic trace before full-model timing
- [ ] Record source roles/checksums, duplicate groups, reset state and recency bias
- [ ] Record raw-index and checksum-collapsed probability, entropy and effective source count
- [ ] Verify PAPER-BLOCK delta `25,600` from exact state dict
- [ ] PAPER-BLOCK only: residual-only semantic/resource gate
- [ ] CANDIDATE-RAW only: artifact diagnostic; no paper attribution
- [ ] Fresh-process AB/BA timing, isolated RSS and operator controls
- [ ] T<=512 fit and T=2048 breakpoint ratio
- [x] Dataset, training and quantization prohibited

### E — Integration

- [x] E001–E003 completed
- [ ] Mark unchanged candidate inadmissible as canonical paper reproduction
- [ ] Classify D003-GHA environment stage PASS/RETRY/path failure
- [ ] Classify PAPER-BLOCK semantic/resource stage PASS/WARN/path failure
- [ ] Keep Block AttnRes unadopted until quality/resource/3-seed evidence

## PAPER-BLOCK semantic completion

- [ ] Registered boundary reset occurs
- [ ] No unintended duplicate source checksum
- [ ] No recency-bias parameter
- [ ] No optional mixing-gate parameter
- [ ] Source identities match preregistration
- [ ] Exact parameter delta is explained

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
- No promotion of preflight/smoke to full evidence
- No silent semantic patch
- No capability, intelligence-principle, high-school-level, or 1GB-goal claims without evidence