# 系列E Cycle 025 研究報告

## 仮説

**Constraint-Edge Birth from Cross-Candidate Energy Credit before Commutator Tests**  
（交換子検定前の候補間energy creditによるconstraint edge創発）

Cycle 024ではobject/value候補への介入A→BとB→Aがほぼ全面可換で、非ゼロ交換子prototypeは0件だった。原因仮説は、一方の候補操作が他方の内部状態へ伝播するconstraint edgeが存在しないことである。

今回は交換子を先に測らず、object候補を固定した際のvalue候補順位、およびvalue候補を固定した際のobject候補順位の変化を測った。複数surface環境で再発し、局所pair energyが代替候補より低く、non-target damageが少ないsignatureだけを疎なconstraint edgeへ昇格した。

## 先行研究整理

- TANGOは学習されたLyapunov energyの降下流とenergy-preservingな接線流を分離し、安定性と情報伝播を両立する。今回の方式は学習済みnode表現を前提とせず、生の日本語span候補間でedge birthを試みる点が異なる。
  - https://openreview.net/forum?id=c3aN3wecSt
- SPHINXはtask signalから潜在hypergraphを推論するが、end-to-end differentiable encoderと教師task signalを前提とする。
  - https://proceedings.mlr.press/v267/duta25a.html
- Generalized Equilibrium Propagationはgraph上の局所parameter更新を扱うが、network topologyとstate variablesは定義済みである。
  - https://arxiv.org/abs/2602.03546
- Equilibrium Propagation Without Limitsは有限nudgeでも局所energy差からexact gradientを得る理論を示すが、候補nodeとlocal energy termは既知である。
  - https://arxiv.org/abs/2511.22024

今回の検証対象は、そのさらに上流にある「生の自由日本語からconstraint edge自体を生成できるか」である。

## 最新系列との重複表

| 系列 | 最新中心 | 限定信号 | 支配的失敗 | Eとの分離 |
|---|---|---|---|---|
| A | commitment除去による予測責任 | 主語省略でcarry候補recall | 二値gateが全面終了へ退化 | 談話予測責任は扱わない |
| B | role交換consequenceから実行binding graph | MDL短縮 | 実行accuracy 0 | state-change実行graphは扱わない |
| C | 多witness正介入整列によるstate-variable fiber | null collapse除去 | identity class 0 | 因果transition witnessは扱わない |
| D | memory element除去による反実仮想credit | slow factor形成 | slow固定で能力悪化 | 長期memory再固定化は扱わない |
| **E** | **推論候補間のenergy順位変化からconstraint edge birth** | 今回検証 | edge生成・factor binding | 系列固有 |

棄却した候補:
- Bと同型の三部実行binding graph
- Cと同型のpositive transition witness alignment
- Dと同型のmemory element removal credit
- Aと同型の談話commitment responsibility

## 実験条件

- Seed: 1 / 7 / 19
- 学習bundle: 24 × 4 surface環境
- 候補上限: object 4 × value 4、pair最大16
- Edge採用条件:
  - 3環境以上
  - 4回以上support
  - cross-candidate平均credit > 0.03
  - non-target / execution damage率 < 0.2
- 最大反復: 6 sweep
- 停止:
  - active集合不変
  - 最小energy + 0.04以内へ収縮
  - 最大反復到達
- Ablation:
  1. Base energy
  2. Constraint-edge energy
  3. Constraint-edge + Null
- 統合test:
  - 既知
  - 未知語
  - 曖昧性
  - 入れ子
  - 主語省略
  - 複数段落
  - 計画変更
  - 反実仮想

Hidden object/value labelは評価器だけで使用した。

## 3 seed平均

| 条件 | Base精度 | Edge精度 | Edge+Null率 | Edge pair recall |
|---|---:|---:|---:|---:|
| 既知 | 0.5833 | 0.5833 | 1.0000 | 0.5833 |
| 未知語 | 0.2222 | 0.2222 | 1.0000 | 0.2222 |
| 曖昧性 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 入れ子 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 主語省略 | 0.0278 | 0.0278 | 1.0000 | 0.0278 |
| 複数段落 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 計画変更 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 反実仮想 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

追加診断:

- Constraint edge: **0.00**
- 平均edge weight: 0.0000
- 既知平均候補: 10.06
- 既知平均active: 1.08
- 平均反復: 2.00
- 収束率: 1.0（最大反復停止を含む）

## 判定

**中核仮説は強く反証された。**

### Constraint edgeは0件

採用条件を通過したedgeは全seedで0件だった。

一候補を固定した際に他候補の順位は変化するが、その変化は複数surface環境で再現せず、またはdamageを伴った。Cycle 024の交換子0の原因を「edge不在」と特定したが、今回のcross-candidate creditでもedgeを生成できなかった。

### 能力増分は全条件0

BaseとEdge方式はaccuracy、wrong commit、object/value/pair recall、active状態数、反復回数が全条件で同一だった。

Edge mechanismはenergy landscapeを一件も変更していない。

### 順位変化はconstraint evidenceではない

固定した候補を含む部分集合だけで再rankingすると、他候補の順位は手続き的に変わる。しかし、その変化が対象・関係・scopeのconstraintを表すわけではない。

> **候補集合の条件付きranking変化は、共有された潜在状態を介した相互作用がなければconstraint edgeの証拠にならない。**

### 難条件のcandidate collapseは継続

- 曖昧性: value / pair recall 0
- 計画変更: value / pair recall 0
- 反実仮想: value / pair recall 0
- 入れ子: pair recall 0
- 複数段落: pair recall 0
- 主語省略: value recall 1.0、object/pair recall 0.0278

候補間edge以前に、object・value・scope候補の生成が不足している。

### Nullは全面棄権

Edge+Null方式は全条件でwrong commit 0、null率1.0、accuracy 0だった。安全停止としてのみ機能する。

## 単なるHopfield記憶・既存NNとの差

固定patternの保存と最近傍想起ではなく、入力ごとにobject/value候補を同時保持し、pair energy、候補固定による順位変化、疎edge、反復緩和を用いる点はHopfield記憶と異なる。

一方、現在の実装は手続き的な文字列energyであり、学習された連続energy network、正式な平衡伝播、意味node間の局所力学には到達していない。既存NNの小型版でもなく、まだ検証用の離散energy prototypeである。

## 収束と失敗分類

- **候補崩壊**: 正答object/value/scopeが候補集合外
- **Edge birth崩壊**: cross-environmentで安定した正credit edgeが0
- **相互作用崩壊**: ranking変化が共有潜在状態を介さない
- **局所最適**: Nullなしではjunk pairへ安定収束
- **Null安全停止**: 全面棄権
- **発散**: active集合単調縮小と最大6 sweepにより未観測

active集合は各sweepで部分集合にしかならないため、有限候補上では最大6回以内に停止する。

## 資源量

- Edge model: **133 bytes**
- 学習時間: **0.501130 sec**
- 既知推論: **5.833 ms/example**
- Peak RSS: **40828 KiB**（Python runtime込み）
- 最大候補: 16
- 平均active: 1.08
- 平均反復: 2.00
- 推定計算量:
  - 候補生成 `O(L²)`
  - Edge credit学習 `O(NEH²)`
  - 緩和 `O(SH)`
  - `E=4、H≤16、S≤6`

1GB未満は達成した。推論は既知・未知語・主語省略・反実仮想で5msを超え、弱いスマートフォンCPU目標は未達。実機未検証。

## 系列E固有の進展

> **交換子の前にconstraint edgeが必要という順序は妥当だが、候補固定による条件付き順位変化だけではedgeは生まれない。Edgeには複数候補が共同で説明する第三の残差状態が必要である。**

## 他系列へ返す知見

- A: commitment除去後の予測誤差増加も、第三の未説明観測状態へ局所化しなければ責任edgeにならない。
- B: object/value交換後のafter変化だけでなく、両者が共同説明するstate-change residual nodeが必要。
- C: witness間の必要edgeは、二者類似ではなく共同で説明されるresidual stateへ接続すべき。
- D: memory element除去creditは、query loss全体ではなく局所未説明residualへ帰属させる必要がある。

## 次の仮説

**Residual-Mediator Constraint Hyperedges from Triadic Energy Synergy**  
（三者energy相乗効果からの残差媒介constraint hyperedge）

次はobject-value pairを直接edge化しない。

1. After・future・non-targetの未説明残差区間を第三nodeとして生成
2. Object単独、value単独、residual単独のenergy reductionを計測
3. Object+value+residualの共同低下が単独効果の和を超える場合だけhyperedge候補化
4. 3環境以上で同じ局所相乗signatureが再現する場合だけweight化
5. Object/valueを交換した際、対応residual nodeだけが移るか反証
6. Free/nudged固定点差からhyperedge-local creditを更新
7. 曖昧性・計画変更・反実仮想のvalue/pair/scope recallを主評価化
8. Hyperedgeなし、pair-edge、triadic-hyperedgeを独立ablation

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
