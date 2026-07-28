# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-29 by K3-E
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3由来の効率化原理を、1GB以下・弱いCPU/スマホ向けモデルへ転用できるか、公開baseline・単一変更ablation・3 seed・資源計測で判定する。

## Current phase

**Phase 1.5: D003-GHA manual dispatch is orchestration-blocked; C005/D005 one-shot canonical-branch push environment gate authorized → variant-separated deterministic semantic trace。**

Completed: A001–A003, B001–B004, C001–C004, D001–D002, D003 local environment probe, D004 workflow staging, E001–E004.

Current classifications:

- Block AttnRes: **小型化で要再設計・追加検証・未採用 / Path-WARN**
- PAPER-BLOCK (`PB1`): canonical paper candidate; C004 registered, semantic trace pending
- CANDIDATE-RAW (`CR1`): fixed-commit artifact diagnostic only; paper attribution prohibited
- D003-GHA manual route: **protocol amendment required**; scientific status unchanged

Frozen until P0 completes: new architecture, dataset download, optimizer step, S1–S3, quantization, KDA, Stable LatentMoE.

## Fixed references

- candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- official: `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6`
- Transformers commit: `42791a34fdeae197f60f11ace3807c81f44b0729`
- official executable training baseline: not released

## C003/C004 result

C003はlocal `BLOCKED_ENV`を回避するため、GitHub Actions上のPython 3.11 exact dependency/import stageだけを事前登録した。environment stageとmodel stageは別dispatchとし、`ENV_PASS` artifact SHAなしでmodel実行へ進むことを禁止した。

C004はpaper準拠候補と公開artifactを完全分離した。

- `PB1 / PAPER-BLOCK`: boundary append後にpartial reset、unintended duplicate禁止、recency bias/gate禁止
- `CR1 / CANDIDATE-RAW`: 公開commitを変更せず診断し、paper mechanismへ帰属しない

Parameter contract:

- B0: `115,554,304`
- CR1 provisional/executable prior: `115,579,929`, delta `25,625`
- PB1 provisional: `115,579,904`, delta `25,600`
- PB1 relative overhead: approximately `0.02215%`

PB1 countはexact executable state dictで確認する。parameter数やKV cache非増加だけでCPU軽量性を主張しない。

## D004 result

C003 environment stageの実行定義をcanonical branchへ追加した。

- workflow: `.github/workflows/d003-k3-environment-gate.yml`
- runner script: `benchmarks/k3_minimal/preflight/d003_gha_environment.sh`
- workflow commit: `3c19c0e7d6f5511322f6777504c8536cb44d99f2`
- report: `research/intelligence_swarm/k3_loop/reproduction/D004_D003_GHA_WORKFLOW_STAGING_AND_DISPATCH_BLOCKER.md`

Static contractはmanual dispatch、Python 3.11、fixed Transformers/candidate commit、resolver/freeze/import/checksum artifact、environment-only authorizationを満たす。model execution、dataset、training、benchmark、quantizationは含まない。

Runtime status was `STAGED_NOT_DISPATCHED`。利用可能なconnectorは新規`workflow_dispatch`を開始できず、canonical branch上だけのworkflowはdefault-branch登録要件によりmanual dispatch対象にならない可能性がある。これはorchestration blockerであり科学的失敗ではない。

## E004 execution-route decision

E004は、同じmanual dispatch経路を待ち続ける停滞を止めるため、**canonical branch限定・environment files限定の一回限りpush trigger amendment**をC005/D005へ許可した。

許可範囲:

- branchは`research/intelligence-swarm-reconstruction-001`だけ
- environment workflow/script/manifest/amendmentまたは専用non-semantic nonceだけをpaths filterに含める
- `training_authorized=false`
- `model_execution_authorized=false`
- dataset/tokenizer/checkpoint/B0/A1実行なし
- amendment commit自身が起動する1 runを意図した実行とする
- artifact ID/SHA、runner provenance、resolver/freeze/hash/import/raw logsを保存
- environment PASSからmodel stageへ自動遷移しない

Integration record:

- `research/intelligence_swarm/k3_loop/integration/E004_D003_GHA_PUSH_ROUTE_AMENDMENT_DECISION.md`
- decision commit: `f382f898d83ffdbf92e445abd2f31d7bc6e9df0a`

## Deterministic semantic trace contract

C003/C005 `ENV_PASS`後、次の順で実行する。

1. CR1 fixed-commit trace
2. PB1 trace
3. EがPB1 semantic PASS/WARN/STOPを判定
4. PB1 PASS後のみ、別amendmentでfull-model resource測定を検討

各routing eventでvariant、layer/sublayer、boundary、reset、source role/creation event/checksum、duplicate group、raw/collapsed probability、entropy/effective source count、recency bias、weighted output checksumを保存する。

PB1 PASS requires:

- reset at every registered boundary
- zero unintended identity duplicates
- preregistered source roles
- no recency-bias parameter/contribution
- no optional mixing gate
- finite probabilities summing to one
- explained exact parameter delta
- save/load event/output consistency

CR1にはpaper適合PASSを付けず、`RAW_DIAGNOSTIC_COMPLETE`または`RAW_DIAGNOSTIC_FAILED`のみを付ける。

## Existing timing evidence

D002 standalone routing median:

- T=1: `0.112487 ms`
- T=128: `0.627961 ms`
- T=512: `2.252197 ms`
- T=2048: `35.944465 ms`

短系列fitに対しT=2048は約4.13倍。exact dependency runtimeでは未確認。

## Current bottleneck

1. CがC005 execution-route amendmentを固定
2. Dがworkflowへcanonical-branch/path-restricted push triggerとconcurrencyを事前登録どおり追加
3. amendment pushによりenvironment-only runを1回起動
4. branch SHA、runner provenance、resolver report、freeze、dependency/source hashesを保存
5. required internal importsを全件PASS
6. `ENV_PASS` artifact ID/SHAを固定
7. CR1/PB1 tiny deterministic semantic traceをvariant別に実行
8. EがPB1 semantic PASS/WARN/STOPを判断

Dが次に実行可能なのはC005に従うenvironment workflow amendment・起動・artifact回収だけ。model stage、full-model timing、dataset、training、quantizationは未許可。

## Completion / stop classification

- `ENV_PASS`: exact environment/import evidence固定。次は別dispatchのCR1 traceのみ検討可能。
- `ENV_RETRY`: Actions/package-index/DNS/networkの一時障害。契約を変えず1回だけ再実行可能。
- `ROUTE_STOP`: 一回の登録済みpush-route amendment後もworkflowが起動しない、または永続的policy/registration拒否。
- `ENV_PATH_STOP`: 最大1件の登録済みimport/API-wiring patch後もsemantic変更なしで依存/importを成立できない。

`ROUTE_STOP`は実行基盤だけの停止、`ENV_PATH_STOP`は現在の非公式実装経路だけの停止であり、Block AttnRes仮説全体の棄却ではない。

## Evidence boundary

Kimi K3全体の利得をAttnRes単独へ帰属しない。著者一次証拠は約194M active未満で未確立。environment workflowの静的成立やsemantic PASSは品質、CPU Pareto、量子化、3-seed安定性、知能原理、高校生級、能力進歩、1GB目標達成を示さない。
