# 系列E Cycle 034 研究報告

## 仮説

**Command–State Coupled Energy Fibers from Cross-Value Contrastive Work**  
（値横断contrastive workによるcommand-state結合energy fiber）

Cycle 033では、状態側の候補supportへ複数値を往復介入し、距離分散・round-trip・区間外damageをenergy曲率へ変換した。しかしcorrect probeとshuffleを分離できず、surface置換統計へ退化した。

今回はstate側だけのworkを棄却し、同じ値候補をcommand区間とprospective state区間へ同時に交換したときだけ閉じる局所work loopを形成した。推論時には`before + command`だけを使用し、final testの`after / future`はcandidate生成・energy rankingに使用していない。

## 他系列との重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A | command-state共同創発transition cell | 時間方向の再起動・carry |
| B | command-state swap grammarによるvariable production | MDL・program grammar |
| C | command-coupled intervention fiber | 因果state support・world transition |
| D | tri-view shared-generator memory cycle | 長期memory・read/write閉路 |
| **E** | **command-state同時swapが作る局所work loopとenergy固定点** | 今回の固有対象 |

共同生成器やfiberの存在自体は系列Eの成果とせず、coupling edgeがenergy landscapeと最終固定点をcorrect probe固有に変えるかだけを中心評価とした。

## 実装

- State候補区間とcommand固有区間から最大24候補を生成
- 現在command内に存在する同shape値候補を最大3個保持
- 各値についてcommand区間とstate rollout区間を同時swap
- command-value closure、state-value closure、round-trip、区間外damage、outcome距離を局所work signature化
- 独立probeで2回以上再現し、damage 0・closure成立のedgeだけ保持
- No energy / State-only / Command-state coupled / Shuffled outcomeを比較
- Active集合を各sweepで最小energy+0.055以内へ単調縮小
- 最大7 sweep、実測最大2 sweep

## 3 seed平均

| 条件 | No energy 精度/wrong | State-only 精度/wrong | Coupled 精度/wrong | Coupled active |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 16.67 |
| 未知語 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 14.75 |
| 曖昧性 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 12.12 |
| 入れ子 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 19.92 |
| 主語省略 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 20.00 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 16.92 |
| 計画変更 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 16.29 |
| 反実仮想 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 18.92 |

追加診断:

- Coupled edge: 26.33
- Shuffled edge: 27.67
- Probe audit: 288
- モデルサイズ: 6007 bytes
- 学習時間: 0.283995 sec
- 既知推論: 29.372 ms/example
- 複数段落推論: 55.683 ms/example
- 反実仮想推論: 84.792 ms/example
- Peak RSS: 111824 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Command-state coupling edgeは形成

Correct probeでは平均26.33件のcoupling edgeが形成された。State-only workより厳しい、command値交換とstate rollout交換の閉路条件を通過している。

### Correctとshuffleを分離できない

Shuffled outcomeでも平均27.67件のedgeが形成され、Correct probeよりむしろ多かった。全条件でCoupled方式とShuffle方式のaccuracy・null率・active状態数はほぼ同じである。

> **Commandとstateの値交換が閉じるだけでは意味的constraintにならない。文字shape・相対位置・区間幅が揃えば、誤対応でも局所work loopは形成できる。**

### Energy landscapeは変わるが固定点能力は0

既知条件のactive状態数はNo-energy 20.00からCoupled 16.67へ減少した。曖昧性でもactive集合は変化している。

しかし全条件でexecution accuracy、exact boundary recall、object-value pair recallは0で、全面tie/nullとなった。Coupling edgeはenergy地形を変形したが、semantic attractorを形成していない。

### 計画変更・反実仮想・主語省略

- 主語省略: object permanenceなし
- 計画変更: 撤回edgeと最終edgeの分離なし
- 反実仮想: 実行・非実行固定点の並行保持なし
- 曖昧性: 複数object候補のscope分離なし

### 失敗分類

- Candidate birth: 24候補を維持
- Coupling-edge birth: 成立
- Constraint grounding collapse: correct/shuffle差なし
- Semantic boundary collapse: exact recall 0
- Flat attractor landscape: 全面tie/null
- Wrong attractor: 今回は安全閾値により未確定
- 発散: 未観測

## Hopfield記憶・既存NNとの差

固定patternの想起ではなく、入力ごとに局所command-state swap候補を生成し、複数値のwork loopをenergy項へ変換して反復緩和する点は単純Hopfield記憶と異なる。

一方、現在は手続き的な文字区間置換であり、正式なEquilibrium Propagation、学習された連続energy、意味constraint topologyには未到達である。Equilibrium PropagationやAugmented Lagrangian Predictive Codingは局所的な固定点学習・constraint error伝播を提供するが、状態nodeとconstraint topologyが既に定義されている。今回の失敗点はその前段のnode・binding創発である。

## 資源量・収束保証

- Candidate生成: `O(L^4)`、24候補へ上限制限
- Coupled work: `O(QHVL^2)`
- Relaxation: `O(SH)`
- `H≤24, V≤3, S≤7`
- Active集合は各sweepで単調に部分集合化するため有限停止
- 1GB未満: 達成
- 5ms未満: No-energyのみ概ね達成、Coupledは未達
- 弱いスマートフォンCPU実機: 未検証

## 系列E固有の進展

> **State-only workより強いcommand-state同時swap閉路を形成しても、correct probeとshuffleを区別できない。Energy couplingには値一致だけでなく、object・scope・goalの交換に対する選択的なwork差が必要である。**

## 他系列へ返す知見

- A: command-state共同cellも、値swap閉路だけでは時間identityにならない。object swapとturn再起動の選択性が必要。
- B: swap grammarはcorrect/shuffleでproduction topologyが異なることを必須化すべき。
- C: command-coupled fiberにはvalue交換だけでなくobject交換時のtarget support切替が必要。
- D: shared-generator cycleも三視点のsurface closureではなく、反例交換で対応cycleだけが変化する必要がある。

## 次の仮説

**Object-Selective Work Networks from Double-Contrast Command–State Swaps**  
（値・対象の二重contrast swapによるobject選択的work network）

1. Value swapに加えてobject区間swapを生成
2. Value swapでは同じstate supportの値だけ変化することを要求
3. Object swapではtarget supportだけが別objectへ移ることを要求
4. 二重swapの可換性・非可換性を局所work tensor化
5. Correct double contrast／shuffled object／value-only／state-onlyを比較
6. Object-selective edge除去で対応attractorだけが消えるか監査
7. 曖昧性では複数object networkを並行保持
8. 計画変更では撤回networkへ抑制constraint
9. 反実仮想では実行・非実行networkを別固定点化
10. Exact object/value/support recall、accuracy、wrong attractorを独立評価

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
