# 系列E Cycle 031 研究報告

## 仮説

**Counterexample-Driven Boundary Expansion from Near-Miss Probe Residuals**  
（near-miss probe残差による反例駆動境界拡張）

Cycle 030では独立probeによる境界nudgeを試したが、正しい候補が候補集合に存在せず、discrimination・local updateは0だった。本Cycleではprobeを候補選択だけでなく候補生成へ戻し、probe候補afterと観測afterの最小差分から、target/value境界のexpand・contract・shift量を局所repair operatorとして学習した。

Final test outcomeはcandidate生成・rankingに使用していない。Probe outcomeは、候補生成後のnear-miss residualとlocal repair ruleの学習にのみ使用した。

## 先行研究整理

- Equilibrium Propagationはfree/nudged phaseの局所差から学習するが、状態変数とenergy topologyが既に存在する（Scellier & Bengio, 2017）。
- finite-nudge EPは有限摂動でも局所energy差から厳密な勾配を得られる可能性を示す（arXiv:2511.22024）。
- Augmented Lagrangian Predictive Codingは局所constraint errorを双対変数へ蓄積し、深い系でcredit伝播を改善する（arXiv:2605.31022）。
- ALOEは離散構造上の局所探索samplerを学習するが、探索対象の構造表現は事前定義される。

本Cycleの固有課題は、定義済みnodeを学習することではなく、生の日本語から境界nodeと局所生成操作そのものを作ることである。

## 他4系列との重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A | probe駆動transition-kernel可塑性 | 談話予測状態・時間誤差相殺 |
| B | probe駆動symbol boundary repair | MDL・program symbol class |
| C | minimal intervention supportによるmechanism family | 因果world transition |
| D | consequence-preserving read/write topology rewiring | 長期memory・再固定化 |
| **E** | **near-miss制約違反が境界energy地形とcandidate birthを変える局所力学** | 今回の固有対象 |

Bもprobe差分によるboundary repairを次仮説としているため、系列Eではsymbol production ruleやMDLを扱わず、repair operatorがfree-phase候補集合・energy gap・固定点・局所更新を変えるかに限定した。

## 実装

- 固定ontology、手書きslot、辞書、分類器、RAG、外部LLMなし
- Induction / independent probe / final testを分離
- Free phase:
  - `before`内target境界候補
  - `command`内value境界候補
  - 最大96候補
- Nudged training phase:
  - probe candidate afterと観測afterの編集距離を計測
  - 最小near-miss候補を選択
  - target/valueの開始・終了境界deltaを抽出
  - 複数probeで2回以上再現するdeltaだけrepair operator化
- Final inference:
  - raw候補にrepair operatorを適用して最大128候補へ拡張
  - energy最小値+0.08以内へactive集合を単調縮小
  - gap<0.10ならnull
  - 最大6 sweep

## 3 seed平均

| 条件 | Residualなし | Correct residual | Shuffle residual | Wrong commit | 最小境界距離 |
|---|---:|---:|---:|---:|---:|
| 既知 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 10.54 |
| 未知語 | 0.0000 | 0.1250 | 0.0000 | 0.0417 | 0.43 |
| 曖昧性 | 0.0000 | 0.0000 | 0.0000 | 0.2778 | 12.31 |
| 入れ子 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 12.69 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 11.69 |
| 複数段落 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 13.56 |
| 計画変更 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 16.03 |
| 反実仮想 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 15.69 |

追加診断:

- Probe audit: 3456
- Near-miss: 36
- Repair update: 36
- Repair context: 6.33
- Repair rule: 8.33
- Shuffle repair rule: 0.00
- モデルサイズ: 42421 bytes
- 学習時間: 0.982 sec
- 既知推論: 10.44 ms/example
- 複数段落推論: 12.20 ms/example
- Peak RSS: 113048 KiB（Python runtime込み）

## 判定

**一般的な境界創発・言語理解仮説としては強く反証。未知語条件の境界近接化に限定信号があるが、正しい意味境界・安定した制約充足には未到達。**

### Correct residualで局所repair ruleは形成

Correct probeでは平均8.33件のrepair ruleが形成され、shuffleでは0件だった。Probe outcomeの正しい対応関係が、単なる候補順序ではなく境界生成操作へ影響したことは確認できた。

### 未知語で境界距離が大幅低下

未知語条件の平均最小境界距離は、12.97から0.43へ低下した。Accuracyは0から0.125へ上昇し、shuffleでは0のままだった。

これはnear-miss残差が、候補選択だけでなく候補birthを正しい境界近傍へ移動させ得る初めての系列E信号である。

### ただしexact pair recallは0

全条件でexact object-value pair recallは0だった。未知語でexact-afterが生成された例も、内部target/value境界が評価上の真のobject/value spanと一致していない。

> **After文字列を正しく生成できても、対象・値・関係・操作の意味境界が形成されたとは限らない。**

### 曖昧性では誤attractorを増加

曖昧性条件ではaccuracy 0のままwrong commitが0.2778へ増えた。Repair operatorが候補を非空・非平坦にした一方、複数対象のscopeを区別せず、誤った安定点を強化した。

### 既知・入れ子・主語省略・長文・計画変更・反実仮想

- 既知: 境界距離は12.69→10.54へ小改善するがaccuracy 0
- 入れ子: repair ruleが適用されず0
- 主語省略: object permanenceがなく0
- 複数段落: 長距離scopeを扱えず0
- 計画変更: 撤回案と最終案を分離できず0
- 反実仮想: 実行/非実行worldを分離できず0

### 失敗分類

- **Boundary-near-miss improvement**: 未知語で境界距離低下
- **Semantic boundary collapse**: exact pair recall 0
- **Scope collapse**: 曖昧性でwrong attractor増加
- **Transfer collapse**: 入れ子・長文・計画変更・反実仮想0
- **Flat landscape**: 多くの条件でnull tie
- **Local-minimum error**: 曖昧性で誤固定点
- **発散**: active集合単調縮小、最大2 sweep実測で未観測

## Hopfield記憶・既存NNとの差

固定patternの想起ではなく、入力ごとに境界候補を生成し、probe残差から局所境界操作を学習し、候補集合そのものを変形してenergy固定点を探索する。単純なHopfield記憶とは異なる。

一方、現在は手続き的文字列置換と粗いcontext signatureであり、正式な平衡伝播、意味constraint graph、連続energy networkには未到達。

## 収束保証・停止条件

各sweepでactive候補をenergy閾値内の部分集合へ単調縮小し、最大6 sweepとするため有限停止する。実測平均・最大は全条件2 sweep。

## 資源量・計算量

- Candidate生成: `O(L^4)`を96候補へ疎制限
- Near-miss edit distance: `O(QHL^2)`
- Repair expansion: `O(HR)`
- Relaxation: `O(SH)`
- `Q=36, H≤128, R≤3/context, S≤6`

1GB未満は達成。推論10〜13ms/exampleで5ms未満と弱いスマートフォンCPU実機条件は未達。

## 系列E固有の進展

> **Independent probeのnear-miss残差を候補生成操作へ戻すと、正しい境界近傍への探索距離を下げられる。しかし粗いcontext別deltaはsemantic roleやscopeを持たず、曖昧性では誤attractorを強化する。**

## 他系列へ返す知見

- A: probe creditをscoreではなくoperator topologyへ作用させる方向は有効だが、scope条件なしでは誤状態を強化する。
- B: boundary repairはcandidate birthを改善し得るが、exact pair recallとMDLを同時に評価しないと広い置換区間で見かけのexecutionが出る。
- C: minimal intervention supportは必須。正しいafterだけではstate-variable境界を保証しない。
- D: read/write topology rewiringでも、曖昧なaddressを分離するnegative scope constraintが必要。

## 次の仮説

**Scope-Gated Boundary Repair Attractors from Competing Counterexample Residuals**  
（競合反例残差によるscope-gated境界修復アトラクタ）

1. 単一near-missだけでなく上位k候補の競合残差を保持
2. 同じrepairで複数候補が正しくなる場合はscope不明として保留
3. Object候補除去・value候補除去・段落除去の反実仮想残差を別channel化
4. Correct候補だけ改善し競合候補を悪化させるrepairへ正の局所force
5. 曖昧性でwrong commitを増やすrepairをnegative constraint化
6. Minimal intervention supportまでtarget/value境界をcontract
7. Correct residual / shuffled residual / no residual / no scope gateを比較
8. Exact pair recall・boundary distance・accuracy・wrong attractorを同時評価
9. 主語省略・計画変更・反実仮想ではscope stateを複数固定点として保持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
