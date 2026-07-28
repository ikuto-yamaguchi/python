# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-29 by K3-A
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3 と関連一次研究から、1GB以下・弱いCPU/スマホで高速な汎用モデルへ転用可能な効率化原理を抽出し、公開baseline再現、単一変更ablation、3-seed計測を通して採否を決める。

## Current phase

**Phase 1.3: D003 exact dependency/import gateをGitHub Actions上で固定し、paper-semantics variantとraw candidate artifactを分離する。**

- A001/A002/A003、B001/B002/B003、C001/C002、D001/D002、E001/E002/E003完了。
- 現行sandboxのD003 probeは `BLOCKED_ENV`。これは品質失敗でもimplementation-path STOPでもない。
- A003で、raw candidateに公式pseudocodeとの重大なsemantic deviationを確認した。
- Block AttnRes: **小型化で要再設計・追加検証・未採用 / Path-WARN**。
- unchanged raw candidate: **canonical paper reproductionとしては不適格。artifact diagnosticに限定**。
- 新規architecture、dataset取得、optimizer step、S1/S2/S3、量子化、KDA、Stable LatentMoEは引き続き禁止。

## Current candidate

- candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- candidate model blob SHA: `649aa0067e5b9d0fc2a3cc68784a6794090a26a4`
- audited `modeling_attnres.py` blob: `31faf5942b49470e857c0b7c688468ab5aa0751e`
- official reference: `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6`
- official executable training baseline: 未公開
- reproduction classification: 非公式実装の独立再現

## A003 semantic-deviation result

Official pseudocode requires the completed intra-block partial state to be appended and reset at a block transition. The current candidate appends the state after an MLP boundary but does not reset `partial_block`.

Consequences:

- the just-completed cumulative state remains both in `blocks` and as `partial_block` at the next routing event;
- the same representation is duplicated as two sources;
- subsequent stored blocks are cumulative prefixes rather than disjoint block-level partial sums;
- routing prior and gradients differ from the published block-partition mechanism.

The candidate additionally introduces a learned source-specific recency-logit bias absent from the official pseudocode and optional sigmoid/alpha mixing gates. A finite recency bias does not make the model mathematically identical to standard Qwen3 at initialization.

Required separation:

1. **PAPER-BLOCK variant** — preregistered minimal correction matching author pseudocode, with boundary reset, explicit source identities, no recency bias, and no optional mixing gate.
2. **CANDIDATE-RAW diagnostic** — unchanged third-party artifact, never attributed to paper Block AttnRes alone.

## Dependency contract

- Python: `3.11.x` exact patchをrunner実測で記録
- PyTorch: upstream requirement `>=2.4` を満たす単一exact build
- Transformers: `42791a34fdeae197f60f11ace3807c81f44b0729`
- tokenizersおよび全transitive dependency: exact version/hash固定
- `pip --report`、`pip freeze`、downloaded artifact hashes、Python executable、CPU/OS/thread情報を保存
- synthetic preflightではdataset/tokenizer model/W&B/UI依存を除外
- compatibility patchはimport/API wiringに限り最大1件。semantic、shape、initialization、forward equationの変更は禁止
- PAPER-BLOCK semantic correctionは互換patchとして黙って適用せず、独立したC amendmentとvariantとして登録する

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
- raw-candidate A1 total/active parameters: `115,579,929`
- raw-candidate AttnRes addition: `25,625`
- relative overhead: `0.02218%`
- B0 FP32 parameter bytes: `462,217,216`
- raw-candidate A1 FP32 parameter bytes: `462,319,716`

The PAPER-BLOCK parameter contract must be recomputed after removing recency-bias parameters and registering exact boundary semantics.

## Existing evidence boundary

D002 standalone harnessはraw candidateのrouting-only parameter差分、有限forward/backward、全75 routing tensorの有限非ゼロgradient、save/load差`0.0`を通過した。ただしexact third-party runtimeでもpaper-faithful semanticsでもなく、品質、training throughput、CPU生成、量子化、3-seed証拠はない。

Routing単体のD002値:

- T=1: `0.112487 ms`
- T=128: `0.627961 ms`
- T=512: `2.252197 ms`
- T=2048: `35.944465 ms`

T=1/128/512 fitは `t≈0.100753+0.004197T ms/event`。T=2048は予測の約`4.13x`で原因未識別。

## Current single bottleneck

**D003-GHA Stage 1 exact dependency/import gateをPASSさせ、続いてCがPAPER-BLOCK/CANDIDATE-RAW分離を事前登録すること。**

単一仮説:

> 固定GitHub Actions CPU jobとPython 3.11により候補互換dependency graphと内部APIを固定でき、その後、source identity traceによってpaper-semantics variantだけをcanonical residual-only比較へ進められる。

## Authorized next work

### A

- 新K3技術は凍結。
- Actions resolver/import probeで具体的不一致が出た場合のみdependency provenanceを追補。
- A003 paper-to-candidate deviation matrixは完了。

### B

- exact D003 trace後にfit、2048 residual、operator share、temporary threshold、paper/raw variant差を再計算。
- それ以前のCPU crossover主張は禁止。

### C

- GitHub Actions実行基盤を固定するC003 amendment/manifestを作る。
- runner image/provenance、Python 3.11、exact dependency lock、cache policy、artifact paths、environment PASS後のみmeasurementを許可する二段階gateを登録。
- 続くC004でPAPER-BLOCKとCANDIDATE-RAWを分離し、boundary indexing、partial reset、source identity、recency-bias禁止、optional gate禁止を登録。
- 候補以外のK3 component、品質threshold、base architectureは変更しない。S1は許可しない。

### D

D003-GHA Stage 1のみ先行実行する。

1. canonical branch checkoutとcommit SHA保存
2. Python 3.11 setup
3. exact dependency resolve/install
4. resolver report、freeze、artifact hashes、environment metadata保存
5. `d003_environment_probe.py`実行
6. 成否にかかわらずraw logs/artifacts upload

Stage 1 PASS後:

- tiny deterministic source traceを先に実行
- layer/sublayer、boundary、source count、source checksum、duplication、partial reset、recency bias、zero-query source weightsを保存
- CANDIDATE-RAWはdiagnosticに限定
- PAPER-BLOCK variantだけをcanonical semantic/resource gateへ進める
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

Semantic PASS:

- PAPER-BLOCK variantでregistered boundaryごとにpartial stateがresetされる
- completed sourceとcurrent partialに意図しないchecksum duplicationがない
- recency-logit biasとoptional mixing gatesがない
- source identitiesがauthor pseudocode contractと一致

Implementation-path STOPは、固定Actions環境と最大1件の登録済みwiring patch後にもdependency/install/import/instantiateがsemantic変更なしで成立しない場合のみ。Raw candidateのsemantic mismatch自体はBlock AttnRes仮説のSTOPではなく、variant分離を要求する。

## Evidence boundary

- Kimi K3全体の利得をAttnRes単独へ帰属しない。
- 著者一次証拠は約194M active未満で未確立。
- raw candidateの結果をpaper Block AttnResへ帰属しない。
- parameter overhead、KV cache非増加、漸近FLOPsだけでCPU軽量性を主張しない。
- 言語品質、CPU Pareto、量子化、知能原理、高校生級、能力進歩、1GB目標達成は未主張。
