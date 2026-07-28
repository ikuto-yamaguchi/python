# K3 Minimal Intelligence Loop — Backlog

Last updated: 2026-07-29 by K3-E

## P0 — Block AttnRes minimum reproduction

Classification: **小型化で要再設計・追加検証・未採用 / Path-WARN**

Current single bottleneck:

> GitHub Actions上のPython 3.11 CPU環境でD003 exact dependency/import gateをPASSさせ、provenance artifactsを保存する。

### A — Evidence

- [x] Author-controlled executable implementation/checkpoint status確認。未公開。
- [x] 一次報告のmodel size、depth、width、block数、token budget抽出。
- [x] 非公式候補 `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6` 固定。
- [x] Dependency lower bound固定。
- [ ] Actions resolver/import probeで具体的不一致が出た場合のみprovenanceを追補。
- [ ] S2前にpaper-to-candidate deviation matrixを作成。
- [x] P0未解決中は他K3 componentを凍結。

### B — Theory

- [x] Parameter/FLOPs/state-memory/communication/sequence/quantization/CPU比較。
- [x] 小型scale反例と失敗条件。
- [x] CPU roofline/operator trace contract。
- [x] Corrected delta `25,625`反映。
- [x] D002 scaling-breakpoint audit。
- [x] T=1/128/512 fitとT=2048 ratio `≈4.13x`記録。
- [ ] exact D003 traceからfit、residual、operator share、temporary thresholdを再計算。
- [x] D003前にCPU crossoverを主張しない。

### C — Preregistration

- [x] C001 baseline/Block AttnRes単一変更、token budget、seed `17/29/43`固定。
- [x] C002 exact dependency、fresh-process、AB/BA、RSS/operator protocol固定。
- [ ] C003: GitHub Actions runner image/provenance、Python 3.11、dependency lock、cache policy、artifact pathsを登録。
- [ ] C003: environment PASS後のみmeasurementを許可する二段階gateを登録。
- [ ] D003 Path-PASS後もglobal batch 64を保証する別amendmentを作成。
- [x] S1を許可しない。

### D — Reproduction

- [x] D001 static contract audit。
- [x] D002 standalone parameter-faithful preflight。
- [x] D003 environment/import probe実装。
- [x] 現行sandboxの`BLOCKED_ENV`を機械可読保存。
- [x] blockerをPython 3.13、Transformers/tokenizers欠如、GitHub DNS不可へ切り分け。
- [ ] 手動dispatch可能なD003 GitHub Actions workflowを追加。
- [ ] canonical branch/commit SHAとrunner image provenanceを保存。
- [ ] Python 3.11 exact patchを記録。
- [ ] exact PyTorch buildとTransformers commitをinstall。
- [ ] `pip --report`、`pip freeze`、downloaded wheel/source hashesを保存。
- [ ] `d003_environment_probe.py`を実行しrequired imports全件PASS。
- [ ] failure時もraw logsとsummaryをartifact upload。
- [ ] Stage 1 PASS後のみexact B0/A1 semantic gateを実行。
- [ ] exact countsとresidual-only config/state-dict diff。
- [ ] fixed input SHA256、forward/backward/routing gradients、save/load `<=1e-6`。
- [ ] fresh-process `AB/BA/AB/BA` timingとisolated RSS。
- [ ] no-op/list/source/stack/norm+score/softmax/mix controls。
- [ ] temporary bytes、allocation/operator-call evidence。
- [ ] T<=512 fitとT=2048 breakpoint ratio。
- [ ] raw logs、machine-readable summary、artifact checksums。
- [x] Dataset、optimizer step、S1/S2/S3、量子化を禁止。

### E — Integration

- [x] E001: D002を単一ボトルネック化。
- [x] E002: D002をPath-WARNとして統合しD003を選定。
- [x] E003: local `BLOCKED_ENV`を科学的失敗とせず、D003をGitHub Actionsへ移管。
- [ ] D003-GHA environment stage後、dependency pathをPASS/RETRY/STOP分類。
- [ ] exact model stage後、implementation pathをPASS/WARN/STOP分類。
- [ ] quality/resource evidence合格まで未採用を維持。

## D003-GHA environment completion conditions

- [ ] Python `3.11.x`
- [ ] exact PyTorch buildとTransformers commit記録
- [ ] required internal imports全件PASS
- [ ] candidate source/patch checksum
- [ ] resolver report、freeze、environment metadata
- [ ] raw logsとartifact checksums
- [ ] silent API substitutionなし

## D003-GHA classification

- **ENV-PASS:** exact dependency/import gateとprovenance artifactが成立。
- **ENV-RETRY:** Actions、package index、DNS等の一時障害。科学的判断には使わず再実行。
- **PATH-STOP:** 固定runnerと最大1件の登録済みimport/API-wiring patch後にも、semantic変更なしでdependency/import/instantiateが成立しない。
- **MODEL-PASS:** residual-only semantics、gradient/save-load、再現可能なmeasurementが成立し、A1 full-model時間・RSS overheadが各10%未満。
- **MODEL-WARN:** CPU時間/RSS `>=10%`、stack/layout+framework相当 `>=50%`、fresh-process ratio `>=2.0`、またはorder block不安定。

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
- Preflight/smokeの事後的full evidence昇格禁止。
- Silent patch禁止。
- 現在の環境が不便という理由で、別候補や文献監査へ逃げない。