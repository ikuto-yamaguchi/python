# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-29 by K3-C
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3由来の効率化原理を、1GB以下・弱いCPU/スマホ向けモデルへ転用できるか、公開baseline・単一変更ablation・3 seed・資源計測で判定する。

## Current phase

**Phase 1.5: D003-GHA environment gate → variant-separated deterministic semantic trace。**

Completed: A001–A003, B001–B004, C001–C004, D001–D002, D003 local environment probe, E001–E003.

Current classifications:

- Block AttnRes: **小型化で要再設計・追加検証・未採用 / Path-WARN**
- PAPER-BLOCK (`PB1`): canonical paper candidate; C004 registered, semantic trace pending
- CANDIDATE-RAW (`CR1`): fixed-commit artifact diagnostic only; paper attribution prohibited

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

## Deterministic semantic trace contract

C003 `ENV_PASS`後、次の順で実行する。

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

1. D003-GHA environment/import workflowを追加・実行
2. branch SHA、runner provenance、resolver report、freeze、dependency/source hashesを保存
3. required internal importsを全件PASS
4. C003 `ENV_PASS` artifact SHAを固定
5. CR1/PB1 tiny deterministic semantic traceをvariant別に実行
6. EがPB1 semantic PASS/WARN/STOPを判断

Dが次に実行可能なのはC003 environment stageだけ。model stage、full-model timing、dataset、training、quantizationは未許可。

## Evidence boundary

Kimi K3全体の利得をAttnRes単独へ帰属しない。著者一次証拠は約194M active未満で未確立。semantic PASSはsource transition実装の適合だけを示し、品質、CPU Pareto、量子化、3-seed安定性、知能原理、高校生級、能力進歩、1GB目標達成は未主張。
