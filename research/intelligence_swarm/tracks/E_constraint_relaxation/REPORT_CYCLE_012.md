# 系列E Cycle 012 研究報告

## 仮説

**Open-Set Residual Energy with Null-Hypothesis Attractors**（帰無仮説アトラクタを持つ開集合残差energy）

Cycle 011では残差候補classのみへfactorを取得して制御精度を維持した一方、正答候補が集合外でも76.17%が一意候補へ誤収束した。本Cycleでは候補集合へ「既存候補のどれでもない」null attractorを追加し、候補間の相対energyではなく、観測と最良候補の絶対残差から候補外を検出できるか検証した。

## 他系列との重複表

| 系列 | 最新中心 | 成功・失敗 | Eとの差 |
|---|---|---|---|
| A | 共有active probeによる予測class分割 | probe数半減、言い換え・入れ子recall 0 | 外部観測policyは棄却 |
| B | multi-field relation保存program | observational preservationの増分情報0 | program/MDL生成は棄却 |
| C | changed/preserved contrastによる状態変数 | 全文prototypeより改善、relationは表面chunk | world-state変数生成は棄却 |
| D | signed retrieval-interference boundary credit | event F1改善、長gap過分割 | 長期memory境界は棄却 |
| E | null attractorによる候補外検出 | 本Cycle | 系列固有 |

継承知見：A/Eから正答候補が集合外なら情報利得や収束は誤確信を生む、B/Cから観測済み整合の再確認は増分情報を持たない、Dから単目的最適化は干渉副作用を生む、を採用した。

## 実装と停止条件

12個の候補を8次元の疎なoutcome stateとして同時保持し、closed adaptive、fixed null、adaptive nullを比較した。最大4 sweep、残差classを分割するfactor利得が1以下、または一意候補で停止する。発散、平坦化、候補崩壊、誤候補への局所最適を別指標で扱う。

## 実験

- seed: 1 / 7 / 19
- 例数: 120 / 360 / 1080 / condition
- 条件: in-set、out-set、2bit noise、全候補同型collapse
- 候補数: 12、factor数: 8、最大sweep: 4

## 最大1080例・3 seed平均

| 指標 | Closed adaptive | Fixed null | Adaptive null |
|---|---:|---:|---:|
| in-set accuracy | 0.7071 | 0.7043 | 0.7000 |
| out-set wrong commit | 0.9812 | **0.5062** | 0.8216 |
| out-set null rate | 0.0000 | 0.1525 | **0.1599** |
| noisy accuracy | **0.3818** | 0.1741 | 0.3710 |
| noisy wrong commit | 0.5923 | **0.2799** | 0.6012 |
| collapse convergence | 0.0000 | 0.0000 | 0.0000 |
| factor evals/out-set | 14.87 | 0 | 14.02 |
| 推論/out-set | 0.0414ms | **0.0393ms** | 0.0406ms |

## 資源

- model: 82 bytes
- Peak RSS: 14,508 KiB（Python runtime込み）
- worst-case `O(HF)`、H=12、F=8、S<=4
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 判定

**null attractorには限定的な候補外信号があるが、中核仮説は反証。**

固定nullはout-set wrong commitを0.9812から0.5062へ、noisy wrong commitを0.5923から0.2799へ削減した。絶対残差は候補集合外・観測不整合の検出に増分情報を持つ。

一方、out-setの約50.6%を依然誤確定し、null rateは15.25%に留まる。adaptive分割を併用するとwrong commitが82.16%へ再悪化した。追加factorが現実適合性を改善せず、候補内差だけを強調して誤候補を一意化するためである。in-set accuracyも約0.70で、thresholdは制御データ上の固定値である。候補outcome空間は実験側供給で、生の自由日本語から対象・変数・関係・操作・目的・制約・因果候補を生成していない。collapseでは停止するが、平坦化と意味的曖昧性を区別していない。平衡伝播・局所weight学習の成立証拠でもない。

## 系列E固有の進展

必要条件を、candidate recall、outcome non-isomorphism、local separability、factor minimality、reality calibration、**adaptive factor取得中の絶対残差校正**、attractor relaxation/local learningへ更新した。絶対残差は候補外信号を持つが、候補内分割factorが誤確信を再増幅することを確認した。

## 他系列へ返す知見

- A: class分割前に全候補が観測を十分説明するか絶対残差を測る。
- B: program precisionを上げても仕様外ならnull programが必要。
- C: mechanism edgeの相対順位と絶対的介入説明力を分離する。
- D: retrieval gainで境界を選ぶ前にnull境界を保持する。

## 次の仮説

**Dual-Residual Null Attractors with Intervention-Calibrated Energy**

language reconstruction、intervention/outcome、non-target preservation、future recall、complexityの残差を分離する。候補内分割factorは絶対outcome residualも改善する場合だけ取得する。nullを候補生成失敗と観測noise/矛盾の二種類へ分ける。

最低成功条件：out-set wrong commit 0.5062を0.20未満、in-set accuracy 0.7043以上、候補16以下、sweep4以下、32KB以下、5ms/query以下、生の日本語candidate recallを0から改善。

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: 未達
