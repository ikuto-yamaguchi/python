# 系列E Cycle 011 研究報告

## 仮説

**Adaptive Factor Acquisition by Residual Equivalence Splitting**  
（残差同値類分割による適応factor獲得）

Cycle 010ではwhole-outcome factorだけで引用付き制御候補を完全分離でき、全edge Jacobianは精度を増やさず計算量だけを増やした。本Cycleでは、現在のfactorで同率になる候補classだけへ追加介入を発行し、classを最も分割するfactorのみを獲得する。

## 他系列との重複表

| 系列 | 最新中心 | 成功・失敗 | 未解決点 | E候補との判定 |
|---|---|---|---|---|
| A | scope候補の能動実行・修復 | 正しい候補があればgeneric feedbackで修復、無標識候補recall 0 | open-set proposal | 外部観測取得は重複のため棄却 |
| B | 反例誘導role境界 | recall 0.9037だがprecision 0.26、能力0 | relation boundary | program生成は重複のため棄却 |
| C | context/state probeによるmechanism分離 | raw fingerprintへ過分裂し悪化 | relation-level state variable | 因果edge生成は重複のため棄却 |
| D | boundary surprise＋replay | 一部干渉更新改善、event F1崩壊 | retrieval Jacobian boundary credit | 長期memory形成は重複のため棄却 |
| E | residual classにのみ追加factor取得 | 今回検証 | factor minimalityとopen-form proposal | 系列固有 |

## 実装

比較は `whole`、6 factorを固定取得する `full`、残差classを最大分割するfactorだけを最大4 sweepで追加する `adaptive`。停止条件は残差1、分割利得0、または4 sweep。

## 540例・3 seed平均

| 条件 | Whole精度 | Full精度 | Adaptive精度 | Full factor数 | Adaptive factor数 |
|---|---:|---:|---:|---:|---:|
| 既知 | 0.0000 | 1.0000 | **1.0000** | 6.00 | **2.13** |
| 曖昧性 | 0.0000 | 1.0000 | **1.0000** | 6.00 | **2.15** |
| 入れ子proxy | 0.0000 | 1.0000 | **1.0000** | 6.00 | **2.18** |
| 反実仮想proxy | 0.0000 | 1.0000 | **1.0000** | 6.00 | **2.16** |
| 訂正proxy | 0.0000 | 1.0000 | **1.0000** | 6.00 | **2.14** |
| 無標識日本語 | 0.0000 | 0.0000 | 0.0000 | 6.00 | 1.28 |

- Full factor evaluation: 218.0/query
- Adaptive factor evaluation: **102.9/query**
- Adaptive平均sweep: 2.13
- Active candidates: 31.1
- Adaptive実測: 0.0475 ms/query
- model: 135 bytes
- Peak RSS: 296664 KiB（Python runtime込み）

## 判定

**factor acquisitionの計算選択部品は限定支持。ただし中核仮説は反証。**

残差classにだけ追加介入することで、full方式の約47%のfactor評価で同じ制御精度を得た。一方、factor空間は実験側供給で、無標識日本語candidate recallは0。正答候補がない条件でも0.7617が一意収束し、内部収束は現実の正しさを保証しなかった。自然な入れ子・反実仮想・訂正理解、平衡伝播による局所weight学習も未成立。

## 系列E固有の進展

必要条件を、candidate recall、outcome non-isomorphism、local factor separability、factor minimality、**reality calibration of residual convergence**、attractor/local learningへ更新した。本Cycleではfactor minimalityを制御条件で支持したが、候補外検知で失敗した。

## 他系列へ返す知見

- A: 最大情報利得probeでも正答仮説が集合外なら誤確信へ収束する。
- B: cross-episode反例は残差classを実際に分割する場合だけ取得する。
- C: relation probeは既存mechanism classへ増分情報を与えるものだけ保持する。
- D: retrieval Jacobianは分割利得と候補外検知を別々に測る。

## 次の仮説

**Open-Set Residual Energy with Null-Hypothesis Attractors**

候補集合へ必ずnull stateを含め、どの既存候補も観測を説明できないresidual energyを測る。制御精度1.0を維持しつつ、無標識条件の誤った一意収束0.7617を大幅削減する。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
