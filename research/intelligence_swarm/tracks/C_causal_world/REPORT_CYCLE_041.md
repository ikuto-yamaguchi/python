# 系列C Cycle 041

## 仮説

**Predictive Relation Axes from Leave-One-World-Out Difference Completion**  
（leave-one-world-out差分補完による予測的relation axis創発）

Cycle 040では、観測済みafter差分をobject/support/payload軸へ分解するとCorrect probe固有の低rank成分が形成されたが、finalの`before + command`から同じ軸を再生成できず全面棄権した。

今回はmulti-world群のうち1 worldのafter差分を完全に隠し、残りworldの差分軸から欠測worldの差分signatureを補完した。補完誤差が小さく、複数groupで再現するaxisだけを保持し、finalでは`before + command`から同axisを再生成できるか検証した。

## 最新系列との重複表

| 系列 | 最新中心 | Cで棄却・分離した領域 |
|---|---|---|
| A | Boundary-conditioned state rebirth | 時間境界後のstate再起動 |
| B | Deletion-causal role grammar | MDL・role削除十分集合 |
| D | Counterfactual-deletion memory generator | 長期memory・双方向閉路 |
| E | Leave-one-counterexample-out constraint mode | Energy field・残差mode |
| **C** | **欠測worldの因果差分補完とrelation axis** | object/value/operation変化から未知transitionを予測 |

Eも欠測counterexample予測へ進んでいるため、Cではenergy mode形成を扱わず、object/value/operation world群の**欠測state transition予測**と未知対象転移だけを中心評価にした。

## 実装

- 1 groupを4 worldで構成
  - 同object・別value
  - 同object・別operation
  - 別object・同value
- 各worldを順番に隠し、残り3 worldからobject/support/payload axisの直積候補を補完
- Literal / Rank-1 / Completion / Group-shuffleを比較
- Final testのafter/futureはcandidate生成・rankingに不使用
- 固定ontology、手書きslot、辞書、RAG、外部LLMなし

## 3 seed平均

| 条件 | Literal | Rank-1 | Completion | Shuffle | Completion Null |
|---|---:|---:|---:|---:|---:|
| 既知 | 0 | 0 | 0 | 0 | 1.0 |
| 未知語順 | 0 | 0 | 0 | 0 | 1.0 |
| 未知語彙 | 0 | 0 | 0 | 0 | 1.0 |
| Rename | 0 | 0 | 0 | 0 | 1.0 |
| 入れ子 | 0 | 0 | 0 | 0 | 1.0 |
| 主語省略 | 0 | 0 | 0 | 0 | 1.0 |
| 複数段落 | 0 | 0 | 0 | 0 | 1.0 |
| 計画変更 | 0 | 0 | 0 | 0 | 1.0 |
| 反実仮想 | 0 | 0 | 0 | 0 | 1.0 |

追加診断：

- Literal axis: **24**
- Rank-1 axis: **24**
- Completion axis: **24**
- Shuffled axis: **8**
- Completion hit: **75.67**
- Shuffled completion hit: **17.33**
- Completion model: **約905 bytes**
- Training: **0.0254秒**
- Seen inference: **9.56 ms/example**
- Paragraph inference: **26.42 ms/example**
- Counterfactual inference: **33.79 ms/example**
- Peak RSS: **119,028 KiB**（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### 欠測差分補完信号は形成

Correct groupingでは平均24 axisと約75.7件のleave-one-world-out補完hitが形成された。Groupをshuffleするとaxisは8件、補完hitは17.3件へ減少した。

したがって、同じmulti-world群の残り差分から欠測差分signatureを補完する信号自体は存在する。

### Final入力で候補0

しかし全条件でexecution accuracy 0、null率1.0、candidate数0だった。

学習時の補完axisは、隠していない3 worldの**観測済みafter差分**から作られている。Finalの`before + command`だけではsupport axisを同じ形で生成できない。

> 欠測world差分を他の観測済みworldから補完できても、観測前入力から因果transitionを生成できるとは限らない。

### Correct groupingとshuffleの差は因果能力ではない

Correct groupingはshuffleより多くのaxisとcompletion hitを持つが、両方式ともfinal能力0である。これはmulti-world表面template内の差分共分散を捉えた証拠であり、object identity、relation、operation、goal、constraintの獲得証拠ではない。

### 反証条件

- Leave-one-world-out差分補完 > shuffle: **達成**
- Final before+commandからaxis再生成: **未達**
- 未知対象へのtransition転移: **未達**
- Object axis除去でtarget移動だけ崩壊: **未検証**
- Payload axis除去でvalue共変だけ崩壊: **未検証**
- 計画変更・反実仮想world分離: **未達**

## 先行研究との差

Causal-JEPAはobject-level maskingにより他objectから隠したobject stateを予測し、latent interventionを誘導するが、object tokenは既に与えられている。COMETやSTICAもslot/object表現とaction bindingを前提にworld transition・planningを行う。今回の未解決点は、そのさらに上流にある生の日本語からobject/support/payload axis自体を予測生成する問題である。

## 資源量

- Training: `O(G W A^3)`
- Inference: `O(L^3)`
- Axis上限: 24
- Candidate上限: 256
- Model: 約905 bytes
- Peak RSS: 119,028 KiB

1GB未満は達成。推論は既知で約9.56ms、複数段落で約26.42msのため5ms未満は未達。弱いスマートフォンCPU実機は未検証。

## 系列C固有の進展

> 観測済みmulti-world差分の低rank整理から一歩進み、leave-one-world-out欠測差分補完がcorrect grouping固有に成立することを確認した。しかし補完axisは依然after観測へ依存し、入力から因果eventをbirthできない。

## 他系列へ返す知見

- A: 境界後state rebirthは、境界後outcomeを見ずにstate supportを生成できるかを分離評価すべき。
- B: 削除因果roleがcross-form補完できても、入力からrole境界を再生成できなければsemantic grammarではない。
- D: Memory generatorのleave-one-episode-out補完はquery時のaddress再生成を別ゲートにすべき。
- E: Leave-one-counterexample-out residual modeは、hidden residual予測だけでなくfinal candidate rankingの因果差を必須化すべき。

## 次の仮説

**Prospective Support Axes from Counterfactual Command Completion**  
（反実仮想command補完によるprospective support axis創発）

次はafter差分を一切用いず、multi-world command群の一つを隠し、残りworldのobject/value/operation交換関係から隠したcommandとprospective supportを同時補完する。

1. 同じbeforeに対するobject/value/operation違いのcommand群を構成
2. 一つのcommandを隠す
3. 残りcommandの交換構造から隠したobject/value/operation境界を補完
4. 補完したcommandからprospective support候補を生成
5. Outcomeは独立probeでのみ監査
6. Correct grouping／shuffle／after-difference completion／command-onlyを比較
7. Unknown object・Rename・別状態表現でsupport転移を評価
8. Axis lesionでtarget/value/operationの選択的損失を監査
9. 計画変更では撤回commandと最終commandを別axis化
10. 反実仮想では実行・非実行commandを並列補完

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
