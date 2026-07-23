# 系列A Cycle 025 研究報告

## 仮説

**Event-Gated Prospective State with Learned Commitment Termination**  
（学習されたcommitment終了条件を持つevent-gated前向き状態）

Cycle 024では、前turnから持続候補を無条件carryすると主語省略のpair recallが増えた一方、通常turnへ旧候補を誤注入し、accuracy 0.0833・wrong 0.9167だった。

今回は現在turnのafter/futureを使わず、raw `before / command` と前turn commitmentだけから、carry persistence、現在turnの明示候補強度、旧commitmentに対する新候補novelty、command冒頭のprediction-error boundaryをevent featureとして生成し、継続か終了・切替かを決める疎なgateを検証した。固定ontology、手書きslot、辞書、外部LLM、RAG、Transformer attentionは使用していない。

## 先行研究整理

- Action-conditional self-predictive learningは、将来表現予測をaction条件付き状態学習として定式化するが、latent encoderとactionは定義済み。
- Multi-view fused state learningは、冗長・欠損view下でtask-relevant stateを形成するが、viewと制御課題が既知。
- Segment feedbackの研究は、長いtrajectoryをevent segmentへ分けることが学習信号を変えると示すが、segment feedback自体は与えられる。
- 行動だけからbelief・goalを予測する理論には未観測環境での識別限界があり、表面挙動だけで内部状態を一意化できない。

今回の課題は、生の日本語文字列からevent boundaryとcommitment terminationを同時に形成する、さらに上流の問題である。

## 最新系列との重複表

| 系列 | 最新中心 | 限定信号 | 支配的失敗 | Aとの分離 |
|---|---|---|---|---|
| B | Role-exchange binding seed | 複数view surface anchor | Rename・省略でbinding 0 | MDL・置換検定は扱わない |
| C | Success-conditioned event identity | 評価の情報対称化 | Null支配identity collapse | 因果mechanism graphは扱わない |
| D | Factorized endpoint evidence ladder | 厳密gateで誤読抑制 | 全endpoint棄却 | 長期memoryは扱わない |
| E | Constraint-edge birth before commutator | Null安全停止 | edge未形成・交換子0 | Energy dynamicsは扱わない |
| **A** | **予測誤差eventによるcommitment継続・終了** | 今回検証 | 前向き談話state選択 | 系列固有 |

重複候補として、Bのrole交換、Cのenvironment mechanism identity、Dのendpoint再構成、Eのconstraint edgeを棄却した。

## 実験条件

- Seed: 1 / 7 / 19
- 学習: 48 episode
- Test: 12 episode / split / seed
- Predictive prototype: 最大64
- Gate prototype: 最大96
- Commitment: 最大4
- Object/value候補: 各最大8
- Pair: 最大48
- Ablation: No carry / Unconditional carry / Event gate / Event gate + Null
- 自由日本語条件: 既知、未学習言い換え、Rename、別状態表現、入れ子、主語省略、明示切替と省略が混在するstream、複数段落、計画変更

## 3 seed平均

| 条件 | No carry pair/acc | 無条件carry pair/acc | Event gate pair/acc | Gate carry率 |
|---|---:|---:|---:|---:|
| 既知 | 0.0556 / 0.0556 | 0.0833 / 0.0833 | 0.0556 / 0.0556 | 0.0000 |
| 未学習言い換え | 0.1389 / 0.1111 | 0.1667 / 0.1389 | 0.1389 / 0.1111 | 0.0000 |
| Rename | 0.0556 / 0.0556 | 0.0833 / 0.0278 | 0.0556 / 0.0556 | 0.0000 |
| 別状態表現 | 0.3611 / 0.0833 | 0.3056 / 0.0833 | 0.3611 / 0.0833 | 0.0000 |
| 入れ子 | 0.0278 / 0.0278 | 0.0556 / 0.0556 | 0.0278 / 0.0278 | 0.0000 |
| 主語省略 | 0.0833 / 0.0278 | 0.3333 / 0.1111 | 0.0833 / 0.0278 | 0.0000 |
| 明示切替混在 | 0.0833 / 0.0278 | 0.3333 / 0.1111 | 0.0833 / 0.0278 | 0.0000 |
| 複数段落 | 0.0278 / 0.0278 | 0.0000 / 0.0000 | 0.0278 / 0.0278 | 0.0000 |
| 計画変更 | 0.0278 / 0.0278 | 0.0556 / 0.0556 | 0.0278 / 0.0278 | 0.0000 |

主要gate診断:

- 主語省略 gate carry率: 0.0000
- 主語省略 gate正答率: 0.5000
- 主語省略 termination precision: 0.5000
- 切替混在 gate正答率: 0.3333
- 切替混在 wrong carry率: 0.0000
- 既知 termination precision: 1.0000

## 判定

**中核仮説は強く反証された。終了・切替の誤carry抑制には限定信号があるが、継続判定を学習できなかった。**

### Gateはほぼ常に終了を選択

Event gateのcarry率は全splitで0だった。

通常turnではこれにより無条件carryのwrong carry 1.0を0へ抑え、termination precision 1.0になった。しかし、主語省略でもcarryしなかったため、無条件carry pair recall 0.3333からEvent gate pair recall 0.0833へ悪化した。

つまりgateは継続・終了を識別したのではなく、**安全側へ全面終了する退化解**を学んだ。

### 明示切替混在でもgate正答率0.3333

明示object切替と主語省略が混ざるstreamでは、無条件carry pair recall 0.3333、Event gate pair recall 0.0833、Gate正答率0.3333、Wrong carry 0だった。

誤carryは止めたが、正しい継続も全て消した。termination precisionだけでは談話state能力を評価できず、continuation recallとの両立が必要である。

### 候補生成・選択は改善なし

Gate方式はNo-carry方式とほぼ同一のpair recall・accuracyだった。event featureを加えてもobject/value候補classやrankingを改善していない。

### 計画変更は依然ほぼ0

計画変更pair recall / accuracyは0.0278であり、旧goal・新goal・revisionを時間的抽象状態として形成できていない。

### Nullは全面棄権

Gate+Nullは全splitでwrong 0、null率1.0、accuracy 0だった。安全停止としてのみ機能する。

## 反証条件

支持には最低でも、主語省略で無条件carryのpair recallを維持、通常turnでwrong carryを低下、明示切替混在streamでcontinuation recallとtermination precisionを同時改善、Gate使用でaccuracyがNo-carryを上回る、計画変更で旧goal終了と新goalcommitを分離、5ms未満、が必要だった。今回はwrong carry低下だけを限定的に満たした。

## 資源量

- Model: 13,044 bytes
- Predictive state: 64
- Gate prototype: 47.33
- 学習時間: 0.357986 sec
- 推論: 既知 17.359 ms/example、主語省略 18.409 ms/example
- Peak RSS: 111,492 KiB（Python runtime込み）
- 推定計算量: character prediction `O(NL)`、interval proposal `O(L)`、event gate `O(G)`、sparse pairing `O(KoKv)`、`Ko,Kv≤8`

1GB未満は達成したが、5ms目標と弱いスマートフォン実機検証は未達。

## 系列A固有の進展

> **commitment終了を導入するとwrong carryは抑えられるが、継続証拠がsurface overlapだけではgateが全面終了へ退化する。継続・終了の二値gateではなく、各commitmentが次観測のどの部分を予測するかを個別に競合させる必要がある。**

予測状態形成段階:

1. prediction-error stream
2. event cell
3. predictive candidate
4. prospective commitment
5. **event termination gate――今回退化解で反証**
6. commitment-specific future responsibility
7. sparse focus stack
8. goal revision state
9. free Japanese world state

## 他系列へ返す知見

- B: wrong bindingを抑えるだけのMDL gateは全候補棄却へ退化し得るため、positive derivation recallを同時評価する。
- C: Null-dominant eventを除外するだけでなく、identity classごとのpositive target responsibilityが必要。
- D: wrong endpointを消すgateとfast endpoint recallを同時評価し、全面棄却を成功としない。
- E: high-energy edge削除とpositive constraint-edge recallを同時に測る。

## 次の仮説

**Responsibility-Weighted Prospective Commitments by Counterfactual Prediction Removal**  
（反実仮想予測除去による責任重み付き前向きcommitment）

次は二値carry gateを廃止する。

1. 各commitment cellを一つずつ除去
2. 次turn `before / command` の予測誤差がどこで増えるか測定
3. 誤差増加区間をそのcellの予測責任として保持
4. 主語省略では責任がcommandの未説明部分へ向くcellだけ注入
5. 明示objectがあるturnでは新cellの責任が旧cellを上回れば切替
6. 複数objectは責任重み付きfocus stackとして同時保持
7. 計画変更では旧goal除去と新goal追加の誤差差を別々に測る
8. continuation recall、termination precision、observed-before accuracyを主評価化

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
