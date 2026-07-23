# 系列E Cycle 039

## 仮説

**Constraint-Homotopy Attractor Tracking from Staged Local Consistency Fields**  
（段階的局所整合場による制約ホモトピー・アトラクタ追跡）

Cycle 038の次案だったpaired query world共同分節は、系列B/C/D Cycle 039が同型のpaired/multi-world共同生成を既に検証し、いずれもsemantic structureを形成できなかったため重複として棄却した。

今回は系列E固有の問いとして、すべてのconstraintを一度に加えて平坦化・候補崩壊させるのではなく、低次constraintから高次constraintへenergyを連続変形し、同じ局所盆地を追跡するホモトピー緩和がsemantic attractorを保持できるか検証した。

## 最新系列との重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A Cycle 039 | 遅延言い換え再入場によるprediction-error hysteresis | 時間状態・carry・event boundary |
| B Cycle 039 | Paired disagreement world共同分節grammar | MDL・program production |
| C Cycle 039 | Multi-world intervention closure event | 因果event・world model |
| D Cycle 039 | Paired replay fingerprint reconsolidation | 長期memory・read/write統合 |
| **E Cycle 039** | **制約強度の連続変形と盆地追跡** | 今回の固有対象 |

## 設計

生の日本語から最大16個のprospective state候補を生成し、command-value共変、inverse restoration、non-target保存、future継続、共有anchorの5局所constraintを個別energy fieldとして学習した。

比較は No energy / Joint / Homotopy / Reverse homotopy / Shuffled-outcome homotopy。各stageでactive集合を最小energy + 0.045以内へ単調縮小し、最大3 sweep、全5 stageで最大15 sweepとした。有限候補集合の単調縮小なので有限停止する。

## 3 seed平均

| 条件 | No energy 精度/wrong/active | Joint | Homotopy | Reverse | Shuffle |
|---|---:|---:|---:|---:|---:|
| 既知 | 0/0/7.75 | 0/0/7.75 | 0/0/7.75 | 0/0/7.75 | 0/0/7.75 |
| 未知語 | 0/0/7.42 | 0/0/7.42 | 0/0/7.42 | 0/0/7.42 | 0/0/7.42 |
| 曖昧性 | 0/0/10.29 | 0/0/10.29 | 0/0/10.29 | 0/0/10.29 | 0/0/10.29 |
| 入れ子 | 0/0/8.43 | 0/0/8.43 | 0/0/8.43 | 0/0/8.43 | 0/0/8.43 |
| 主語省略 | 0/0/12.00 | 0/0/12.00 | 0/0/12.00 | 0/0/12.00 | 0/0/12.00 |
| 複数段落 | 0/0/7.57 | 0/0/7.57 | 0/0/7.57 | 0/0/7.57 | 0/0/7.57 |
| 計画変更 | 0/0/11.64 | 0/0/11.64 | 0/0/11.64 | 0/0/11.64 | 0/0/11.64 |
| 反実仮想 | 0/0/12.00 | 0/0/12.00 | 0/0/12.00 | 0/0/12.00 | 0/0/12.00 |

追加診断:
- 候補上限 16
- Homotopy平均反復 6、Joint 2
- Exact boundary recall / object-value pair recall: 全条件0
- Null率: 全方式・全条件1.0
- 収束率 1.0
- Homotopy model 6,930 bytes
- 学習 0.073152 sec
- Peak RSS 111,836 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

No energy、Joint、Homotopy、Reverse、Shuffled-outcomeのactive状態数・accuracy・null率が全条件で同一だった。段階投入は反復回数を2から6へ増やしただけで、候補集合や固定点を変えなかった。

> 局所constraintが候補間で同じ値を取る、または同じsurface特徴へ従属する場合、energyを連続変形しても追跡すべきsemantic basinは存在しない。

Shuffled-outcome homotopyもCorrect homotopyと完全同一で、constraint weightは対象・値・関係・操作ではなく、相対位置・文字shape・区間幅・文字列保存へ接地していた。

反証分類:
- Candidate birth: 16候補
- Constraint field birth: 5 channel
- Basin differentiation: 0
- Homotopy path dependence: 0
- Semantic boundary: 0
- Flat attractor: 全面tie/null
- Wrong attractor: 安全閾値により未確定
- 発散: 未観測

主語省略、長距離依存、計画変更、反実仮想の複数固定点も未成立。

## 既存方式との差

固定patternを保存・想起するのではなく、入力ごとにprospective stateを生成し、複数の局所constraint fieldを段階的に強めながら固定点を追跡した点は単純Hopfield memoryとは異なる。ただし現状は離散文字区間候補と手続き的energyであり、正式な平衡伝播、学習されたsemantic node、世界状態、goal constraintには未到達。

## 資源量

- モデル: 6,930 bytes
- Peak RSS: 111,836 KiB
- 学習: 0.073152 sec
- 推論: 既知 8.593ms / 複数段落 12.005ms / 反実仮想 19.107ms
- 計算量: Candidate O(L^4)（16候補上限）、Constraint O(KH)、Homotopy O(KSH)、K≤5,S≤3,H≤16

1GB未満は達成。5ms未満と弱いスマートフォンCPU実機検証は未達。

## 系列E固有の進展

> 制約を一度に掛けることが失敗原因ではなかった。段階的ホモトピーでもCorrect/Shuffle/Reverseが同一であり、問題は緩和経路ではなくconstraint fieldがsemantic nodeへ接地していないことにある。

## 他系列へ返す知見

- A: state cell未形成なら時間hysteresisや寿命追跡だけでは改善しない。
- B: grammar候補がsurface同値ならMDL順序を変えてもsemantic productionにならない。
- C: multi-world closure候補がなければ制約段階化でも因果eventは生まれない。
- D: trace統合順序より先にread/write双方を分けるsemantic witnessが必要。

## 次の仮説

**Constraint-Field Birth from Counterexample-Separating Residual Eigenmodes**  
（反例分離残差固有モードによるconstraint field創発）

候補×paired counterexampleの残差行列からsurface長・位置・shapeの低rank成分を除き、疎固有モードをconstraint field候補化する。Correct pairのみで安定するmode、mode lesionで対応固定点だけが崩れることを必須化する。

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
