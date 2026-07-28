# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-29 by K3-E
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3 と関連一次研究から、1GB以下・弱いCPU/スマホで高速な汎用モデルへ転用可能な効率化原理を抽出し、公開baseline再現、単一変更ablation、3-seed計測を通して採否を決める。

## Current phase

**Phase 1.2: D003 exact dependency/import gateをGitHub Actions上へ移し、再現可能なPython 3.11 CPU環境を固定する。**

- A001/A002、B001/B002/B003、C001/C002、D001/D002、E001/E002/E003完了。
- 現行sandboxのD003 probeは `BLOCKED_ENV`。これは品質失敗でもimplementation-path STOPでもない。
- Block AttnRes: **小型化で要再設計・追加検証・未採用 / Path-WARN**。
- 新規architecture、dataset取得、optimizer step、S1/S2/S3、量子化、KDA、Stable LatentMoEは引き続き禁止。

## Current candidate

- candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- candidate model blob SHA: `649aa0067e5b9d0fc2a3cc68784a6794090a26a4`
- official reference: `MoonshotAI/Attention-Residuals`
- official executable training baseline: 未公開
- reproduction classification: 非公式実装の独立再現

## Dependency contract

- Python: `3.11.x` exact patchをrunner実測で記録
- PyTorch: upstream requirement `>=2.4` を満たす単一exact build
- Transformers: `42791a34fdeae197f60f11ace3807c81f44b0729`
- tokenizersおよび全transitive dependency: exact version/hash固定
- `pip --report`、`pip freeze`、downloaded artifact hashes、Python executable、CPU/OS/thread情報を保存
- synthetic preflightではdataset/tokenizer model/W&B/UI依存を除外
- compatibility patchはimport/API wiringに限り最大1件。semantic、shape、initialization、forward equationの変更は禁止

## Local environment result

Observed sandbox:

- Python `3.13.5`
- PyTorch `2.10.0+cpu`
- Transformers/tokenizers absent
- GitHub DNS unavailable
- gate status: `BLOCKED_ENV`
- result SHA256: `aee26a00ae6b7e6400144dce4c95b57500c3b74b705fb027e40552fda7efe8f3`

この環境を待ち続けず、同じ実験契約をGitHub Actionsの固定CPU runnerへ移す。

## Corrected parameter contract

- B0 total/active parameters: `115,554,304`
- A1 total/active parameters: `115,579,929`
- AttnRes addition: `25,625`
- relative overhead: `0.02218%`
- B0 FP32 parameter bytes: `462,217,216`
- A1 FP32 parameter bytes: `462,319,716`

## Existing evidence boundary

D002 standalone harnessはrouting-only parameter差分、有限forward/backward、全75 routing tensorの有限非ゼロgradient、save/load差`0.0`を通過した。ただしexact third-party runtimeではなく、品質、training throughput、CPU生成、量子化、3-seed証拠はない。

Routing単体のD002値:

- T=1: `0.112487 ms`
- T=128: `0.627961 ms`
- T=512: `2.252197 ms`
- T=2048: `35.944465 ms`

T=1/128/512 fitは `t≈0.100753+0.004197T ms/event`。T=2048は予測の約`4.13x`で原因未識別。

## Current single bottleneck

**D003-GHA: GitHub Actions上でexact dependency/import gateをPASSさせ、provenance artifactsを保存すること。**

単一仮説:

> 固定GitHub Actions CPU jobとPython 3.11により、候補互換dependency graphと内部APIをsilent substitutionなしで固定でき、その後にexact B0/A1 fresh-process AB/BA計測へ進める。

## Authorized next work

### A

- 新K3技術は凍結。
- Actions resolver/import probeで具体的不一致が出た場合のみdependency provenanceを追加監査。

### B

- exact D003 trace後にfit、2048 residual、operator share、temporary threshold、full-model overheadを再計算。
- それ以前のCPU crossover主張は禁止。

### C

- GitHub Actions実行基盤だけを固定するC003 amendment/manifestを作る。
- runner image/provenance、Python 3.11、exact dependency lock、cache policy、artifact paths、environment PASS後のみmeasurementを許可する二段階gateを登録。
- 候補、threshold、architectureは変更しない。S1は許可しない。

### D

D003-GHAのみ実行する。

Stage 1:

1. canonical branch checkoutとcommit SHA保存
2. Python 3.11 setup
3. exact dependency resolve/install
4. resolver report、freeze、artifact hashes、environment metadata保存
5. `d003_environment_probe.py`実行
6. 成否にかかわらずraw logs/artifacts upload

Stage 1 PASS後のみStage 2:

- exact countsとresidual-only config/state-dict diff
- fixed input SHA256
- finite forward/backward/routing gradients
- save/load `<=1e-6`
- fresh-process `AB/BA/AB/BA`
- isolated peak RSS、operator controls、temporary/allocation evidence
- T<=512 fit、T=2048 residual/ratio

Dataset取得・学習は禁止。

## Completion and stop rules

Environment PASS:

- Python 3.11.x
- exact PyTorch build/Transformers commit記録
- required internal imports全件PASS
- candidate/patch checksums
- resolver/freeze/environment/raw logs/checksumsをartifact化
- silent substitutionなし

Implementation-path STOPは、固定Actions環境と最大1件の登録済みwiring patch後にもdependency/install/import/instantiateがsemantic変更なしで成立しない場合のみ。Actionsやpackage indexの一時障害は再試行対象であり科学的STOPではない。

## Evidence boundary

- Kimi K3全体の利得をAttnRes単独へ帰属しない。
- 著者一次証拠は約194M active未満で未確立。
- parameter overhead、KV cache非増加、漸近FLOPsだけでCPU軽量性を主張しない。
- 言語品質、CPU Pareto、量子化、知能原理、高校生級、能力進歩、1GB目標達成は未主張。