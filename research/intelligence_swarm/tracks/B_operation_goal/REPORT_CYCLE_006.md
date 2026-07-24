# 系列B Operation / Goal Cycle 006

## 仮説

**Joint Version-Space Collapse for Executable Operation Birth**  
（言語・世界の共同version-space縮退による実行可能操作創発）

GOV-007 / AF-008に従い、候補を事前に類似度でfamily化せず、候補diagramを外部識別行為で生存・破壊する順序を維持した。A Cycle 007ではworld側の候補結果分離だけを最大化するActive選択がhidden自由日本語で局所陽性を示した一方、未知語順・複数段落ではRandomに負けた。

今回は、識別行為の価値を次の積として定義した。

- world候補が返す結果signatureの分離量
- raw Japaneseから得る32候補分布のentropy

world-only、random、outcome shuffle、oracle selectorと比較し、world候補とlanguage候補のversion spaceを同時に縮小すれば、未知語彙domainでoperation / goal unitが生まれるかを検証した。

## 禁止事項と漏洩監査

- test時after / completed trajectory不使用
- fixed ontology / handwritten slot / span proposal不使用
- domain辞書 / shared object ID不使用
- string retrieval / RAG / external LLM不使用
- candidate familyの事前類似度cluster不使用
- 3 seed: 1 / 7 / 19

## 3 seed平均（完全語彙非共有hidden d3）

| 条件 | Joint-selector joint | World-only | Random | Outcome shuffle | Joint inverse | Goal変更 | Failure repair |
|---|---:|---:|---:|---:|---:|---:|---:|
| Held | 0.0625 | 0.0625 | 0.0347 | 0.0139 | 0.2153 | 0.1181 | 0.1875 |
| 未知語順 | 0.0208 | 0.0208 | 0.0347 | 0.0208 | 0.2917 | 0.1111 | 0.2917 |
| 複数段落 | 0.0625 | 0.0625 | 0.0208 | 0.0347 | 0.3542 | 0.1389 | 0.2986 |
| 自由日本語 | 0.0417 | 0.0417 | 0.0347 | 0.0208 | 0.2153 | 0.1319 | 0.2639 |
| Rename | 0.0278 | 0.0278 | 0.0417 | 0.0278 | 0.2361 | 0.1458 | 0.2292 |

Joint chanceは0.03125、inverse chanceは0.25。Strict gateは **0 / 3 seed**。

## 判断

**中核仮説は強く反証。能力上の進歩は未認定。G1/G2未達。**

### Joint selectorとworld-onlyが完全同一

全評価条件でJoint selectorとworld-onlyの測定値が一致した。bootstrap言語候補分布のentropyはepisode間でほぼ定数となり、観測順位を一件も変えなかった。

これは単なる実装上の係数不足ではなく、より上流の失敗である。現在のraw Japanese候補モデルは、観測前には「どの曖昧性がその介入で解けるか」を区別できず、言語version-spaceをworld actionへ接続する情報を持たない。

### Hidden domainの外部能力は不安定

- 複数段落inverseは0.3542でRandom 0.2708を上回った
- しかし未知語順jointは0.0208でRandom 0.0347を下回った
- 自由日本語inverseは0.2153でchance未満
- goal変更は0.11〜0.15でchance 0.25未満
- failure repairもRandom / shuffleを一貫して上回らない

一条件の陽性は、prospective・inverse・goal・repairを同じlatent operationが閉じた証拠ではない。

### Oracle selectorも上限を改善しない

oracle action selectorを用いてもhidden d3のjoint / inverseは改善しなかった。したがって現時点の主因は「識別行為の選び方」だけではなく、候補集合に正しい再利用可能operation unitが存在しない **candidate-support failure** である。

> 最小識別行為は、正しい候補が既に存在する場合の選別条件にはなり得るが、raw Japaneseからoperation候補を誕生させる原理ではない。

## A/C/Dへ返す知見

- **A**: language entropyをworld分離量へ掛けるだけではidentity曖昧性を解けない。候補が観測を説明不能になった残差から、新しいlanguage/world候補をbirthする必要がある。
- **C**: action selectorの改善より先に、Correct候補が存在するかをoracleで監査する。oracleでも閉じない場合は介入最適化を停止する。
- **D**: formal memory eligible operation unitは0。取得前候補support failureであり、保持失敗・catastrophic forgettingではない。
- **E**: `joint_version_space_entropy_weighting_creates_operation_identity` はAF-008の不採用下位仮説候補。

## 資源量

- Model: **98474 bytes**
- Peak RSS: **112092 KiB**（Python / NumPy runtime込み）
- Runtime: **8.234 sec / 3 seeds**
- Observation budget: 24 / domain
- Candidate: 32
- Estimated update: 12,288 ops / episode
- Estimated inference: 12,288 ops / query
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 次の仮説

**Residual-Born Operation Candidates from Joint Explanation Failure**  
（共同説明失敗残差からの操作候補創発）

次は既存候補を選別するだけにしない。

1. raw Japanese候補とworld候補の全てが観測結果を説明できないepisodeをbirth triggerにする
2. 言語予測残差とworld transition残差を別々に保持する
3. 一つのtarget / transition / goalだけを修復する最小局所候補を生成する
4. 別episodeで同じ修復効果が再現した候補だけをoperation proposalにする
5. Candidate birth / selector-only / residual shuffle / oracle-supportを比較する
6. hidden domainでprospective / inverse / goal変更 / failure repairを同時監査する

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
