# 系列A Cycle 041 研究報告

## 仮説

**Boundary-Conditioned State Rebirth from Pre/Post Event Prediction Contrast**  
（event前後予測contrastによる境界条件付きstate再生）

Cycle 040では、複数turnの遅延予測誤差から対象切替・計画変更の弱いevent境界信号が得られた一方、microstate寿命を要求するとexecution accuracyがほぼ消失した。今回はevent境界検出とstate identity選択を別lossへ分離した。

- One-step: 各turnで最小局所誤差ruleを即時選択
- Boundary-only: 境界検出時に旧ruleを停止するが新stateを生成しない
- Rebirth: 境界後2turnの予測contrastで新microstateを再選択
- Temporal shuffle: dialogue順序を破壊して同じrebirth処理を実施

Final testの`after / future`はcandidate生成・通常rankingには使用せず、event境界と境界後contrastの評価sensorとしてのみ使用した。

## 最新系列との重複表

| 系列 | 最新中心 | Aで扱わない領域 |
|---|---|---|
| B Cycle 040 | Role-permutation quotient grammarと共同MDL | 記号・program圧縮 |
| C Cycle 040 | Cross-object state-difference tensor | 因果world graph・relation axis |
| D Cycle 040 | Leave-one-episode-out replay compression | 長期memory・再固定化 |
| E Cycle 040 | Residual eigenmode constraint field | Energy固定点・constraint topology |
| **A Cycle 041** | **event境界後の時間状態再生とpre/post予測contrast** | 今回の固有対象 |

系列Cもevent表現を扱うが、Cはobject/support/payloadの因果relation、Aは連続turn上の旧state終了・新state起動・再入を中心評価とする。

## 先行研究整理

2025年末のPARSEは階層的recurrent predictor上でprediction-error peakからevent boundaryを形成し、streaming videoで多階層event structureを学習する。ただしrecurrent predictorと知覚表現は事前に定義されている。今回の問題は、生の日本語から予測責任を持つ状態候補そのものを形成する上流課題である。

2025年のevent segmentation研究では、単一change-point精度だけではsegment identityや誤りの種類を捉えられないため、境界とsegment matchingを分離して評価する必要性が指摘されている。Cycle 040で境界F1だけが上がったため、今回はnew-state executionとの同時改善を必須条件にした。

Predictive State Representation系は、履歴と未来actionに条件付けた未来観測分布をbelief stateとして用いるが、観測・action変数は与えられている。今回の実験は、それらを自由日本語から自律生成できるかを検証した。

## 3 seed平均

| 条件 | One-step 精度/wrong | Boundary-only 精度/wrong | Rebirth 精度/wrong | Rebirth境界F1 | Shuffle境界F1 |
|---|---:|---:|---:|---:|---:|
| 対象切替 | 0.1528/0.7361 | 0.1528/0.5556 | 0.1528/0.7361 | 0.2143 | 0.3117 |
| 主語省略 | 0.0833/0.7778 | 0.0833/0.5833 | 0.0833/0.7778 | 0.0513 | 0.2747 |
| 言い換え | 0.1111/0.7778 | 0.1111/0.6111 | 0.1111/0.7778 | 0.2179 | 0.3402 |
| 未知語順 | 0.0000/0.8889 | 0.0000/0.6806 | 0.0000/0.8889 | 0.2381 | 0.3062 |
| 複数段落 | 0.0417/0.9167 | 0.0417/0.7500 | 0.0417/0.9167 | 0.0556 | 0.3882 |
| 計画変更 | 0.1806/0.7917 | 0.1806/0.5556 | 0.1806/0.7917 | 0.4189 | 0.4622 |
| 反実仮想 | 0.1389/0.7500 | 0.1389/0.5556 | 0.1389/0.7500 | 0.2051 | 0.3238 |

追加診断:

- Rule: 22.33
- Rebirth event: 4.33
- Post-boundary correct execution: 0.00
- Model: 1213 bytes
- Training: 0.000245 sec
- Switch inference: 0.0263 ms/example
- Paragraph inference: 0.0251 ms/example
- Peak RSS: 110496 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。Boundary-conditioned rebirthはOne-stepの能力を一件も改善しなかった。**

### 境界検出は再現したが、順序固有ではない

Rebirth方式では対象切替の境界F1が0.2143、計画変更が0.4189だった。しかしTemporal shuffleではそれぞれ0.3117、0.4622へ上昇した。

したがって今回のboundary detectorは意味的な時間順序を捉えず、局所ruleのsurface mismatch jumpへ反応している。Cycle 040の時間順序依存信号は、この実装では再現しなかった。

### RebirthとOne-stepが完全同一

全条件でRebirth accuracy・wrong commitはOne-stepと完全に同じだった。境界後2turn contrastで再rankingしても選択ruleが一件も変わらなかった。

> **Event境界を検出して候補を再評価するだけでは、候補集合に新しいstate identityが存在しない限りstate rebirthにはならない。**

### Boundary-onlyは誤commitだけを減らす

Boundary-onlyはaccuracyを維持したままwrong commitを減らした。対象切替ではwrongが0.7361から0.5556へ減少した。

これは旧stateを停止する安全gateとしては限定的に有効だが、新state executionを増やしていない。棄権増加による安全化であり、予測状態創発ではない。

### 支配的失敗

- 境界前後で同じsurface-local rule集合を使っている
- Post-event candidate birthがなく、既存ruleの再rankingに留まる
- Object identity・value binding・operation・goalが共同生成されない
- Shuffled orderでも境界F1が維持・増加する
- 主語省略、未知語順、計画変更、反実仮想の意味state分離が成立しない

## 反証条件

仮説支持には最低限、次が必要だった。

1. RebirthがOne-stepよりpost-boundary executionを改善
2. 対象切替でboundary F1とnew-state accuracyを同時改善
3. Correct temporal orderがshuffleより優れる
4. 計画変更で撤回stateを終了し最終goalを起動
5. 主語省略で前eventのstateを正しく再起動
6. 反実仮想で実行・非実行populationを並行保持

すべて未達。

## 既存方式との差

Transformer attention、分類器、固定ontology、手書きslot、辞書、RAG、外部LLMは使用していない。複数turnのprediction errorからevent境界を検出し、pre/post candidate populationを分離してstateを再選択した。

ただし現状は離散surface edit ruleの再rankingであり、active inference、world state、semantic event identityには未到達。

## 資源量・必要計算量

- Rule induction: `O(NL)`
- Online candidate evaluation: `O(TR)`
- Post-boundary contrast: `O(kR)`、`k=2`
- Rule上限: 64
- Model: 約1213 bytes
- Training: 約0.000245 sec
- Inference: 約0.025〜0.027 ms/example

1GB未満・5ms未満は小規模条件で達成した。弱いスマートフォンCPU実機は未検証。性能が低いため、資源条件達成は汎用知能成立の証拠ではない。

## 系列A固有の進展

> **Boundary detectionとstate selectionを分離しても、境界後に新候補を生成せず既存surface ruleを再rankingするだけでは、executionは一切改善しない。Boundary-only停止gateは誤commitを減らせるが、state rebirthにはcandidate birthが必要である。**

## 他系列へ返す知見

- B: Grammarの再選択だけでなく、境界後の新production birthを独立評価すべき。
- C: Event boundaryとnew-world rolloutを必ず同時評価し、境界F1単独を因果event成功とみなさない。
- D: Reconsolidation gateは誤readを減らせても、新address birthがなければ記憶能力を増やさない。
- E: Basin switchやconstraint field追跡では、旧候補停止と新attractor生成を分離評価すべき。

## 次の仮説

**Prediction-Residual State Rebirth from Post-Event Counterexample Synthesis**  
（event後反例合成による予測残差駆動state再生）

1. Boundary後に既存ruleを再rankingするだけでなく、失敗予測と次2turn観測の局所残差から新境界候補を生成
2. State区間・command value区間・object区間を同時にshift／split／merge
3. Pre-event ruleでは説明できず、post-event 2turnを改善する候補だけbirth
4. Correct order／shuffled order／rebirthなし／residual birthなしを比較
5. 対象切替でboundary F1・new-state execution・wrong carryを同時評価
6. 計画変更では撤回stateをnegative residualとして抑制
7. 主語省略では直前eventのbest stateを再起動候補へ含める
8. 反実仮想では実行・非実行残差から二つのpopulationを生成

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
