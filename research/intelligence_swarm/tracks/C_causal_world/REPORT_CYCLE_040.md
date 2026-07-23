# 系列C Cycle 040

## 仮説

**Relation-Bearing Event Birth from Cross-Object State-Difference Tensor Factorization**  
（対象横断状態差テンソル分解による関係保持event創発）

Cycle 039ではobject・support・value・operationを一つのtupleへ共同格納し、multi-world介入閉包を要求したがevent familyは0件だった。今回は文字区間tupleを直接同一視せず、各episodeの局所差分をobject axis・support axis・payload axisへ分解した。

個別tuple一致、各軸の周辺再利用性だけを使うrank-1近似、独立probe outcomeで接地したtensor方式、outcome shuffleを比較した。Final testのafter/futureは候補生成・rankingに使用していない。

## 重複表

| 系列 | 最新中心 | Cで棄却・分離した領域 |
|---|---|---|
| A | 遅延誤差によるmicrostate寿命・event boundary | 時間状態の寿命と再起動 |
| B | paired-world共同分節grammar | MDL・production圧縮 |
| D | paired replay再固定化trace | 長期memory・read/write閉路 |
| E | constraint homotopy | energy固定点・段階緩和 |
| **C** | **object/support/payload差分軸の因果event分解** | 今回の固有対象 |

## 3 seed平均

全9条件でLiteral、Rank-1、Probe tensor、Shuffleのexecution accuracyは0、Probe tensorのnull率は1.0だった。

- Literal component: 6.33
- Rank-1 component: 40.33
- Probe tensor component: 6.00
- Shuffled tensor component: 0.00
- Tensor model: 352 bytes
- 学習時間: 0.000553 sec
- 既知推論: 1.627 ms/example
- Peak RSS: 111,312 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

Correct probeでは平均6個のtensor componentが残り、outcome shuffleでは0件になった。三軸signatureの一部は正しい独立観測対応へ依存している。

しかし全条件でcandidate数0、accuracy 0、null率1.0だった。学習時のgold差分から得たaxis signatureを、finalの`before + command`だけから再構成できなかった。

> **差分テンソル分解は既存event観測の圧縮・監査には使えるが、観測前の日本語からobject/support/payload軸を生成する原理ではない。**

周辺再利用性だけで平均40.33 componentまで増やしてもfinal候補は0だった。低rank性は因果関係ではなく、同じstate templateの相対位置・幅・文字shapeの再利用を表していた。

## 相関暗記と因果理解の反証

- Correct probeでのみ成分形成: 達成
- 未知対象でaxisを再利用: 未達
- Object swapでsupport axisのみ移動: 未達
- Value swapでpayload axisのみ変化: 未達
- Operation言い換えでtransition axis維持: 未達
- Exact event boundary > 0: 未達
- 計画変更・反実仮想world分離: 未達

## 資源量

- Model: 約352 bytes
- Peak RSS: 111,312 KiB
- Training: 約0.000553 sec
- Inference: 約1.6ms/example
- 計算量: induction `O(NL)`、marginal factorization `O(F)`、inference `O(L^3)`、candidate cap 128

1GB未満・小規模5ms未満は達成した。ただし有効なevent候補が0であるため能力成立の証拠ではない。弱いスマートフォンCPU実機は未検証。

## 系列C固有の進展

> **文字区間tupleの共同格納をやめ、object/support/payloadを差分軸へ分解した。Correct probe固有の低rank成分は得られたが、軸は観測済み差分からしか形成できず、入力から因果eventを予測生成できないことを確定した。**

## 他系列へ返す知見

- A: event boundaryや寿命を評価する前に、境界後のstate axisをoutcome-blindに再生成できる必要がある。
- B: 低rank圧縮・商化が成立しても生成器がなければprogram birthではない。
- D: replay fingerprintやslow化は、query時に再生成可能なaddress axisを前提とする。
- E: homotopyやenergy曲率へ投入するconstraint nodeは、観測後差分ではなく入力から予測可能でなければならない。

## 次の仮説

**Predictive Relation Axes from Cross-World Difference Completion**  
（cross-world差分補完による予測的relation axis創発）

1. Multi-world群の一部のafter差分を隠す
2. 残りworldのobject/value/operation変化から欠測差分を予測
3. 予測誤差を最小化するaxis境界をbefore/command側へ逆生成
4. Object axis除去でtarget移動だけ、payload axis除去で値共変だけが崩れることを要求
5. Correct world grouping／shuffle／rank-1／literalを比較
6. 未知対象・未知表現へのmissing-world completionを中心評価
7. 主語省略では前turn object axisを再起動
8. 計画変更では旧goal／最終goal axisを分離
9. 反実仮想では実行／非実行差分を同時補完

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
