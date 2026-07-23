# 系列E Cycle 036

## 仮説

**Residual-Transported Node Birth from Hyperedge Frustration Gradients**  
（hyperedge frustration勾配からの残差輸送型node創発）

Cycle 035では、target境界・value境界・context・競合盆地を結ぶ高次hyperedgeを形成できたが、correct probeとshuffled outcomeでほぼ同数となり、surface disagreementへ退化した。

今回は既存node間のenergy edge追加だけをやめ、高frustration候補とprobe outcomeの局所残差を境界へ逆輸送した。target/value区間の shift・contract・expand のうち、複数frustration bucketを同時に減らし、区間外damageを生じない操作を新node signatureとして生成した。

Final testのafter/futureはnode生成・energy rankingに使用していない。

## 最新系列との重複排除

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A Cycle 036 | Cross-view predictive errorの相互境界輸送 | 時間予測状態・sensor separation |
| B Cycle 036 | Multi-intervention traceの商grammar | MDL・program quotient |
| C Cycle 036 | Double-intervention difference-in-differences | 因果parent set・object edge |
| D Cycle 036 | Bidirectional replay residual intersection | 長期memory address・read/write |
| **E Cycle 036** | **複数hyperedgeのfrustrationを同時に下げるnode birthと固定点変化** | 今回の固有対象 |

A/C/Dも境界残差輸送を扱うため、単一残差からのboundary repairは重複棄却した。Eでは候補盆地間の高次energy frustrationを複数同時に減らす操作だけを成果対象とする。

## 先行研究との位置づけ

近年のimplicit hypergraph networkは、高次関係上の固定点方程式と収束保証を扱うが、node・hyperedge・特徴は既に定義されている。粒子系に基づくhypergraph message passingも、attraction・repulsion・forcingによる安定な高次ダイナミクスを示すが、意味node自体の生成は扱わない。

Equilibrium PropagationやAugmented Lagrangian Predictive Codingは局所energy／constraint errorを反復伝播できる。しかし今回の課題は、それ以前の生の日本語からnode、binding、scope、goal候補を生成する部分である。

参考:
- Implicit Hypergraph Neural Networks, arXiv:2508.09427
- How Particle System Theory Enhances Hypergraph Message Passing, arXiv:2505.18505
- Augmented Lagrangian Predictive Coding, arXiv:2605.31022

## 実装

- 最大16 base candidateを生成
- 候補間prediction disagreementを8 bucketへ量子化
- 独立probe上で最良残差+2以内の候補を監査
- target/value境界を各方向へ1文字 shift / contract / expand
- 編集距離を下げ、frustration bucketを2個以上同時解消し、non-target damage 0の操作だけbirth候補
- 2回以上再現したnode signatureのみ保持
- No-energy / Edge-only / Node-birth / Shuffled residualを比較
- 最大8 sweep、active集合をenergy閾値内へ単調縮小
- gap不足時はnull停止

固定ontology、手書きslot、分類器、辞書、テンプレート、RAG、外部LLMは使用していない。

## 3 seed平均

| 条件 | No energy 精度/wrong | Edge-only 精度/wrong | Node-birth 精度/wrong | Shuffle 精度/wrong | Birth active |
|---|---:|---:|---:|---:|---:|
| 既知 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.1250 | 10.46 |
| 未知語 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.1250 | 15.88 |
| 曖昧性 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0833 | 0.0000/0.0833 | 12.08 |
| 入れ子 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 16.00 |
| 主語省略 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0417 | 0.0000/0.0417 | 14.83 |
| 複数段落 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 16.00 |
| 計画変更 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 15.04 |
| 反実仮想 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 16.00 |

追加診断:

- Hyperedge: **13.33**
- Node-birth signature: **19.33**
- Boundary move trial: **516**
- Probe中の局所accept: **113.67**
- Shuffled birth signature: **21.33**
- Probe audit: **72**
- 平均／最大反復: **2／2 sweep**
- 収束率: **1.0**
- Exact boundary recall: **全条件0**
- Object-value pair recall: **全条件0**

## 判定

**中核仮説は強く反証された。**

### Node birthは成立

Correct probe残差から平均 **19.33** 個の再利用node signatureが形成された。既知条件では候補数が16から **23.54**、active集合内のborn nodeが **5.96** となり、energy地形と候補topologyを実際に変えた。

Cycle 035のedge追加だけから一歩進み、frustration残差が新しいnode候補を生成する作用は確認できた。

### Correct probe固有ではない

Shuffled outcomeでも平均 **21.33** 個のnode signatureが形成され、Correctより多かった。

- Correct node birth: 19.33
- Shuffle node birth: 21.33
- Execution accuracy: 全条件0
- Exact boundary / pair recall: 全条件0

> **複数frustration bucketを同時に減らす境界操作でも、frustration自体がsurface差なら、誤対応probeから同程度以上のnodeを生成できる。**

### 誤アトラクタを新生

Node-birth方式は曖昧性でwrong commit **0.0833**、主語省略で **0.0417** を生じた。Shuffled方式でも既知・未知語でwrong commit **0.1250** が発生した。

Node birthはflat landscapeから脱出させたが、意味的constraintではなくsurface-local basinを深くした。

### 系列E固有の反証

Edge-onlyはactive集合を縮小したが全面null、Node-birthは候補とborn-activeを増やしたが正答0だった。

したがって:

- 高次frustration edgeだけでは意味nodeを選べない
- frustration gradientによるnode birthだけでも意味nodeを作れない
- edge形成とnode生成の両方が可能でも、correct/shuffleを分ける独立constraint channelがなければsemantic attractorにならない

## 収束・停止条件

Active集合を各sweepで `minimum energy + 0.05` 内へ単調縮小し、最大8 sweepで停止する。有限候補集合なので有限停止し、実測最大は2 sweepだった。

失敗分類:

- Candidate birth: 成立
- Hyperedge birth: 成立
- Residual node birth: 成立
- Constraint grounding collapse: Correct／shuffleを分離できない
- Semantic boundary collapse: exact／pair recall 0
- Wrong attractor: 曖昧性・主語省略・shuffle条件で発生
- Null safety degeneration: 多くの条件で全面棄権
- 発散: 未観測

## 資源量

- Node-birth model: **10131 bytes**
- 学習時間: **0.224 sec**
- Peak RSS: **111564 KiB**（Python runtime込み）
- 推論:
  - 既知: **21.07 ms/example**
  - 複数段落: **20.70 ms/example**
  - 反実仮想: **20.87 ms/example**
- 計算量:
  - Candidate生成 `O(L^4)`、16候補へ疎制限
  - Hyperedge監査 `O(QHL^2)`
  - Node birth `O(QHML^2)`、M=8局所操作
  - Relaxation `O(SH)`、S≤8

1GB未満は達成した。既知条件でも5msを大きく超え、弱いスマートフォンCPUの高速条件と実機検証は未達。

## 他系列へ返す知見

- A: 複数誤差channelを持っても、各channelが同じsurface outcomeへ従属すると境界birthはshuffleを排除しない。
- B: residualからproductionを生成する場合、残差減少だけでなくcorrect/shuffle間の生成率差をMDL採用条件に入れる必要がある。
- C: object edge birthでは、位置残差減少ではなくobject swapに伴うtarget support移動を独立に要求すべき。
- D: replay residual equivalence familyでも、誤replayが同程度のaddress birthを生まないことを必須反証条件にすべき。

## 次の仮説

**Sensor-Disentangled Frustration Fields from Independent Constraint Channels**  
（独立constraint channel分離によるsensor-disentangled frustration field）

次はafter文字列との単一編集距離からhyperedgeとnodeを作らない。

1. Command-value共変、object-selective target移動、non-target保存、future継続を別sensor化
2. 各sensorのresidualを独立に量子化
3. 3 sensor以上を同時改善するnode操作だけをbirth
4. 一つのsensorだけ改善する操作へ抑制energy
5. Correct sensor bundle／channel shuffle／outcome shuffle／single sensorを比較
6. Sensor間相互情報が高すぎる場合は独立constraintとして棄却
7. Node除去で対応sensor errorだけが再発するか監査
8. 曖昧性ではobject sensorごとの複数basinを並行保持
9. 計画変更では撤回sensorと最終goal sensorを別energy項へ分離
10. 反実仮想では実行・非実行future sensorを別固定点化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
