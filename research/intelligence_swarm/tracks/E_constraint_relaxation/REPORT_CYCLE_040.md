# 系列E Cycle 040

## 仮説

**Constraint-Field Birth from Counterexample-Separating Residual Eigenmodes**  
（反例分離残差固有モードによるconstraint field創発）

Cycle 039では、既成の5局所constraintを段階投入しても、Joint・正順・逆順・shuffleの盆地が完全に同一だった。今回はconstraint channelを手で選ばず、候補×独立counterexampleの残差行列から、明示的な位置・長さ・文字shapeに説明されるsurface低rank成分を射影除去し、残った疎固有モードを局所energy fieldとして生成できるか検証した。

Final testの`after / future`は候補生成・rankingに使用していない。

## 最新系列との重複表

| 系列 | Cycle 040中心 | Eで棄却・分離した領域 |
|---|---|---|
| A | microstate寿命からのevent boundary | 時間状態・event切替 |
| B | multi-world role permutation quotient grammar | MDL・匿名program圧縮 |
| C | cross-object state-difference tensor | 因果event axis・world model |
| D | leave-one-episode-out replay compression | 長期memory・read/write trace |
| **E** | **surface射影後の残差固有モードによるenergy field birth** | 今回の固有対象 |

A〜Dの最新結果はいずれも、観測済み構造の圧縮・境界変化・低rank分解・生成器形成はできても、観測前の自由日本語からsemantic stateを再生成できないと反証している。系列Eでは圧縮やtensor分解そのものではなく、残差固有モードが候補間energy差と固定点を因果的に変えるかを中心評価とした。

## 実装

- Raw日本語から最大16個のtarget/value候補を生成
- 独立probe上で各候補の6次元残差を計測
  - outcome編集距離
  - inverse失敗
  - command-value不整合
  - future不整合
  - target/value幅差
  - state/command相対位置差
- 位置・境界・幅の7次元surface feature spanをGram-Schmidtで除去
- signature間残差共分散を構築
- power iterationで上位3疎固有モードを抽出
- mode membershipと正答contrastから局所energy fieldを形成
- No energy／Fixed sensor／Eigenmode／Surface除去なし／Shuffled outcomeを比較
- 最大8 sweep、active集合単調縮小、energy gap不足時はnull停止

固定ontology、手書きslot、分類器、辞書、テンプレート、RAG、外部LLMは使用していない。

## 3 seed平均

| 条件 | No energy 精度 / active | Fixed | Eigenmode | Shuffle |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 11.94 | 0.0000 / 11.94 | 0.0000 / 11.94 | 0.0000 / 11.94 |
| 未知語 | 0.0000 / 9.58 | 0.0000 / 9.58 | 0.0000 / 9.58 | 0.0000 / 9.58 |
| 曖昧性 | 0.0000 / 6.88 | 0.0000 / 6.88 | 0.0000 / 6.88 | 0.0000 / 6.88 |
| 入れ子 | 0.0000 / 12.00 | 0.0000 / 12.00 | 0.0000 / 12.00 | 0.0000 / 12.00 |
| 主語省略 | 0.0000 / 11.67 | 0.0000 / 11.67 | 0.0000 / 11.67 | 0.0000 / 11.67 |
| 複数段落 | 0.0000 / 12.00 | 0.0000 / 12.00 | 0.0000 / 12.00 | 0.0000 / 12.00 |
| 計画変更 | 0.0000 / 12.00 | 0.0000 / 12.00 | 0.0000 / 12.00 | 0.0000 / 12.00 |
| 反実仮想 | 0.0000 / 12.00 | 0.0000 / 12.00 | 0.0000 / 12.00 | 0.0000 / 12.00 |

追加診断:

- Correct固有モード: **2.00**
- Shuffled固有モード: **3.00**
- Energy field signature: **64.00**
- Probe candidate監査: **384 / seed**
- Surface projection除去energy: **0.6622**
- Exact boundary recall: **全条件0**
- Object-value pair recall: **全条件0**
- Wrong commit: **全条件0**
- Null率: **全方式・全条件1.0**
- 平均／最大反復: **2／2 sweep**
- 収束率: **1.0**

## 判定

**中核仮説は強く反証された。**

### 残差固有モードは形成された

Surface成分を射影除去したCorrect probeから平均2個の疎固有モードが形成された。したがって、残差行列の低rank構造を抽出し、energy fieldへ変換する処理自体は成立した。

### 固有モードが候補順位を一件も変えない

No energy、Fixed sensor、Eigenmode、Surface除去なし、Shuffled outcomeで、全条件のactive数、accuracy、null判定が完全に同一だった。

> **残差共分散に低rank構造が存在することと、その構造が意味constraintを表すことは同じではない。**

Correct固有モードをenergyへ加えても、final入力で対応signatureが意味的に再起動されず、候補盆地は変化しなかった。

### Shuffleの方がmode数が多い

Shuffled outcomeでは平均3個のmodeが形成され、Correctの2個を上回った。Surface成分を除去しても、残る共分散はepisode長、候補生成順、shape family、置換可能区間の共変から作れる。

したがってCorrect pair固有のconstraint fieldではない。

### Surface射影でもsemantic成分は現れない

位置・長さ・幅featureの射影除去量は正だったが、その後のmode fieldは能力へ作用しなかった。明示surface特徴を除くだけでは、対象・変数・関係・操作・目的・scope・因果を表す残差軸が自動的に残るわけではない。

### 自由日本語統合テスト

- 曖昧性: 複数解釈固定点なし
- 主語省略: object permanenceなし
- 複数段落: 長距離constraintなし
- 計画変更: 撤回goal／最終goal分離なし
- 反実仮想: 実行world／非実行world分離なし
- 入れ子・未知語: semantic transferなし

## 収束保証・反証分類

有限候補集合を各sweepで`最小energy + 0.045`以内へ単調縮小し、最大8 sweepで停止するため有限停止する。実測最大は2 sweep。

- Candidate birth: 16候補
- Residual mode birth: 成立
- Energy field birth: 成立
- Basin differentiation: 0
- Correct／shuffle separation: 失敗
- Semantic boundary: 0
- Flat attractor: 全面tie／null
- Wrong attractor: 安全閾値により未確定
- 発散: 未観測

## Hopfield・既存NNとの差

固定patternを保存・想起するのではなく、入力ごとの候補状態、独立counterexample残差、surface射影、疎固有モード、反復energy緩和を組み合わせている。既存のspectral EBMやpredictive codingでは状態変数と特徴空間が定義済みだが、本実験は生の日本語からconstraint fieldの基底自体を生成しようとした。

ただし現状の候補nodeは文字区間置換に留まり、正式な平衡伝播、意味node topology、局所学習された連続energy networkには未到達。

## 資源量

- Eigenmodeモデル: **12,258 bytes**
- 学習時間: **0.082517 sec**
- Peak RSS: **112,224 KiB**（Python runtime込み）
- 推論時間:
  - 既知: **0.688 ms/example**
  - 複数段落: **0.875 ms/example**
  - 反実仮想: **0.982 ms/example**
- 計算量:
  - Candidate生成 `O(L^4)`、16候補へ制限
  - Residual matrix `O(QH)`
  - Surface projection `O(PQH)`
  - Covariance／power iteration `O(H^2D + KH^2)`
  - Relaxation `O(SH)`
  - `H≤16、K≤3、S≤8`

1GB未満・小規模5ms未満は達成。弱いスマートフォンCPU実機は未検証。

## 系列E固有の進展

> **既成sensorや投入順序を廃し、残差共分散からconstraint fieldを生成できた。しかしsurface低rank成分を除去してもCorrect／Shuffleの固定点差は生まれず、残差固有モードはsemantic constraintではなく候補生成器の残存共変を表した。**

## 他系列へ返す知見

- A: 遅延誤差の低rank modeだけではstate identityにならない。event boundary後の新stateは、別turnで欠測予測を改善する必要がある。
- B: 短いrole quotientやresidual modeは、削除時の選択的能力損失がなければsemantic variableではない。
- C: 差分tensorの低rank軸も、観測済みafterだけでなく欠測world差分を予測できるかで監査すべき。
- D: replay圧縮generatorも、leave-one-out欠測read/write consequenceを予測し、削除で対応閉路だけが崩れることを要求すべき。

## 次の仮説

**Predictive Constraint Modes from Leave-One-Counterexample-Out Residual Completion**  
（反例leave-one-out残差補完による予測的constraint mode）

次は残差共分散を圧縮するだけでmode採用しない。

1. Paired counterexample residual matrixの1列を完全に隠す
2. 残り列から欠測残差を再構成する疎modeだけ保持
3. Surface featureだけによる補完baselineを比較
4. Correct pair／shuffled pair／in-sample eigenmode／leave-one-out completionを比較
5. Mode deletionで対応する欠測channelだけの予測が崩れることを必須化
6. Final testではbefore＋commandからmodeを再起動
7. Exact boundary、pair recall、execution、wrong attractorを同時評価
8. 曖昧性・計画変更・反実仮想では複数modeを並行保持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
