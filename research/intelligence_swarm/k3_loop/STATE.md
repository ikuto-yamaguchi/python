# K3 Minimal Intelligence Loop — Shared State

Last updated: 2026-07-28 by K3-E
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Objective

Kimi K3 と関連一次研究から、1GB以下・弱いCPU/スマホで高速な汎用モデルへ転用可能な効率化原理を抽出し、公開baseline再現、単一変更ablation、3-seed計測を通して採否を決める。

## Current phase

**Phase 1.0: D002をPath-WARNとして統合し、D003 exact-dependency fresh-process preflightのみ許可。**

- A001、B001/B002、C001、D001/D002、E001/E002完了。
- Block AttnRes: **追加検証・未採用**。
- 新規architecture、S1/S2/S3、KDA、Stable LatentMoEは引き続き禁止。

## E002 decision

D002は以下を通過した。

- B0/A1 instantiate
- AttnRes routingだけのparameter-name差分
- finite forward/backward
- 全75 routing tensorの有限・非ゼロgradient
- save/load出力差 `0.0`
- operator/resource/checksum記録

ただし、exact third-party Transformers実装ではなくstandalone再構成であり、full-model時間は初回実行順序に汚染され、RSSも条件別に分離されていない。品質、training throughput、CPU生成、量子化、3-seed証拠もない。

したがって現在の非公式実装経路は停止せず、**Path-WARNを維持してD003へ進む**。D002は実行可能性の予備確認であり、採用や性能改善の証拠ではない。

## Corrected parameter contract

- B0 total/active parameters: `115,554,304`
- A1 total/active parameters: `115,579,929`
- AttnRes addition: `25,625`
- relative overhead: `0.02218%`
- B0 FP32 parameter bytes: `462,217,216`
- A1 FP32 parameter bytes: `462,319,716`

旧値 `115,578,904` / `24,600` は無効。

## Current single bottleneck

**D003 exact-dependency, fresh-process, order-balanced resource/operator preflight**

単一仮説:

> 固定した非公式候補をexact dependency環境でB0/A1として構築し、残差経路以外を変えず、fresh process・交互順序で再現可能な時間、条件別RSS、operator attribution、checksumを取得できる。

## Authorized next work

### A

- 新K3技術を凍結。
- 候補コードのimport/API使用から、最小のPython/PyTorch/Transformers互換tupleと根拠を固定。

### B

- D002 traceからoperator-share評価項目を整備。
- D003前のCPU crossover主張は禁止。

### C

C001を次だけ修正する。

- A1=`115,579,929`、delta=`25,625`
- D003実行方法とenvironment lock
- save/load tolerance
- PASS/WARN/STOP schema
- CPU固定条件とoperator fields
- 将来S1のglobal batch 64実現方法
- S1は許可しない

### D

D003のみ実行する。

- exact candidate dependency runtime
- B0/A1を別fresh processで実行
- 同一warm-up後に順序を交互化
- fixed synthetic inputとSHA256
- 条件別peak RSSとwall time
- no-op/list traversal/stack-only/norm+score/softmax/mix controls
- parameter/config diff、raw logs、checksums
- dataset取得・学習は禁止

## D003 completion conditions

1. environment lockとdependency provenance
2. candidate commitと最小互換patchのdiff/checksum
3. exact parameter countとresidual-only diff
4. fixed input SHA256
5. finite forward/backward/routing gradients
6. preregistered tolerance内のsave/load一致
7. fresh-process・order-balanced timing
8. 条件別peak RSS
9. operator controlsとtemporary tensor evidence
10. machine-readable summary、raw logs、checksums

## D003 classification

- **Path-PASS:** exact runtime、residual-only差分、再現可能な条件別計測が成立。
- **Path-WARN:** semanticsは成立するがCPU時間/RSSが悪化。目安はA1がB0より10%以上悪化、またはstack/layout+frameworkが追加routing時間の50%以上。この場合はtraining-onlyまたはfusion前提へ狭義化。
- **Path-STOP:** 1回の明示的な最小互換修正後も実行不能、残差以外の差分、gradient/save-load失敗、資源分離不能、semantic変更が必要。

これは実装経路の判定であり、品質の判定ではない。

## Evidence boundary

- Kimi K3全体の利得をAttnRes単独へ帰属しない。
- 著者一次証拠は約194M active未満で未確立。
- 公式repositoryには再現可能なtraining baselineがない。
- 候補は `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`。
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