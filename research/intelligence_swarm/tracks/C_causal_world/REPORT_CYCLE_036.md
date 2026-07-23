# 系列C Cycle 036

## 仮説

**Object-Selective Causal Parent Sets from Double-Intervention Difference-in-Differences**  
（object・value二重介入の差の差による対象選択的因果親集合）

Cycle 035ではcommand介入とstate介入の順序交換子を監査したが、可換diagramはsurface-local候補を削減するだけで、object・state support・value bindingを形成しなかった。

次案の単純なobject/value二重swapは、系列B Cycle 036の複数介入trace商化と中心機構が重なるため棄却した。今回は系列C固有の問いとして、二対象を同時に含むworld stateを導入し、value介入効果がcommand objectによって選択的にgateされる **object×value交互作用** を因果親集合の条件とした。

## 重複表

| 系列 | 最新中心 | Cで扱わない領域 |
|---|---|---|
| A | 複数sensorの予測誤差輸送 | 時間予測状態・再帰更新 |
| B | 複数介入traceのbisimulation商文法 | MDL・program quotient |
| D | 双方向replay残差からのmemory address birth | 長期memory・統合 |
| E | Frustration hyperedgeからのnode birth | Energy固定点・局所力学 |
| **C** | **object指定がvalue→state効果を選択的にgateする因果親集合** | 今回の固有対象 |

## 設計

各episodeのbeforeは二対象を同時に含む。

- 対象1の状態値
- 対象2の状態値
- commandで指定されたobject
- commandで指定されたnew value
- afterでは指定対象だけ更新

Inductionから相対境界proposalを生成し、独立probe上で2×2介入gridを監査した。

1. 元object・元value
2. 元object・別value
3. 別object・元value
4. 別object・別value

因果親集合の支持条件は次の通り。

- 元objectではvalue swapに応じて同一state supportが変化
- object swap後は元supportへのvalue効果が消失
- value効果とobject gateの交互作用が複数probeで再現
- Final test outcomeは候補生成・rankingに不使用

## 3 seed平均

| 条件 | Factorized 精度/wrong | Interaction 精度/wrong | Exact境界 | Wrong target | 候補数 |
|---|---:|---:|---:|---:|---:|
| 既知 | 0.2500 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.00 |
| 未知語順 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.00 |
| 未知語彙 | 0.2500 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.00 |
| Rename | 0.2500 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.00 |
| 別状態表現A | 0.2500 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.00 |
| 別状態表現B | 0.2500 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.00 |
| 入れ子 | 0.2500 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.00 |
| 主語省略 | 0.2500 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.00 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.00 |
| 計画変更 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.00 |
| 反実仮想 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 0.0000 | 0.00 |

追加診断：

- Raw proposal: 24.33
- Factorized parent set: 23.67
- Interaction parent set: 0.00
- Independent probe audit: 11825
- Factorized seen exact boundary / pair: 0.2500 / 0.2500
- Interaction model: 112 bytes
- Factorized model: 2709 bytes
- Interaction training: 0.183960 sec
- Factorized inference: 2.669 ms/example
- Interaction inference: 0.002141 ms/example
- Peak RSS: 111284 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### 二対象worldにするとfactorized baselineは限定的に正答

Factorized方式は既知・Rename・別状態表現・主語省略でaccuracy 0.25、exact boundary 0.25、wrong commit 0を示した。

これは二対象を同じbeforeへ置いたことで、単一対象templateよりtarget supportの局所差分が明瞭になったためである。ただし平均約350候補が残り、75%はtie/nullである。

### Object gateを要求すると全parent setが消失

Value介入の効果は候補support上で確認できたが、command objectを別対象へswapしても、現在のstate edit operatorは同じsupportへ作用し続けた。

その結果、object選択性と差の差交互作用を満たすparent setは全seedで0件になった。

> **現在のoperatorはcommand objectを因果親として使わず、state位置とvalue shapeだけで更新している。**

### Correct probeとshuffleが同じ空集合

Interaction方式もshuffled outcome方式もparent set 0、全条件null率1.0だった。

これは厳密なobject gateが正しい構造を選んだのではなく、候補生成器にobject→target support edgeが一件も存在しないことを示す。

### 主語省略の0.25はobject permanenceではない

Factorized方式の主語省略accuracy 0.25は前turn状態を使っていない。現在beforeの絶対・相対位置からtarget supportを当てたsurface-local信号である。

### 計画変更・反実仮想

Factorized方式も全面nullであり、撤回案と最終goal、実行worldと非実行worldを分離できない。

## 相関暗記と因果理解の反証条件

| 条件 | 結果 |
|---|---|
| 二対象worldでexact target support > 0 | Factorizedのみ達成 |
| Value swapで同一supportが共変 | 局所的に達成 |
| Object swapでtarget supportだけ切替 | 未達 |
| Object×value交互作用parent set形成 | 未達 |
| Correct probeとshuffleの能力差 | 未達 |
| 計画変更・反実仮想world分離 | 未達 |

したがってFactorizedの0.25は因果理解ではなく、二対象surface上の局所状態置換である。

## 既存研究との差

近年の因果表現学習は介入データから因果順序や不変表現を同定するが、観測変数・介入target・表現空間を前提とする。Object-centric world modelもobject tokenやslotを先に持つ。

本実験は、生の日本語からobject・value・state supportを生成し、二重介入の交互作用で因果親集合へ昇格させる上流問題を扱う。ただしobject edgeが候補生成器に存在せず、因果親集合形成には至らなかった。

## 資源量・計算量

- Proposal induction: `O(NL)`
- 2×2 intervention grid: `O(QFVO L)`
- Inference: `O(FVL)`
- Parent set上限: 32
- Value候補上限: 8
- Object候補上限: 6

1GB未満・factorized小規模5ms未満は達成。Interaction方式が極端に高速なのは、有効構造が圧縮されたためではなくparent setが全消失したためである。弱いスマートフォンCPU実機は未検証。

## 系列C固有の進展

> **二対象worldではstate supportの局所回収が初めて安定して0.25へ上がった。しかしcommand objectをswapしてもstate更新先が変わらず、現在の構造にはobject→support因果edgeが存在しないことを二重介入で直接反証した。**

## 他系列へ返す知見

- A: 複数sensor誤差を使う場合、command object channelがstate support選択を実際に変えるかを独立評価すべき。
- B: 複数介入traceを商化する前に、object swapがtarget supportを変えるtraceが候補集合に存在するか確認すべき。
- D: Memory addressのobject nodeがread/write supportを選択的に切り替えなければ、三部cycleはsurface接続に留まる。
- E: Object-value hyperedgeは、object swapでattractor supportが移動する交互作用を必須constraintにすべき。

## 次の仮説

**Object-Edge Birth from Target-Support Residual Transport under Paired Worlds**  
（対世界のtarget-support残差輸送によるobject edge創発）

1. 同じvalue commandでobjectだけ異なるpaired worldを生成
2. 誤ったsupportと正しいsupportの位置差をobject residual化
3. Command object境界からstate target境界へ残差を輸送
4. Object swapに追従してsupportを移動するedgeを新生
5. Correct paired world／shuffled pair／value-only／residualなしを比較
6. Edge除去で対応objectのtransitionだけが崩れることを必須化
7. Rename・別状態表現でobject edge転移を評価
8. 主語省略では前turn object edgeを再起動
9. 計画変更では撤回object-goal edgeを抑制
10. 反実仮想では実行・非実行worldへ同じobject edgeを適用

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
