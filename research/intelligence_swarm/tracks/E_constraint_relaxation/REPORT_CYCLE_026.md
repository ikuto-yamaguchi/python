# 系列E Cycle 026 研究報告

## 仮説

**Residual-Mediator Constraint Hyperedges from Triadic Energy Synergy**  
（三者energy相乗効果からの残差媒介constraint hyperedge）

Cycle 025ではobject候補を固定した際のvalue順位変化からconstraint edgeを生成しようとしたが、edgeは0件だった。今回はobject-value間を直接結ばず、after/futureの未説明残差区間を第三nodeとして生成し、三者共同のenergy低下がobject単独・value単独の効果の和を超える場合だけhyperedge候補化した。

## 重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A | 局所残差routingによるpredictive responsibility | 談話commitment・予測状態 |
| B | Minimal negative witness cutによるbinding graph選択 | 実行program・MDL |
| C | 双方向局所alignmentによるpositive witness birth | 因果transition identity |
| D | Shapley-sparse memory credit set | 長期memory coalition |
| **E** | **object-value-residual三者のenergy相乗効果と固定点緩和** | 今回の固有対象 |

## 先行研究整理

Equilibrium Propagationはfree phaseとnudged phaseの固定点差から局所creditを得るが、状態変数とenergy topologyは定義済みである。2025年のLagrangian-based EPは時間変化系へ拡張し、forward-only・局所学習を維持できる境界条件を整理した。2026年のdissipative dynamics版EPは減衰力学へ局所学習を拡張した。Implicit Hypergraph Neural Networksはhyperedge上の固定点推論に収束条件を与えるが、hypergraph自体は入力として与えられる。2026年のIsing-EP hybridは局所最適をphase-space contractionの問題として扱うが、候補node創発は対象外である。

今回の問題は、それらより上流の、生の日本語spanからnodeとhyperedgeを同時生成できるかである。

## 実験条件

- seed: 1 / 7 / 19
- train: 96例 / seed（既知48 + 未知語48）
- test: 36例 / split / seed
- object候補上限4、value候補上限4、residual候補上限8
- state上限64、active上限16、最大6 sweep
- ablation: Base pair energy / Triadic hyperedge / Hyperedge + Null
- 条件: 既知、未知語、曖昧性、入れ子、主語省略、複数段落、計画変更、反実仮想

## 3 seed平均

| 条件 | Base精度 | Hyperedge精度 | Hyperedge+Null率 | Pair recall |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 未知語 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 曖昧性 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 入れ子 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 主語省略 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 複数段落 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 計画変更 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 反実仮想 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

追加診断:

- Hyperedge: 110.00
- Model: 2,612 bytes
- Training: 0.165767 sec
- 既知 inference: 0.569 ms/example
- 複数段落 inference: 0.744 ms/example
- 平均sweep: 2.00
- 平均active: 16.00
- Peak RSS: 111,000 KiB級（Python runtime込み）

## 判定

**中核仮説は強く反証。**

### Hyperedgeは多数形成されたが能力増分0

平均110件のtriadic hyperedgeが形成された。しかしBase / Hyperedgeは全splitでaccuracy・pair recall・wrong commitが完全に同一だった。形成数は構造創発の証拠ではなく、energy定義が作る相乗scoreを大量に記録しただけだった。

### 三者相乗効果が手続き的

Residual nodeはafter/future内の「beforeに無いsubstring」から生成した。Objectとvalueが明示されると、同じ文字列重なりがafter/future energyを同時に下げるため、joint reductionが単独効果の和を超えやすい。

> **観測文字列から同時に作られた三者の相乗効果は、共有潜在状態ではなく共通surface sourceに由来する。**

### 正答候補を選べない

既知を含む全条件でpair recall 0だった。Candidate generatorは短い部分spanを優先し、完全object/value境界を保持できていない。Hyperedge以前に候補崩壊が支配的だった。

### Hyperedgeはlandscapeを変えない

学習hyperedge keyは学習時の具体的 `(object span, value span, residual span)` に結び付いている。held-out入力ではexact key一致がほぼ起きず、edge creditが固定点energyへ作用しなかった。これはsemantic hyperedgeではなくepisodic triple memoryである。

### Nullは全面棄権

Hyperedge+Nullは全条件でwrong commit 0、null率1.0、accuracy 0だった。安全停止のみ。

## Hopfield・既存NNとの差

固定patternを想起するだけでなく、入力ごとにobject/value/residual候補を生成し、三者hyperedge付きenergyを反復最小化する点は単純Hopfield記憶とは異なる。ただし現在は手続き的substring energyであり、学習された連続energy network、正式なEP local update、意味node間の力学ではない。

## 収束・停止条件

各sweepでactive setを `best_energy + 0.08` 以内へ収縮し最大16状態に制限する。active set不変または最大6 sweepで停止するため有限停止する。

失敗分類:

- 候補崩壊: 完全object/valueが候補外
- Hyperedge汎化崩壊: exact triple keyがheld-outへ移らない
- 相乗効果崩壊: 共通surface sourceを潜在constraintと誤認
- 局所最適: Nullなしではjunk pairへ安定収束
- Null安全停止: 全面棄権
- 発散: 未観測

## 資源

- Model: 2,612 bytes
- Peak RSS: 約111 MiB（Python runtime込み）
- Training: 0.165767 sec
- Inference: 既知0.569 ms / 複数段落0.744 ms
- Hyperedge: 110
- 平均反復: 2.0
- 平均active: 16.0
- 計算量: candidate `O(L²)`、triadic audit `O(NORV)`、relaxation `O(SH)`

1GB未満・5ms未満は小規模制御条件で達成。弱いスマートフォン実機は未検証。

## 系列E固有の進展

> **第三の残差nodeを導入するだけではconstraint hyperedgeにならない。三者が同じ観測文字列から生成されると、相乗効果は共通原因によるsurface leakageになる。Residual nodeは候補から独立した予測器の未説明誤差として生成する必要がある。**

## 他系列へ返す知見

- A: residual nodeをcommitment候補と同じ文字列源から作ると責任routingが自己参照になる。
- B: negative witness cutはprogram候補から独立した観測差でなければtieを解けない。
- C: alignment residualをsource/target spanから直接作るとpositive witnessを自明化する。
- D: coalition lossは同じsurface addressから派生した要素間で偽synergyを作り得る。

## 次の仮説

**Predictor-Independent Residual Nodes from Cross-View Leave-One-Channel-Out Error**

1. Before+commandからafterを予測する局所予測器を形成
2. Before+commandからfutureを別予測器で形成
3. 一方のviewを除いたときだけ増える予測誤差区間をresidual node化
4. Object/value候補生成器とresidual生成器の入力channelを分離
5. Object+value+residualのjoint energy reductionがindependent baselinesを超える場合のみhyperedge化
6. Held-out surfaceでexact span一致なしに応答signatureが再現するか測定
7. Free/nudged phaseのhyperedge-local correlation差でweight更新
8. 候補recall、hyperedge transfer、ambiguity/plan/counterfactual accuracyを主評価化

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
