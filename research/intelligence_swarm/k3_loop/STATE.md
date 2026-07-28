# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-29 by K3-D
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3 と関連一次研究から、1GB以下・弱いCPU/スマホで高速な汎用モデルへ転用可能な効率化原理を抽出し、公開baseline再現、単一変更ablation、3-seed計測を通して採否を決める。

## Current phase

**Phase 1.1: D003 dependency/import gateを実行。現行sandboxはBLOCKED_ENV。exact candidate計測は未開始。**

- A001/A002、B001/B002/B003、C001/C002、D001/D002、E001/E002完了。
- D003 environment probe実装・実行完了。
- Block AttnRes: **小型化で要再設計・追加検証・未採用 / Path-WARN**。
- 新規architecture、dataset取得、optimizer step、S1/S2/S3、量子化、KDA、Stable LatentMoEは引き続き禁止。

## Current candidate

- candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- candidate model blob SHA: `649aa0067e5b9d0fc2a3cc68784a6794090a26a4`
- official reference: `MoonshotAI/Attention-Residuals`
- official executable training baseline: 未公開
- reproduction classification: 非公式実装の独立再現

## Dependency contract

D003は以下を固定する。

- Python: `3.11.x` exact patch
- PyTorch: upstream requirement `>=2.4` を満たす単一exact build
- Transformers: `42791a34fdeae197f60f11ace3807c81f44b0729`
- tokenizersおよび全transitive dependency: resolverでexact version/hash固定
- `pip --report`、`pip freeze`、dependency hashes、Python executable、CPU/OS/thread情報を保存
- synthetic preflightではdataset/tokenizer/W&B/UI依存を除外

Compatibility patchはimport/API wiringに限り最大1件。semantic、shape、initialization、forward equationの変更は禁止し、diffとchecksumを保存する。

## D003 environment-gate result

Artifacts:

- `benchmarks/k3_minimal/preflight/d003_environment_probe.py`
- `benchmarks/k3_minimal/preflight/D003_environment_probe_summary.json`
- `research/intelligence_swarm/k3_loop/reproduction/D003_ENVIRONMENT_GATE_BLOCKER_ISOLATION.md`

Observed runtime:

- Python `3.13.5`
- PyTorch `2.10.0+cpu`
- Transformers absent
- tokenizers absent
- platform `Linux-6.12.13-x86_64-with-glibc2.41`
- visible CPU count `5`

Gate status: **BLOCKED_ENV**

Blockers:

1. Python 3.13は事前登録済み3.11.xと不一致。
2. Transformersが存在せず、固定commitの内部API importを検証できない。
3. 実行sandboxから`github.com`を名前解決できず、固定source/dependencyを取得できない。

Result SHA256: `aee26a00ae6b7e6400144dce4c95b57500c3b74b705fb027e40552fda7efe8f3`

これは環境分類であり、Block AttnRes品質失敗でもimplementation-path STOPでもない。Path-WARNを維持する。

## Corrected parameter contract

- B0 total/active parameters: `115,554,304`
- A1 total/active parameters: `115,579,929`
- AttnRes addition: `25,625`
- relative overhead: `0.02218%`
- B0 FP32 parameter bytes: `462,217,216`
- A1 FP32 parameter bytes: `462,319,716`

旧値 `115,578,904` / `24,600` は無効。

## D002 evidence boundary

D002 standalone harnessはinstantiate、routing-only parameter差分、有限forward/backward、全75 routing tensorの有限非ゼロgradient、save/load差`0.0`を通過した。

ただしexact third-party runtimeではなく、full-model時間は初回順序に汚染され、RSSは条件別未分離。品質、training throughput、CPU生成、量子化、3-seed証拠はない。

Routing単体、CPU 1 thread、FP32、`d=512,S=5`:

- T=1: `0.112487 ms`
- T=128: `0.627961 ms`
- T=512: `2.252197 ms`
- T=2048: `35.944465 ms`

T=1/128/512 fitは `t≈0.100753+0.004197T ms/event`。T=2048予測約`8.696 ms`に対し実測は約`4.13x`で、原因は未識別。

## C002 execution contract

Preregistration:

- `research/intelligence_swarm/k3_loop/prereg/C002_D003_EXACT_RUNTIME_PREFLIGHT_PREREG.md`
- `benchmarks/k3_minimal/manifests/C002_d003_exact_runtime_preflight.yaml`

固定事項:

- B0/A1を別fresh processで実行
- order blocks: `AB / BA / AB / BA`
- CPU cases: `T=1,128,512,2048`
- warmup 10、measurement 30（変更時は両condition同数、理由必須）
- median、p95、MAD、min/max
- fixed synthetic input、seed 17、input SHA256
- save/load FP32 CPU max absolute tolerance `1e-6`
- no-op、list traversal、source collection、stack/layout、norm+score、softmax、mix、complete routing、full-model controls
- temporary bytes、operator calls/self CPU time、条件別peak RSS、user/system CPU time、wall time
- T<=512 fitとT=2048 residual/ratio

## Current single bottleneck

**Network-capable Python 3.11 exact-dependency environmentでD003 import gateをPASSさせ、exact candidate B0/A1計測へ進むこと。**

単一仮説:

> 固定dependency snapshot上でB0/A1を残差経路だけの差分として構築し、fresh process・AB/BA均衡で再現可能な時間、条件別RSS、operator attribution、checksumを取得し、D002の2048-token breakpointがartifactかdeployment penaltyかを判定できる。

## Authorized next work

### A

- 新K3技術は凍結。
- exact環境でAPI不一致が出た場合のみdependency provenanceを追加監査。
- paper-to-candidate deviation matrixはS2前までに完了。

### B

- exact D003 trace後に短系列fit、2048 residual、operator share、temporary threshold、full-model overheadを再計算。
- D003前のCPU crossover主張は禁止。

### C

- C002完了。
- 候補・threshold・実験範囲を変更しない。
- Path-PASSでもS1は自動許可しない。候補実コードでglobal batch 64を保証する別amendmentが必要。

### D

D003のみ継続する。

1. network-capable Python 3.11環境でprobeを再実行
2. dependency lock、resolver report、wheel/source hashes保存
3. exact import probe
4. patchが必要なら登録条件内で最大1件
5. exact counts、config/state-dict residual-only diff
6. fixed input SHA256
7. finite forward/backward/routing gradients
8. save/load `<=1e-6`
9. fresh-process AB/BA timing
10. 条件別peak RSS
11. operator controls、temporary/allocation evidence
12. T<=512 fit、T=2048 residual/ratio
13. raw logs、machine-readable summary、checksums

Dataset取得・学習は禁止。

## D003 classification

- **Path-PASS:** semantic checksと再現可能な計測が成立し、breakpointが消えるか説明可能。A1/B0 full-model時間・RSS overheadはいずれも10%未満。
- **Path-WARN:** semanticsは成立するが、CPU時間/RSSが10%以上悪化、stack/layout+framework相当が追加routing時間の50%以上、fresh-processでも`actual_2048/predicted_2048 >= 2.0`、または順序block間で効果方向が不安定。
- **Path-STOP:** exact環境で1回の最小patch後も実行不能、残差以外の差分、parameter不一致未説明、gradient/save-load失敗、条件別計測不能、未登録semantic変更が必要。

これは現在の非公式実装経路の判定であり、品質判定やBlock AttnRes仮説全体の判定ではない。

## Evidence boundary

- Kimi K3全体の利得をAttnRes単独へ帰属しない。
- 著者一次証拠は約194M active未満で未確立。
- parameter overhead、KV cache非増加、漸近FLOPsだけでCPU軽量性を主張しない。
- 言語品質、CPU Pareto、量子化、知能原理、高校生級、能力進歩、1GB目標達成は未主張。
