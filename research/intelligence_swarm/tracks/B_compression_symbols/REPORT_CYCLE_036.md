# 系列B Cycle 036 研究報告

## 仮説

**Trace-Bisimulation Quotient Grammar from Minimal Multi-Intervention Diagrams**  
（最小複数介入diagramのtrace双模倣商文法）

Cycle 035ではstate変更区間・command value区間・command object区間を共同productionへ格納し、単一value swapへの共変性で匿名class化したが、execution accuracyは0だった。

系列C Cycle 035が介入順序交換子を因果方向の観点から既に検証しているため、交換子の成立自体は本系列の成果候補から棄却した。今回は系列B固有の問いとして、value swap・object swap・語順摂動・二つのswap順序が作る**複数介入traceの観測同値類**を商classへ圧縮したとき、単一swap classより短い記述で実行性能を維持または改善できるかを検証した。

Final testの`after / future`は候補生成・rankingに使用していない。

## 最新系列との重複表

| 系列 | 最新中心 | Bで成果対象にしない領域 |
|---|---|---|
| A | 複数sensor予測誤差によるstate birth | 時間予測状態・再帰更新 |
| C | 二重介入交換子による因果方向・object選択 | 因果world transition |
| D | 双方向replay残差からのmemory address birth | 長期memory・read/write閉路 |
| E | Hyperedge frustration gradientによるnode birth | Energy固定点・局所力学 |
| **B** | **複数介入traceを同値類へ商化する匿名grammarと共同MDL** | 今回の固有対象 |

## 実装

- 固定ontology、手書きslot、辞書圧縮、RAG、外部LLMなし
- Induction: 72例
- Independent probe: 36例
- Final test: 別seed 30例 × 8条件
- Production候補:
  - state変更区間の相対bucket
  - command value区間の相対bucket
  - command object区間の相対bucket
  - old/new/object文字shape
- 介入trace:
  1. Identity execution
  2. Value swap
  3. Object swap
  4. 語順摂動
  5. Value→Object と Object→Value の順序比較
  6. Non-target preservation
- 同一trace histogramを持つproductionを匿名quotient class化
- Factorized / Single-swap / Trace quotient / Quotient+MDL / Shuffled outcomeを比較

## 3 seed平均

| 条件 | Factorized 精度/wrong | Single 精度/wrong | Quotient 精度/wrong | Shuffle 精度/wrong |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 0.7444 | 0.0000 / 0.4556 | 0.0000 / 0.4556 | 0.0000 / 0.6222 |
| 未知語順 | 0.0000 / 0.7444 | 0.0000 / 0.4556 | 0.0000 / 0.4556 | 0.0000 / 0.6222 |
| 未知語彙 | 0.0000 / 0.7444 | 0.0000 / 0.4556 | 0.0000 / 0.4556 | 0.0000 / 0.6222 |
| Rename | 0.0000 / 0.5333 | 0.0000 / 0.4444 | 0.0000 / 0.4444 | 0.0000 / 0.4333 |
| 別状態表現 | 0.0000 / 0.3333 | 0.0000 / 0.3333 | 0.0000 / 0.3333 | 0.0000 / 0.2111 |
| 入れ子 | 0.0000 / 0.7444 | 0.0000 / 0.4556 | 0.0000 / 0.4556 | 0.0000 / 0.6222 |
| 主語省略 | 0.0667 / 0.4667 | 0.0000 / 0.3333 | 0.0000 / 0.3333 | 0.0667 / 0.4667 |
| 複数段落 | 0.0000 / 0.7444 | 0.0000 / 0.4556 | 0.0000 / 0.4556 | 0.0000 / 0.6222 |

追加診断:

- Production symbol: **15.00**
- Quotient class: **5.67**
- Probe trace audit: **540**
- 既知pair recall: **0.1556**
- 平均候補数: **2.63**
- Quotient description: **2099 bits**
- モデルサイズ: **2072 bytes**
- 学習時間: **0.004175 sec**
- 既知推論: **0.025232 ms/example**
- 複数段落推論: **0.024985 ms/example**
- Peak RSS: **111480 KiB**（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Quotient classは形成された

複数介入traceの応答histogramから平均5.67個の匿名quotient classを形成できた。記述長は約2099 bitsで、episode文字列をそのまま保持するより大幅に短い。

### Single-swapと能力が完全同一

全8条件でSingle方式とQuotient方式のaccuracy、wrong commit、pair recall、候補数が完全に同一だった。

Trace quotientは既存productionの順位を一件も変えず、単一swap classを超える追加識別情報を与えなかった。

> **複数介入traceを商化できることと、semantic variable・operationを形成できることは同じではない。**

### Execution accuracyは0

全主要条件でaccuracyは0だった。既知条件ではpair recall 0.1556を維持したが、正しいafterへ接続しない。

候補内にobject/value文字列が存在しても、次が形成されていない。

- 正しいstate target
- Relation
- Operation
- Scope
- Goal
- Constraint

### Correct outcome固有の能力差なし

Shuffled outcomeではwrong/null比率が変化したが、accuracyはCorrect quotientと同じ0だった。

したがって正しい独立観測が、一般化可能な商文法を形成した証拠とは認めない。

### MDL採用条件は未達

Quotient grammarは短いが予測性能0である。説明長を短縮しただけのsurface transformation classであり、意味記号・階層文法・program inductionの成立ではない。

## 反証条件

仮説支持には最低限、次が必要だった。

1. Trace quotientがSingle-swapよりexecution accuracyを改善
2. Correct traceとshuffleでaccuracy差が生じる
3. Rename・別状態表現・語順変更へclassが転移
4. Pair recallとexecution accuracyが同時に増加
5. Quotient metadataの追加bitsを性能利得で回収

すべて未達。

## 探索爆発抑制・資源量

- Production induction: `O(NL)`
- Multi-intervention trace: `O(QPI)`
- Quotient partition: `O(P log P)`
- Inference: `O(PL)`
- `P≤48`
- 候補出力上限64

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列B固有の進展

> **単一swap応答を複数介入traceの観測同値類へ拡張しても、同値類がsurface-local productionから作られている限り、追加圧縮はsemantic bindingや実行能力へ接続しない。**

## 他系列へ返す知見

- A: 複数sensor traceが同値でも、境界候補がsurface-localなら時間状態identityにはならない。
- C: 介入交換子の成立・商class化は因果方向やstate variableの十分条件ではない。
- D: Read/write trace同値類をslow化する前に、closed-cycle executionの能力増分が必要。
- E: 複数介入pathの同一energy応答だけではsemantic constraint topologyにならない。

## 次の仮説

**Residual-Generating Quotient Productions from Counterexample Trace Splits**  
（反例trace分割からの残差生成型商production）

次は既存productionを同値類へまとめるだけにしない。

1. 同一quotient class内でcorrect/wrongが分岐するprobeを抽出
2. 分岐traceの最小差をstate/value/object境界へ逆写像
3. Boundary shift・split・argument relinkから新productionを生成
4. 複数probeで同じtrace分割を説明するproductionだけ保持
5. Correct trace／shuffled trace／class-only／birthなしを比較
6. Production bits＋trace-class bits＋residual errorの共同MDLを評価
7. Pair recall・execution accuracy・candidate entropyを同時評価
8. Rename・別状態表現・主語省略で新productionの転移を監査

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
