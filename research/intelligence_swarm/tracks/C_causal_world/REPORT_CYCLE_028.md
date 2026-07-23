# 系列C Cycle 028 研究報告

## 仮説

**Positive Witness Birth from Bidirectional Local Alignment Search**  
（双方向局所整列探索によるpositive witness創発）

Cycle 027ではevent当たりpositive witnessが平均1.21件しかなく、multi-witness fiber監査が空になった。今回は既存eventのsurface contextをtarget episodeへそのまま適用せず、source/target双方の局所edit contextを独立抽出し、保存shape・command context・state context・future応答を使って双方向整列した。

採用条件:
- source→target局所実行がtarget afterを再構成
- target→source局所実行がsource afterを再構成
- non-target damage 0
- alignment score 0.62以上
- 3環境以上・3 alignment以上の連結成分のみfiber化

## 先行研究整理

2025年のcausal abstraction研究では、低水準介入と高水準介入の対応に観測・介入・反実仮想の整合が必要であり、lossy mappingや部分的identifiabilityが明示的に扱われている。今回のraw日本語alignmentは、それらで前提となる低水準変数・介入target自体を生成する上流課題である。

- Causal Abstraction Inference under Lossy Representations, ICML 2025
- On the Identifiability of Causal Abstractions, AISTATS 2025
- Aligning Graphical and Functional Causal Abstractions, CLeaR 2025
- Causal-JEPA, 2026: object-level latent interventionは有効だがobject representationは事前形成される

## 他系列との重複表

| 系列 | 最新中心 | Cで棄却・分離した領域 |
|---|---|---|
| A | Cross-encoded residual routing | 談話commitment・予測責任 |
| B | Counterfactual test programs from competing binding graphs | program selection・MDL |
| D | Shapley-sparse memory coalition credit | 長期memory再固定化 |
| E | Predictor-independent residual hyperedge | energy・attractor |
| **C** | **双方向実行整列による正の介入witness生成** | 今回の固有対象 |

## 実験条件

- seed: 1 / 7 / 19
- train: 96 episode/seed（seen・held・Rename・alternateを混合）
- test: 24例/split/seed
- event上限: 32
- alignment上限: 256
- ablation: Surface / Alignment / Fiber
- test: 因果局所更新、未学習言い換え、Rename、別状態表現、主語省略、複数段落、計画変更、反実仮想
- hidden object/field/value labelsは評価器のみ

## 3 seed平均

| 条件 | Surface | Alignment | Fiber |
|---|---:|---:|---:|
| 既知 | 0.1667 | 0.1667 | 0.1667 |
| 未学習言い換え | 0.0972 | 0.0972 | 0.0972 |
| Rename | 0.0417 | 0.0417 | 0.0417 |
| 別状態表現 | 0.0694 | 0.0694 | 0.0694 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 複数段落 | 0.1250 | 0.1250 | 0.1250 |
| 計画変更 | 0.0556 | 0.0556 | 0.0556 |
| 反実仮想 | 0.0972 | 0.0972 | 0.0972 |

追加診断:
- event: 32.00
- bidirectional alignment: 250.67
- alignment環境coverage: 4.00
- fiber: 2.33
- fiber member: 23.67
- sequential coverage: 0.0444
- sequential conditional accuracy: 0.3333

## 判定

**中核仮説は強く反証。**

### Alignmentとfiberは多数形成

平均250.67件の双方向alignment、2.33 fiber、23.67 memberが形成された。Cycle 027のfiber 0からは構造数として増えた。

### しかし能力増分は全条件0

Surface / Alignment / Fiberは全splitでaccuracy・wrong commit・null率・候補数が完全同一だった。fiber scoreを追加しても、held-out event選択や新しい状態遷移を一件も改善していない。

### 「双方向成功」が独立証拠ではない

source→targetとtarget→sourceは、それぞれ各episode自身から抽出した局所eventを使っている。そのため両方向成功は同じ潜在mechanismをtransportした証拠ではなく、各episodeの自己再構成を並べて一致scoreを付けたものに退化した。

> **Target側の局所eventをtarget自身のafterから抽出してよいなら、positive witness birthは自明化する。未知targetのafterを見ずにsource mechanismだけからtarget transitionを予測できなければ、因果transportではない。**

### Fiberはsurface-shape connected component

fiberは複数環境を跨いだが、old/new shapeと局所context類似で連結した成分であり、object・relation・state-variable identityを表さない。

### 主語省略・計画・反実仮想

主語省略は全方式0、null率1.0。計画変更0.0556、反実仮想0.0972もSurfaceと同一で、goal revisionや未実行worldを形成した結果ではない。

### Counterfactual composition未成立

Sequential coverage 0.0444、conditional accuracy 0.3333で、alignment/fiberによる増分0。

## 相関暗記と因果理解の反証条件

支持には以下が必要だった。
1. target afterをalignment生成に使わない
2. source mechanismだけでtarget afterを予測
3. Rename・alternateでpositive witness coverage増加
4. Alignment/FiberがSurfaceよりexecution accuracyを改善
5. non-target保存とwrong抑制
6. fiber利用でcounterfactual coverage改善

今回は1を満たさず、2〜6も能力増分0。

## 資源量

- model: 16863 bytes
- training: 0.054179 sec
- inference: 0.071410 ms/example
- Peak RSS: 111080 KiB（Python runtime込み）
- graph: event 32 / alignment 250.67 / fiber 2.33
- 計算量: event抽出 `O(NL)`、bidirectional alignment `O(P²L)`、component形成 `O(P+A)`、推論 `O(PL)`

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォン実機は未検証。

## 系列C固有の進展

> **Positive witnessを増やす際、target after由来のeventを使うと双方向整列が自己再構成へ退化する。Open-form witness birthは、target outcomeを隠した状態でsource mechanismからtarget transitionを予測する厳密なholdoutが必要。**

## 他系列へ返す知見

- A: current outcome由来residualでrouteを作ると予測責任が自明化するため、選択時点を分離する。
- B: counterfactual testは競合programの予測から生成し、正解afterからcutを作らない。
- D: coalition creditはheld-out answerをmemory identity形成へ漏洩させない。
- E: predictor-independent residualでも、candidate選択後の正解viewをnode生成へ使うとleakageになる。

## 次の仮説

**Outcome-Blind Positive Witness Birth from Source-Only Mechanism Transport**  
（source mechanismのみの転送によるoutcome-blind positive witness創発）

1. target before/commandだけをalignment探索へ使用
2. target after/futureは評価時まで完全に隠す
3. source eventの保存区間・change shapeをtargetへ写す候補を複数生成
4. target afterを正しく予測した候補だけ事後にpositive witness化
5. wrong/noexecをalignment pruningへ蓄積
6. Rename・alternate・未知objectでwitness coverageを主評価
7. 3環境以上のoutcome-blind witness後にのみfiber形成
8. fiber利用でcounterfactual rolloutを評価

## 最終状態

- 高校生級: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機: **未検証**
- 完成: **未達**
