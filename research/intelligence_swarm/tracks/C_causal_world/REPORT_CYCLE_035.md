# 系列C Cycle 035 研究報告

## 仮説

**Asymmetric Causal Direction from Command–State Intervention Commutators**  
（command–state介入交換子の非対称性による因果方向創発）

Cycle 034では、同じ状態supportへ複数値を可逆介入できるfiberを形成できたが、commandの対象・値・scopeを束縛できず、execution accuracyとexact boundary recallは0だった。

当初の次案だったcommand-state contrastive swapは、系列A Cycle 035、系列B Cycle 035、系列D Cycle 034、系列E Cycle 034が共同生成・swap・couplingを既に検証しており、中心機構が重複するため棄却した。本Cycleでは系列C固有の問いとして、**介入順序の交換子が因果方向を識別するか**を検証した。

- command内value介入後にstate rolloutを実行する経路
- state supportへの直接介入後にcommand整合性を確認する経路
- 両経路が同じprospective stateへ到達する可換性
- forward成功、inverse restoration、非対象保存
- independent probeでの再現

Final testのafter/futureは候補生成・rankingに使用していない。

## 最新系列との重複表

| 系列 | 最新中心 | Cで扱わない領域 |
|---|---|---|
| A | command-state共同cellとturn横断swap | 時間予測状態・再起動 |
| B | joint-born variable productionとswap grammar | MDL・匿名記号・圧縮 |
| D | tri-view shared-generator memory cycle | 長期memory・read/write閉路 |
| E | command-state coupled energy fiber | energy固定点・work曲率 |
| **C** | **介入順序交換子の非対称性と因果方向** | 今回の固有対象 |

## 3 seed平均

| 条件 | Forward 精度/wrong | Commutator 精度/wrong | Exact境界 | 候補数 |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 250.68 |
| 未知語順 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 231.58 |
| 未知語彙 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 238.32 |
| Rename | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 280.82 |
| 別状態表現A | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 77.24 |
| 別状態表現B | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 225.07 |
| 入れ子 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 176.94 |
| 主語省略 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 250.65 |
| 複数段落 | 0.0000 / 0.0278 | 0.0000 / 0.0278 | 0.0000 | 63.01 |
| 計画変更 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 220.04 |
| 反実仮想 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 159.33 |

追加診断:

- Raw proposal: 27.33
- Forward diagram: 25.33
- Commutator diagram: 15.67
- Independent probe audit: 4864.67
- Shuffled outcome diagram: 0.00
- モデルサイズ: 1816 bytes
- 学習時間: 1.125101 sec
- 既知推論: 1.653 ms/example
- 複数段落推論: 0.622 ms/example
- Peak RSS: 111056 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Correct probe固有の交換子diagramは形成

Forward条件では平均25.33 diagram、forward・inverse・交換子可換性を要求した条件では15.67 diagramが残った。Probe outcomeをshuffleするとdiagramは0になった。

したがって、正しい独立観測に依存する局所介入構造は形成できた。

### 因果能力増分は0

しかし全主要条件でexecution accuracyは0、exact target boundaryとobject-value bindingも0だった。Commutator条件はForward条件よりdiagram数を削減したが、正しいtransitionを一件も選べなかった。

> **介入順序が可換であることは、候補operatorの整合性監査には使えるが、対象・状態変数・操作target・因果方向を生成する十分条件ではない。**

### 候補数が多いままtie

既知条件では平均250.68候補、Renameでは280.82候補が残り、複数のprospective stateが同点になって全面棄権した。交換子条件は候補空間をわずかに削るだけで、semantic bindingを作らない。

### Shuffled outcomeとの差

Shuffleではdiagramが0になったため、Correct probe固有の構造差はある。しかしCorrect probeでもaccuracy 0なので、相関暗記を超えた因果理解の証拠にはならない。

### 計画変更・反実仮想・主語省略

- 主語省略: object permanence 0
- 計画変更: 撤回案と最終goalの分離 0
- 反実仮想: 実行worldと非実行worldの並列rollout 0
- 複数段落: accuracy 0、wrong commit 0.0278

## 相関暗記と因果理解の反証条件

| 条件 | 結果 |
|---|---|
| Correct probeでのみdiagram形成 | 達成 |
| Forwardより候補を削減 | 達成 |
| Exact state-variable境界 > 0 | 未達 |
| Execution accuracy > 0 | 未達 |
| Object/value swapでtargetだけ共変 | 未達 |
| 計画変更・反実仮想のworld分離 | 未達 |
| Diagram removalで対応transitionだけ消失 | 未検証 |

形成されたdiagramは因果mechanismではなく、同一surface template上の局所置換可換classである。

## 資源量・計算量

- Proposal induction `O(NL)`
- Probe commutator audit `O(QFVO L)`
- Inference `O(FVL)`
- Diagram上限 32
- Value候補上限 8
- Object候補上限 6

1GB未満は達成した。推論は小規模条件でも候補数が多く、弱いスマートフォンCPU実機は未検証である。

## 系列C固有の進展

> **独立probe由来の介入交換子は、surface-local operatorを厳格に削減できる。しかし可換性だけでは因果方向を識別せず、command・object・state supportを共同生成する機構にもならない。**

## 他系列へ返す知見

- A: cross-turn再起動の前に、swap可換性だけではtransition identityを作れない。
- B: 可換diagramを匿名記号化しても、execution 0ならMDL採用すべきでない。
- D: read/write cycleの閉路性だけでなく、object介入による選択的support切替が必要。
- E: energyへ可換work項を加えても、Correct/shuffle能力差がなければsurface統計である。

## 次の仮説

**Object-Selective Causal Fibers from Double Intervention Commutator Asymmetry**  
（value・object二重介入交換子の非対称性による対象選択因果fiber）

1. 同じstate supportへvalue swapを実施
2. command object区間を別対象へswap
3. Value swapでは同一supportの値だけが変化することを要求
4. Object swapではtarget supportだけが別対象へ移ることを要求
5. 二つの介入順序を入れ替え、正しい因果構造では可換・誤bindingでは非可換になるか監査
6. Correct object/value swap、shuffled swap、value-only、object-onlyを比較
7. Exact object boundary、state boundary、execution、wrong targetを独立評価
8. 計画変更では撤回edgeと最終edgeを別fiber化
9. 反実仮想では実行・非実行worldへ同じ二重介入を適用

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
