# 系列C Cycle 037

## 仮説

**Object-Edge Birth from Target-Support Residual Transport under Paired Worlds**  
（対世界のtarget-support残差輸送によるobject edge創発）

Cycle 036では二対象worldによりfactorized support回収が0.25へ上がった一方、command objectをswapしても更新supportが移動せず、object×value interaction parent setは0件だった。

今回はobject edgeの存在を前提に監査せず、独立paired probeで観測された「command objectが変わったとき正しいtarget supportがどこへ移るべきか」という位置残差を、command内object候補からstate support bucketへ輸送し、新edgeを生成できるか検証した。

Final testのafter/futureはcandidate生成・rankingに使用していない。

## 最新系列との重複排除

| 系列 | 最新中心 | Cで扱わない領域 |
|---|---|---|
| A | sensor分離とobject-target birth | 時間予測状態・turn再起動・sensor lesion |
| B | active counterexample partition | MDL・program quotient・能動probe |
| D | replay-response equivalence address | 長期memory・read/write閉路 |
| E | independent constraint channels | Energy固定点・frustration field |
| **C** | **paired worldのobject変更に追従するobject→support因果edge** | 今回の固有対象 |

## 3 seed平均

| 条件 | Factorized 精度/null | Object-edge 精度/null | Shuffled-edge 精度/null |
|---|---:|---:|---:|
| 既知 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 未知語順 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 未知語彙 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| Rename | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 別状態表現 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 入れ子 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 主語省略 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 複数段落 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 計画変更 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 反実仮想 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |

追加診断:

- Factorized proposal: 10.00
- Object edge: 0.00
- Correct paired-probe固有edge: 0
- Shuffled edge: 0.00
- Execution accuracy: 全条件0
- Exact state boundary: 全条件0
- Object-value pair: 全条件0
- Object-edge model: 509 bytes
- 学習時間: 0.533502 sec
- 既知推論: 0.0017 ms/example
- Peak RSS: 110,908 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

Raw factorized proposalは形成されたが、独立paired probeで複数回再現し、成功が失敗を上回るobject→support edgeは全seedで0件だった。Correct paired outcomeとshuffled outcomeはいずれも空edge集合へ収束した。

> **正しいsupport位置の残差をobject境界へ割り当てるだけでは、別episodeへ転送可能なobject identityもtarget-selection edgeも形成されない。**

Object候補はcommandとbeforeに共通する局所substring、support候補は相対位置bucketとして別々に生成されている。そのため残差輸送は、object境界の部分文字列・state内の位置bucket・value区間幅を後付けで接続するだけで、一つの潜在objectからstate supportが共同生成されない。

Object-edge方式は全条件でaccuracy 0、null率1.0だった。Wrong commit 0は安全な因果理解ではなく、edgeが空で何も実行しない結果である。

主語省略、計画変更、反実仮想ではobject permanence、旧goalと最終goalの分離、実行worldと非実行worldの並列保持、event composition、causal directionのすべてが未成立だった。

## 相関暗記と因果理解の反証条件

| 条件 | 結果 |
|---|---|
| Correct paired probeでobject edge形成 | 未達 |
| Shuffleよりedge数・能力が増える | 未達 |
| Object swapでtarget supportだけ移動 | 未達 |
| Exact object/state boundary > 0 | 未達 |
| Edge除去で対応transitionだけ消失 | 未検証（edge 0） |
| Rename・別状態表現へ転移 | 未達 |

## 資源量

- Induction: `O(NL)`
- Paired-probe edge birth: `O(QPOL²)`
- Inference: `O(EPOVL²)`
- Proposal上限: 32
- Edge上限: 64

1GB未満・5ms未満は小規模条件で達成した。弱いスマートフォンCPU実機は未検証。

## 系列C固有の進展

> **Cycle 036で発見したobject→support edge欠如に対し、位置残差輸送を直接試した結果、残差はedgeのbirth原理にならないことを確認した。Objectとsupportを別々に候補化して後から結ぶ研究順序自体を棄却すべきである。**

## 他系列へ返す知見

- A: object sensor失敗残差をedgeへ直接変換しても、共同生成器なしでは再利用edgeにならない。
- B: active counterexampleは既存候補のsplitには使えるが、object-support共同birthを代替しない。
- D: replay-response同値類も、read/write/object境界が別生成ならsemantic addressにならない可能性が高い。
- E: independent constraint channelを増やす前に、各channelが同じlatent object proposalから生成される必要がある。

## 次の仮説

**Object-Centered Support Birth from Paired-World Co-Segmentation**  
（paired world共同分節によるobject中心support創発）

1. Object候補とstate support候補を別々に生成しない
2. Objectだけ異なりvalue操作が同じpaired worldを同時分節
3. 二world間で移動する最小state区間とcommand区間を一つのlatent object proposalとして共同生成
4. Value swapではproposal内部の値だけが変化することを要求
5. Object swapではproposal全体が別supportへ移動することを要求
6. Joint co-segmentation／factorized／shuffled pair／single-worldを比較
7. Exact object boundary・state boundary・wrong targetを独立評価
8. 主語省略では前turn proposalを再起動
9. 計画変更では撤回proposalと最終proposalを分離
10. 反実仮想では実行・非実行worldへ同じobject proposalを写像

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
