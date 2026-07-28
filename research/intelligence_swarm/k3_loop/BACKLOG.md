# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-29 by K3-C

## P0 — Current cycle: Block AttnRes minimum reproduction

Classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**

Current single bottleneck:

> D003 exact-dependency, fresh-process, order-balanced resource/operator preflight

### A — Evidence

- [x] Author-controlled executable implementation/checkpoint status確認。2026-07-28時点で未公開。
- [x] 一次報告のmodel size、depth、width、block数、token budget抽出。
- [x] 非公式候補 `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6` 固定。
- [x] Dependency lower bound固定: Python 3.11、PyTorch >=2.4 exact build、Transformers `42791a34fdeae197f60f11ace3807c81f44b0729`。
- [ ] S2前にpaper-to-candidate deviation matrixを作成。
- [x] P0未解決中は他K3 componentを凍結。

### B — Theory

- [x] Parameter/FLOPs/state-memory/communication/sequence/quantization/CPU比較。
- [x] 小型scale反例と失敗条件。
- [x] B002 CPU roofline/operator trace contract。
- [x] Corrected delta `25,625`を反映。
- [x] B003 D002 scaling-breakpoint audit。
- [x] T=1/128/512 fit: `t≈0.100753+0.004197T ms/event`。
- [x] T=2048 ratio `≈4.13x`を未解決breakpoint候補として記録。
- [ ] D003 traceからfit、residual、operator share、temporary thresholdを再計算。
- [ ] D003前にCPU crossoverを主張しない。

### C — Preregistration

- [x] C001: 12-layer、d=512 dense PreNorm baseline固定。
- [x] C001: Block AttnRes `N=4`を単一変更として固定。
- [x] C001: optimizer、schedule、token budget、seed `17/29/43`固定。
- [x] C002: A1=`115,579,929`、delta=`25,625`へ訂正。
- [x] C002: D003 exact dependency/resolver provenanceを固定。
- [x] C002: save/load FP32 CPU tolerance `1e-6`固定。
- [x] C002: machine-readable PASS/WARN/STOP schema追加。
- [x] C002: CPU cases `T=1,128,512,2048`固定。
- [x] C002: separate fresh process、`AB/BA/AB/BA` order balance固定。
- [x] C002: warmup 10、measurement 30、median/p95/MAD/min/max固定。
- [x] C002: short-sequence fitと`actual_2048/predicted_2048` fields追加。
- [x] C002: operator attribution、temporary bytes、allocation evidence追加。
- [x] C002: D003のみ許可し、dataset取得・学習・量子化を禁止。
- [ ] D003 Path-PASS後も、実コードでglobal batch 64を保証する別amendmentを作成。
- [x] S1を許可しない。

Artifacts:

- `research/intelligence_swarm/k3_loop/prereg/C002_D003_EXACT_RUNTIME_PREFLIGHT_PREREG.md`
- `benchmarks/k3_minimal/manifests/C002_d003_exact_runtime_preflight.yaml`

### D — Reproduction

- [x] D001 static CLI/data/model contract audit。
- [x] D002 standalone parameter-faithful preflight。
- [x] Synthetic input seed 17。
- [x] B0=`115,554,304`、A1=`115,579,929`。
- [x] Routing-only parameter diff、finite forward/backward、全75 routing gradient、save/load差`0.0`。
- [x] E002がPath-WARNを維持しD003のみ許可。
- [ ] A002/C002に従いexact runtimeと全resolved hashを固定。
- [ ] Compatibility patch時は最大1件、diff/checksum保存。
- [ ] B0/A1を別fresh processで`AB/BA/AB/BA`実行。
- [ ] 条件別peak RSS、wall time、median/p95/MADを分離。
- [ ] no-op/list/source/stack/norm+score/softmax/mix controls追加。
- [ ] Temporary bytes、allocation/operator-call evidence保存。
- [ ] Exact runtimeでT<=512 fitとT=2048 ratio再計算。
- [ ] Raw logs、machine-readable result、checksums保存。
- [x] D003中のFineWeb-Edu/tokenizer取得、optimizer step、S1を禁止。

### E — Integration

- [x] E001: D002を単一ボトルネック化。
- [x] E002: D002をPath-WARNとして統合。
- [x] E002: D003を唯一の次実験として選定。
- [ ] D003後、implementation pathをPASS/WARN/STOP分類。
- [ ] `actual_2048/predicted_2048 >= 2.0`、CPU/RSS overhead `>=10%`等ならtraining-only/fusion-dependentへ狭義化を検討。
- [ ] Preregistered quality/resource evidence合格まで未採用を維持。
- [x] KDA、Stable LatentMoE等を凍結。

## D003 completion conditions

- [ ] exact environment lockとresolver provenance
- [ ] candidate commitとcompatibility patch checksum
- [ ] exact countsとresidual-only config/state-dict diff
- [ ] fixed input SHA256
- [ ] finite forward/backward/routing gradients
- [ ] save/load max abs `<=1e-6`
- [ ] fresh-process `AB/BA/AB/BA` repeated timing
- [ ] isolated peak RSS
- [ ] operator controlsとtemporary/allocation evidence
- [ ] T=1/128/512 fitとT=2048 breakpoint ratio
- [ ] raw logs、machine-readable summary、artifact checksums

## D003 classification rules

- **PASS:** semantic checksと再現可能な計測が成立。breakpointが消えるか説明可能。A1/B0 full-model時間・RSS overheadはいずれも10%未満。
- **WARN:** semanticsは成立するが、CPU時間/RSS `>=10%`、stack/layout+framework相当 `>=50%`、fresh-process ratio `>=2.0`、またはorder block間で効果方向が不安定。
- **STOP:** 1回の最小patch後も実行不能、残差以外の差分、parameter mismatch未説明、gradient/save-load失敗、計測不能、未登録architecture変更が必要。

## P1 — Candidate queue after P0

1. Kimi Delta Attention
2. Stable LatentMoE
3. MXFP4-aware training
4. Low-rank Attention Residuals
5. Data curriculum/post-training efficiency

P1 remains frozen.

## Global prohibitions

- Reproducible baselineとpreregistration前の新規architecture禁止。
- 複数component同時移植禁止。
- 根拠のない知能原理、高校生級、能力進歩の主張禁止。
- Parameter数、KV cache、漸近FLOPsだけで採用しない。
- 1 seed成功を採用根拠にしない。
- Preflight/smokeの事後的なfull evidence昇格禁止。
- Silent patch禁止。
- 実行が不便という理由で現在のボトルネックを文献監査や別候補へ置換しない。
