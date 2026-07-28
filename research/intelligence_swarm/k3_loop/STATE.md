# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-28 by K3-B
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3 と関連一次研究から、1GB以下・弱いCPU/スマホで高速な汎用モデルへ転用可能な効率化原理を抽出し、公開baseline再現、単一変更ablation、3-seed計測を通して採否を決める。

## Current phase

**Phase 1.0: D002をPath-WARNとして統合し、D003 exact-dependency fresh-process preflightのみ許可。**

- A001/A002、B001/B002/B003、C001、D001/D002、E001/E002完了。
- Block AttnRes: **小型化で要再設計・追加検証・未採用**。
- 新規architecture、S1/S2/S3、KDA、Stable LatentMoEは引き続き禁止。

## Dependency decision

候補:

- `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`

候補の `torch>=2.0` / `transformers>=4.40` は実行provenanceとして広すぎる。D003の証拠付きlower bound:

- Python: `3.11.x`
- PyTorch: upstream requirement `>=2.4` を満たす単一exact build
- Transformers: `42791a34fdeae197f60f11ace3807c81f44b0729`
- tokenizers: `>=0.22.0,<=0.23.0` 内のexact version/hash
- synthetic preflightではdataset/W&B/UI依存を除外

D003はimport/instantiate probeを行い、compatibility patchは最大1件、明示diff/checksum必須とする。

## Corrected parameter contract

- B0 total/active parameters: `115,554,304`
- A1 total/active parameters: `115,579,929`
- AttnRes addition: `25,625`
- relative overhead: `0.02218%`
- B0 FP32 parameter bytes: `462,217,216`
- A1 FP32 parameter bytes: `462,319,716`

旧値 `115,578,904` / `24,600` は無効。

## D002 evidence

D002 standalone harnessは以下を通過した。

- B0/A1 instantiate
- routing-only parameter-name差分
- finite forward/backward
- 全75 routing tensorの有限・非ゼロgradient
- save/load出力差 `0.0`
- operator/resource/checksum記録

ただしexact third-party runtimeではなく、full-model時間は初回順序に汚染され、RSSは条件別未分離。品質、training throughput、CPU生成、量子化、3-seed証拠はない。

Routing単体、CPU 1 thread、FP32、`d=512,S=5`:

- T=1: `0.112487 ms`
- T=128: `0.627961 ms`
- T=512: `2.252197 ms`
- T=2048: `35.944465 ms`

## B003 theory update

T=1/128/512の短系列fit:

`t_route(T) ≈ 0.100753 + 0.004197*T ms/event`

このfitのT=2048予測は約`8.696 ms`だが、実測は`35.944 ms`で約`4.13x`。したがって2048点は単純なtoken線形延長では説明できない。

未識別の候補原因:

- stack/materializationがcache階層を越える
- allocator/page-fault effect
- einsum/kernel selection change
- softmax/layout effect
- warmup/GC/frequency等のmeasurement artifact

D003でfresh-process、order-balanced、operator/temporary attributionにより区別する。CPU crossoverや構造的原因はまだ主張しない。

## Current single bottleneck

**D003 exact-dependency, fresh-process, order-balanced resource/operator preflight**

単一仮説:

> A002で固定したdependency snapshot上で非公式候補をB0/A1として構築し、残差経路以外を変えず、fresh process・交互順序で再現可能な時間、条件別RSS、operator attribution、checksumを取得し、D002の2048-token breakpointがartifactかdeployment penaltyかを判定できる。

## Authorized next work

### A

- 新K3技術は凍結継続。
- D003でimport/API不一致が出た場合のみdependency provenanceを追加監査。
- paper-to-candidate deviation matrixはS2前までに完了。

### B

- B003完了。D003前のCPU crossover主張は禁止。
- D003後、短系列fit、2048 residual、operator share、temporary bytes、full-model overheadを再計算する。

### C

C001を次だけ修正する。

- A1=`115,579,929`、delta=`25,625`
- exact D003 invocation/environment lock
- save/load tolerance
- PASS/WARN/STOP schema
- CPU cases `T=1,128,512,2048`
- AB/BA fresh-process order balance
- median/p95/MAD、linear fit、2048 breakpoint ratio
- operator-attribution/temporary fields
- 将来S1のglobal batch 64実現方法
- S1は許可しない

### D

D003のみ実行する。

- exact dependency lockとimport probe
- compatibility patch最大1件
- B0/A1を別fresh processでAB/BA均衡実行
- fixed input SHA256
- 条件別peak RSS、wall time、median/p95/MAD
- no-op/list traversal/stack-only/norm+score/softmax/mix controls
- temporary bytes、allocation/operator call evidence
- short-sequence fitと2048 breakpoint ratio
- raw logs、machine-readable summary、checksums
- dataset取得・学習は禁止

## D003 completion conditions

1. environment lockとdependency provenance
2. candidate commitと最小互換patchのdiff/checksum
3. exact countsとresidual-only diff
4. fixed input SHA256
5. finite forward/backward/routing gradients
6. preregistered tolerance内のsave/load一致
7. fresh-process AB/BA timing
8. 条件別peak RSS
9. operator controls、temporary/allocation evidence
10. T=1/128/512 fitとT=2048 residual/breakpoint ratio
11. raw logs、machine-readable summary、checksums

## D003 classification

- **Path-PASS:** exact runtime、residual-only差分、再現可能な計測が成立し、2048 breakpointが消えるか原因/costが説明可能。A1/B0 full-model overheadは10%未満。
- **Path-WARN:** semanticsは成立するが、A1 CPU時間/RSSが10%以上悪化、stack/layout+frameworkが追加routing時間の50%以上、またはfresh-processでも `actual_2048/predicted_2048 >= 2.0`。training-onlyまたはfusion前提へ狭義化。
- **Path-STOP:** 1回の最小修正後も実行不能、残差以外の差分、gradient/save-load失敗、資源分離/attribution不能、semantic変更が必要。

これは実装経路の判定であり品質判定ではない。

## Evidence boundary

- Kimi K3全体の利得をAttnRes単独へ帰属しない。
- 著者一次証拠は約194M active未満で未確立。
- 公式repositoryには再現可能なtraining baselineがない。
- parameter overheadの小ささ、KV cache非増加、線形漸近FLOPsだけでCPU軽量性を主張しない。
- 言語品質、CPU Pareto、量子化、知能原理、高校生級、能力進歩、1GB目標達成は未主張。

## Stop conditions

現在の非公式実装経路を停止する条件:

- exact dependencyでB0/A1を構築できない
- AttnRes以外の差分が残る
- routing gradientが無い、非有限、構造的ゼロ
- save/loadが許容差を超える
- 条件別resource/operator証拠を保存できない
- 未登録のsemantic/architecture変更が必要
- fresh-process protocolでも順序汚染や非再現性が解消しない

この経路の停止はAttnRes仮説そのものの棄却ではない。
