# 系列A Cycle 040 研究報告

## 仮説

**Delayed-Error Event Boundary Birth from Competing Microstate Lifetimes**  
（競合microstate寿命の遅延誤差からのevent境界創発）

Cycle 039では局所ruleが48件形成されたが、最初の明示turnで同点となり、active state cellを一度も起動できなかった。今回は初回turnで単一ruleへ即決せず、最大12個のmicrostate候補を並行維持し、prospective after、future継続、non-target保存、command object整合の遅延誤差を複数turnで累積した。

累積誤差が低い候補だけ寿命を延長し、既存候補が崩壊して新候補が優勢になる時点をevent boundaryとした。Final testのafter/futureはcandidate生成・rankingには使用せず、評価時の遅延誤差sensorとしてのみ使用した。

## 最新系列との重複表

| 系列 | 最新中心 | Aで扱わない領域 |
|---|---|---|
| B Cycle 039 | Paired-world co-segmentation grammar | MDL・記号grammar |
| C Cycle 039 | Multi-world intervention-closure event family | 因果world graph |
| D Cycle 039 | Paired replay fingerprint reconsolidation | 長期memory・slow統合 |
| E Cycle 039 | Constraint-homotopy attractor tracking | Energy固定点・constraint continuation |
| **A Cycle 040** | **複数turnの遅延予測責任とmicrostate寿命によるevent境界** | 今回の固有対象 |

系列Cもevent familyを扱うが、Cは介入閉包と因果event identity、Aは時間方向の状態持続・再起動・終了を中心評価とする。

## 3 seed平均

| 条件 | One-step 精度/wrong | No-lifetime 精度/wrong | Lifetime 精度/wrong | Lifetime境界F1 | 時系列Shuffle 精度/wrong |
|---|---:|---:|---:|---:|---:|
| 既知明示 | 0.2679/0.1000 | 0.2679/0.1000 | 0/0 | 0.0278 | 0.0145/0.2294 |
| 主語省略 | 0.2334/0.1000 | 0.2334/0.1000 | 0/0 | 0.0278 | 0.0290/0.2119 |
| 言い換え | 0.0167/0.0500 | 0.0167/0.0500 | 0/0 | 0.0317 | 0/0.2500 |
| 未知語順 | 0.0435/0.1500 | 0.0435/0.1500 | 0/0 | 0 | 0/0.2226 |
| 複数段落 | 0.2160/0.0123 | 0.2160/0.0123 | 0/0 | 0.1298 | 0.0247/0.1250 |
| 対象切替 | 0.3284/0.0575 | 0.3284/0.0575 | 0.0115/0 | **0.3126** | 0.0115/0.1646 |
| 計画変更 | 0.2562/0.0123 | 0.2562/0.0123 | 0/0 | **0.1239** | 0.0370/0.1003 |
| 反実仮想 | 0.0435/0.0500 | 0.0435/0.0500 | 0/0 | 0 | 0/0.1636 |

追加診断:

- Rule: 64
- Lifetime retain events: 1.67（既知明示）
- Lifetime terminate events: 111.33（既知明示）
- Model: 3,345 bytes
- Training: 0.001916 sec
- Seen inference: 0.0692 ms/example
- Paragraph inference: 0.0913 ms/example
- Peak RSS: 160,120 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。Event boundary検出に限定的な信号はあるが、予測状態能力を破壊した。**

### Microstate寿命は境界信号を生んだ

Lifetime方式では、対象切替条件のevent boundary F1が **0.3126**、計画変更条件が **0.1239** となった。One-step・No-lifetime・Temporal shuffleのboundary F1は0であるため、turn順と遅延誤差の累積が境界信号へ寄与した。

### しかし実行精度はほぼ消失

One-step方式は既知明示で0.2679、主語省略で0.2334、対象切替で0.3284だった。Lifetime方式では対象切替の0.0115を除き全条件でaccuracy 0となった。遅延commit条件が厳しすぎ、正候補も寿命延長前に消失した。

> **複数turnの遅延誤差はevent boundaryの弱い検出信号になり得るが、surface-local microstateから意味的predictive stateを生成しない。**

### Boundaryとstate identityが分離している

対象切替でboundary F1が上がっても、正しいprospective state executionはほぼ0である。検出した境界はobject stateの終了、新object stateの開始、goal revision、event semanticsを表すものではなく、候補集合の急な崩壊点にすぎない。

### 時系列shuffleとの比較

Temporal shuffleではboundary F1が全条件0になった一方、誤commitが増えた。時間順序が境界信号に必要であることは確認できたが、正しい状態identityの形成には不十分だった。

### 支配的失敗

- 初期microstateは相対位置・文字shapeに依存
- command object整合が弱く、主語省略で対象を再起動できない
- future sensorは値文字列の存在確認に退化
- 累積誤差が意味的stateではなくsurface rule寿命を選択

## 反証条件

仮説支持には最低限、次が必要だった。

1. Lifetime方式がOne-stepよりexecution accuracyを改善
2. 主語省略で前turn stateを正しく再起動
3. 対象切替でboundary F1と正しいnew-state executionが同時改善
4. 計画変更で撤回microstateを終了し、最終goalを保持
5. Temporal shuffleで能力が低下
6. 言い換え・未知語順・複数段落へ転移

5のboundary signalだけ達成し、1〜4・6は未達。

## 既存方式との差

Transformer attention、分類器、固定ontology、手書きslot、辞書、RAG、外部LLMは使用していない。単一turn分類ではなく、複数microstateを並行維持し、遅延prediction errorによって寿命・終了・event boundaryを更新する。

ただし現状は離散surface edit ruleの競合であり、world state、active inference、event semanticsには未到達。

## 資源量

- Rule induction: `O(NL)`
- Online update: `O(TR)`
- Rule上限: 64
- Active microstate上限: 12
- Model: 約3,345 bytes
- Training: 約0.001916 sec
- Inference: 0.07〜0.10 ms/example

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列A固有の進展

> **Microstate寿命と遅延誤差は、候補崩壊点を時間境界として検出できる。しかし意味的state identityがないまま寿命だけを導入すると、event boundary信号と引き換えに実行能力を失う。**

## 他系列へ返す知見

- B: 長期traceを圧縮する前に、boundary signalとproduction identityを分離して評価すべき。
- C: Event familyの評価では、境界F1だけでなく新state rolloutを同時に要求すべき。
- D: Replay寿命・再固定化は、正しいaddress identityがない場合、棄権を増やす。
- E: Homotopyや盆地追跡でも、盆地identityとconstraint急変点を分ける必要がある。

## 次の仮説

**Boundary-Conditioned State Rebirth from Pre/Post Event Prediction Contrast**  
（event前後予測contrastによる境界条件付きstate再生）

1. Event boundary前後の候補集合を別populationとして保持
2. 境界前に良かったruleを新eventへ無条件carryしない
3. 境界後2turnの予測を最も改善する新microstateをbirth
4. Boundary detectionとstate identity selectionを別lossに分離
5. Pre-event／post-event prediction contrastを局所credit化
6. Correct temporal order／shuffled order／boundaryなし／rebirthなしを比較
7. 対象切替でboundary F1とnew-state executionの同時改善を必須化
8. 計画変更では撤回stateを終了し、最終goal stateを再生
9. 反実仮想では実行・非実行populationを並行保持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
