# 系列E Cycle 022 研究報告

## 仮説

**Constraint-Wise Bifurcation Intersection for Open-Set Factor Birth**  
（制約別分岐交差によるopen-set factor birth）

Cycle 021ではafter再構成・future整合・non-target保存・execution可否を単一energyへ合算し、null basinからcandidate basinへ切り替わる位置をfactor候補化した。しかしvalue recallが消失した。

今回は4制約を独立landscapeとして保持し、nudge homotopy中のargmin切替区間を制約ごとに抽出した。2つ以上の独立制約で同じ最小区間が分岐した場合だけ、object/value factorとしてbirthさせた。

## 先行研究整理

- Equilibrium Propagationはfree phaseとnudged phaseの同一力学から局所creditを得るが、状態変数と結合候補は事前定義される。
- 2025年のDirected Equilibrium Propagation再検討ではleakを含む収束条件と局所学習則が整理されたが、生文字列から未知nodeを生成する問題は対象外。
- 2025〜2026年のLagrangian／dissipative dynamicsへのEP拡張も、軌道上の局所応答を扱う一方、意味factor候補は既知である。
- 2026年のIsing dynamics型EPは局所最小とphase-space contractionを緩和するが、候補表現のopen-set birthを解かない。

参照:
- https://doi.org/10.3389/fncom.2017.00024
- https://doi.org/10.3390/math13111866
- https://doi.org/10.1103/smt9-1t1l
- https://doi.org/10.1002/aisy.202501310
- https://arxiv.org/abs/2606.09112

## 他系列との重複表

| 系列 | 最新中心 | 限定成功 | 主失敗 | Eとの分離 |
|---|---|---|---|---|
| A | 残差逆投影・談話carryによるtest-cell共同創発 | 自己生成testで候補内識別 | open-set birth増分0 | query・予測testは扱わない |
| B | edit graph反単一化によるcorrespondence program | filler再利用 | context transport 0 | 文法・MDLは扱わない |
| C | 対称情報付きevent direction | 表面局所event再実行 | 因果方向は情報非対称性 | world model・因果graphは扱わない |
| D | write-only value classとread address分離 | endpoint分離で誤読低下 | slow class誤統合 | 長期memoryは扱わない |
| **E** | **独立energy landscapeの分岐交差** | 今回検証 | factor birth方向 | energy・attractor軸固有 |

## 実験条件

- seed: 1 / 7 / 19
- 学習例: 48
- test: 12例 / split / seed
- 独立制約: after / future / non-target / execution
- nudge: 0, 0.1, 0.2, 0.35, 0.5, 0.7, 1.0
- 最大candidate: 48
- 最大relaxation sweep: 4
- 比較:
  1. Base
  2. Single-constraint bifurcation
  3. Constraint intersection
  4. Constraint intersection + Null
- hidden object/valueは評価器のみで使用

## 3 seed平均

| 条件 | Base精度 | Single精度 | Intersection精度 | Intersection+Null率 | Intersection value recall |
|---|---:|---:|---:|---:|---:|
| 既知 | 0.3056 | 0.0000 | 0.0000 | 1.0000 | 0.3056 |
| 未学習言い換え | 0.1944 | 0.0000 | 0.0000 | 0.4722 | 0.1944 |
| 入れ子 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 | 0.8889 | 0.3056 |
| 複数段落 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 計画変更 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 反実仮想 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

## 判定

**中核仮説は強く反証された。**

### 制約交差で正しいpairが一件も増えない

全splitでIntersection accuracyは0だった。既知条件ではBaseがpair/value recall 0.3056を持つ一方、Intersectionはobject recall 0、pair recall 0へ悪化した。

制約別に分岐を測っても、同じ区間への投票は意味roleの一致ではなく、複数のsurface heuristicが同じ包含spanへ収束しただけだった。

### Value候補の限定信号をbindingできない

既知・未学習言い換え・主語省略ではIntersection value recallが0.1944〜0.3056残った。しかしobject recallが0〜0.25で、pair recallは全条件0だった。

> **複数制約が同じvalue区間を支持しても、対応するobject・scope・operationとのbindingは生まれない。**

### 交差は候補生成ではなく過剰棄却

Single方式よりIntersection方式はbirth数を減らした。

- 未学習言い換え: 1.4167 → 0.5556
- 主語省略: 0.7778 → 0.3056
- 入れ子・複数段落・計画変更: 0

探索量は減ったが正答pair recallも0のため、意味的なfactor selectionではなく候補消失である。

### Nullなしでも多くの条件で全面棄権

Intersectionは候補集合自体が空になるため、既知・入れ子・複数段落・計画変更・反実仮想でnull率1.0だった。Null gateの追加による能力差はない。

未学習言い換えと主語省略ではjunk候補を誤確定したため、Null校正も不十分だった。

### 独立energyと独立因果証拠は別

after・future・non-target・executionを別々に計算しても、それらは同じ文字列包含関係に依存する。独立な数値項であることは、独立した意味・因果証拠であることを意味しない。

## 単なるHopfield記憶・既存NNとの差

固定patternの想起ではなく、null/candidate basin、nudge homotopy、制約別分岐、疎candidate birth、反復緩和を用いる点は異なる。

ただし現実装は有限文字列候補へ手続き的energyを与える最小反証器であり、学習された連続energy network、正式なfree/nudged相関差、意味node間の平衡伝播には到達していない。

## 収束・失敗分類

- **候補崩壊**: object/pairが候補集合外
- **分岐交差崩壊**: 複数制約の同一区間投票が意味roleを表さない
- **過剰棄却**: Singleより候補数を減らすがrecallを増やさない
- **局所最適**: 未学習言い換え・主語省略でjunkへ収束
- **Null安全停止**: 多くの条件で全面棄権
- **発散**: 最大4 sweepにより未観測

停止条件はactive集合不変、energy幅0.05以内への収縮、または4 sweep上限。

## 資源量

- Intersection model: 231 bytes
- Prototype: 2.67
- Training: 0.116872 sec
- Inference:
  - 既知: 1.311 ms/example
  - 複数段落: 4.250 ms/example
- Peak RSS: 110884 KiB（Python runtime込み）
- 推定計算量:
  - candidate proposal `O(L²)`
  - 制約別homotopy `O(CJH)`
  - 分岐交差 `O(CH)`
  - relaxation `O(SH)`
  - `C=4, J=7, H≤48, S≤4`

1GB未満・5ms未満は小規模制御条件で達成した。弱いスマートフォン実機では未検証。

## 系列E固有の進展

Energy-based factor形成段階を更新する。

1. Global frustration
2. Responsibility localization
3. Factor-separated residual
4. Basin curvature
5. Null-candidate bifurcation
6. **Constraint-wise bifurcation intersection――今回反証**
7. Cross-environment intervention invariance
8. Learned local factor graph
9. Equilibrium propagation
10. Goal・constraint planning

核心的知見:

> **複数energy制約が同じ文字区間で分岐しても、意味factorの証拠にはならない。制約が同一surface特徴へ依存している限り、交差は独立証拠ではなく相関した誤差の多数決になる。**

## 他系列へ返す知見

- A: 複数future horizonが同じcellを支持しても、同じsurface feature由来なら独立証拠ではない。
- B: 複数derivation viewの一致は、生成過程を変えた反例で独立性を監査する必要がある。
- C: 複数effect footprintの一致だけでstate variable identityを統合しない。
- D: write/read双方の支持も、同じ文字context依存ならslow consolidationの十分条件にならない。

## 次の仮説

**Environment-Decoupled Factor Birth from Intervention-Invariant Energy Responses**  
（環境分離介入に不変なenergy応答からのfactor birth）

次は同一episode内の複数energy項の一致を使わない。

1. object名、value表現、語順、state表現を独立に変えた環境を生成
2. 各候補factorへ同じ局所介入を加える
3. surfaceが変わってもafter改善・future改善・non-target保存の応答vectorが一致する場合だけfactor候補化
4. 同一surface内の複数制約一致はcreditに数えない
5. response vectorが環境ごとに崩れる候補は即時削除
6. factor birth後だけattractor relaxationとfree/nudged局所更新を行う
7. value recall、pair recall、環境横断accuracyを主評価化

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
