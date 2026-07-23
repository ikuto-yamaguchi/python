# 系列E Cycle 037

## 仮説

**Constraint-Synergy Attractors from Selective Sensor Lesion Fields**  
（選択的sensor lesion fieldによる制約相乗アトラクタ）

Cycle 036ではhyperedge frustration残差からnode birthを起こせたが、correct outcomeよりshuffleの方がnode数が多く、意味constraintではなくsurface disagreementへ接地した。

系列A Cycle 037が既に5 sensorの3-of-5多数決によるpredictive state昇格を検証したため、同じ多数決方式は重複棄却した。本Cycleでは系列E固有の問いとして、個別sensorの加算では説明できない**非加法的synergy energy**が形成され、sensor lesionで対応する固定点だけが崩れるかを検証した。

## 開始時の重複比較

| 系列 | 最新中心 | Eで扱わない領域 |
|---|---|---|
| A Cycle 037 | 分離sensorの3-of-5 predictive state | 時間状態・carry・多数決昇格 |
| B Cycle 037 | quotient class内の残差production birth | MDL・program grammar |
| C Cycle 037 | paired-world object edge birth | 因果world・target選択edge |
| D Cycle 037 | replay-response equivalence address | 長期memory・read/write閉路 |
| **E Cycle 037** | **sensor間の非加法的energy synergyと選択的lesion** | 今回の固有対象 |

共有STATEでは高校生級、ネイティブ日本語コミュニケーション、弱いスマートフォン実機検証は未達。BACKLOGのP0である未知境界生成、介入整合性による候補競合、内部整合性と意味妥当性の分離を維持した。

## 先行研究整理

Implicit Hypergraph Neural Networksは高次関係を固定点方程式として解き、well-posednessと収束条件を与えるが、nodeとhyperedgeは事前に定義される。Augmented Lagrangian Predictive Codingは局所constraint errorをlayer-local multiplierへ蓄積し、深い系でも局所的にcreditを伝播するが、層・状態・constraint topologyが既知である。Generalized Lagrangian Equilibrium Propagationも時間変化系へ拡張するが、軌道変数と境界条件が与えられる。

今回の課題は、それ以前の生の日本語からnode・constraint・sensor identity自体を形成する問題である。

## 実装

入力ごとに最大12個のprospective state候補を生成し、独立probe上で以下の5 sensorを別channelとして監査した。

1. command内の値候補再現
2. inverse restoration
3. non-target保存
4. future継続trace
5. before・command・futureを跨ぐ共有anchor

比較方式:

- No energy
- 個別sensor加算energy
- 3/4 sensor組のjoint成功率が最大single成功率を上回るsynergy hyperedge
- channel独立shuffle
- future sensor lesion

Final testのafter/futureはcandidate生成・rankingに使用していない。

## 3 seed平均

| 条件 | No energy 精度/wrong | Additive 精度/wrong | Synergy 精度/wrong | Synergy active |
|---|---:|---:|---:|---:|
| 既知 | 0/0 | 0/0 | 0/0 | 12.00 |
| 未知語 | 0/0 | 0/0 | 0/0 | 12.00 |
| 曖昧性 | 0/0 | 0/0 | 0/0 | 12.00 |
| 入れ子 | 0/0 | 0/0 | 0/0 | 12.00 |
| 主語省略 | 0/0 | 0/0 | 0/0 | 12.00 |
| 複数段落 | 0/0 | 0/0 | 0/0 | 12.00 |
| 計画変更 | 0/0 | 0/0 | 0/0 | 12.00 |
| 反実仮想 | 0/0 | 0/0 | 0/0 | 12.00 |

追加診断:

- Probe sensor audit: **96 / seed**
- Single-sensor entry: **56.67**
- Correct synergy hyperedge: **0**
- Channel-shuffle synergy hyperedge: **0**
- Future-lesion対象hyperedge: **0**
- 候補数: **12**
- 平均／最大反復: **2／2 sweep**
- 収束率: **1.0**
- Exact boundary recall: **全条件0**
- Object-value pair recall: **全条件0**
- Null率: **全条件1.0**

## 判定

**中核仮説は強く反証された。**

### 非加法的synergyが一件も形成されない

個別sensor entryは形成されたが、3個または4個のsensorを同時に満たしたときのcorrect率が、最良の単独sensor correct率を上回る再利用可能な組は全seedで0件だった。

> 独立sensorを増やしても、各sensorが同じsurface置換候補へ従属している限り、非加法的な意味constraintは生まれない。

### Additive energyは地形だけ変える

既知条件のactive状態は12から5.44、未知語では6.67、曖昧性では5.06へ縮小した。しかしaccuracyは0、null率1.0のままである。

個別sensorの和は候補を削れるが、正しいattractorを形成しない。これは局所整合性の蓄積と意味的妥当性が異なるという失敗系列を再確認する。

### Lesion因果監査は開始不能

Synergy hyperedgeが0なのでfuture sensorをlesionしてもtopology・active集合・能力は変化しなかった。対応constraintを除去したときに対応能力だけが崩れるという因果必要性条件は、前提構造不在により未成立である。

### 主語省略・計画変更・反実仮想

- 主語省略: object permanenceなし
- 複数段落: 長距離constraintなし
- 計画変更: 撤回goalと最終goalの分離なし
- 反実仮想: 実行／非実行worldの固定点分離なし
- 曖昧性: 複数object basinの意味的競合なし

## 収束保証・失敗分類

Active集合を各sweepで最小energy+0.05以内へ単調縮小し、最大8 sweepで停止する。有限候補集合なので有限停止し、実測最大は2 sweepだった。

- Candidate birth: 12候補
- Single-sensor field: 成立
- Synergy hyperedge birth: **崩壊**
- Selective lesion necessity: 前提不在
- Semantic boundary: 崩壊
- Flat landscape: Synergy方式で全面tie/null
- Additive over-pruning: active縮小だが能力0
- 発散: 未観測

## Hopfield・既存NNとの差

固定patternの想起ではなく、入力ごとにprospective stateを生成し、独立constraint channelの単独・高次相互作用をenergyへ変換して反復緩和する設計である。Transformer attention、分類器、固定ontology、手書きslot、辞書、RAG、外部LLMは使っていない。

ただし現状は文字列区間置換に基づく小型離散prototypeであり、正式な平衡伝播networkや意味constraint topologyには未到達である。

## 資源量

- Synergy model: **5,671 bytes**
- Peak RSS: **111,336 KiB**（Python runtime込み）
- Training: **0.024966 sec**
- Inference:
  - 既知: **6.448 ms/example**
  - 複数段落: **10.314 ms/example**
  - 反実仮想: **12.033 ms/example**
- 推定計算量:
  - Candidate: `O(L^4)`、12候補へ制限
  - Sensor audit: `O(QH)`
  - Synergy探索: `O(QH Σ C(5,k))`, k=3,4
  - Relaxation: `O(SH)`, S≤8

1GB未満は達成。既知条件5ms未満、長文、弱いスマートフォンCPU実機は未達。

## 系列E固有の進展

> 個別constraint channelを分離しても、単独sensorが同じsurface候補へ従属する場合、非加法的なsynergy hyperedgeは形成されない。Energy-based推論へ進む前に、互いに異なる介入から生じる独立sensor nodeを生成する必要がある。

## 他系列へ返す知見

- A: 3-of-5 sensor多数決の既知surface信号は、非加法的synergy監査では支持されない。channel数ではなく独立介入由来かを確認すべき。
- B: sensor bundleを圧縮してもsynergy 0ならsemantic quotientにはならない。
- C: object-selective sensorがない状態でhigher-order constraintを作っても因果target edgeは形成されない。
- D: memory addressのread/write sensorを後から束ねるだけでは、共同必要性やsynergyは生まれない。

## 次の仮説

**Intervention-Orthogonal Sensor Birth from Actively Synthesized Constraint Queries**  
（能動合成constraint queryによる介入直交sensor創発）

次は既存episodeからsensor bundleを受動抽出しない。

1. 候補対が異なる結果を返す最小command/value/object摂動を能動生成
2. 応答共分散の低いquery集合を自律選択
3. Queryごとのcandidate partitionをsensor node化
4. 直交sensor間だけhigher-order hyperedgeを許可
5. Correct query／query shuffle／受動sensor／single-queryを比較
6. Sensor lesionで対応partitionだけが復元するか監査
7. Energy gap、exact boundary、pair recall、accuracy、wrong attractorを同時評価
8. 曖昧性・計画変更・反実仮想では異なるquery basinを並行保持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
