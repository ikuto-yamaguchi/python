# 系列B Cycle 040

## 仮説

**Role-Permutation Quotient Grammar from Multi-World Co-Segmentation**  
（複数world共同分節による役割置換商文法）

Cycle 039では、元episodeと一つのpaired worldを共同分節しても、factorized方式から候補topologyが変化せず、短文で約1.1万、複数段落で約2.3万候補へ爆発した。

今回はobjectだけ、valueだけ、語順だけが変化する3種類のworldを同時に生成し、一つのlatent proposalから次を匿名roleとして共同抽出した。

- Command内でobject介入に反応する区間
- Command内でvalue介入に反応する区間
- Before→afterで変化するstate区間
- Object/value swap後もrole対応が保存されるか
- 語順変更後もpayload対応が可換か

文字列identityや文字shapeをquotient identityから外し、role幅・role順序・可換性だけで匿名grammarへ商化した。さらにgrammar記述bits、residual error、候補entropy proxyを含むMDLで採否した。Final testのafter/futureは候補生成・rankingに使用していない。

## 先行研究整理

近年のprogram synthesisは、探索空間をgrammarで制約したり、反例で候補空間を精錬したりすることで計算量を抑える。しかし一般に、DSL、component、formal specification、interpreter、評価oracleのいずれかが先に与えられる。

- 2025年のiterative program synthesisは、online knowledgeとencapsulation grammarでprogram空間を精錬する。
- 2024年のSynanticは、与えられたgrammarと実行interpreterからformal semanticsをCEGISで合成する。
- Directed lemma synthesisは、形式化済みprogram equivalence問題で補助lemmaを生成して探索を効率化する。

今回の問題はそれらより上流であり、生の日本語からgrammar primitive、variable role、operation target自体を生成する必要がある。

## 重複表

| 系列 | 最新中心 | Bで扱わない領域 |
|---|---|---|
| A | Microstate寿命と遅延event boundary | 時間状態・再帰更新 |
| C | Multi-world intervention closure event | 因果event・world transition |
| D | Paired replay fingerprint再固定化 | 長期memory・read/write閉路 |
| E | Constraint homotopy attractor tracking | Energy固定点・局所緩和 |
| **B** | **Role permutationの匿名商grammar化とentropy込みMDL** | 今回の固有対象 |

C Cycle 039はobject/value/operationを一つのevent familyへ格納して介入閉包を評価した。今回の系列Bではeventの因果性を成果対象にせず、異なるworld間で同じ匿名role permutationを短く符号化し、候補entropyを実際に減らせるかだけを中心評価とした。

## 最小実装

比較方式:

1. **Pair**: state区間とcommand value区間の二視点対応
2. **Multi-world**: object/value/orderの三world共同分節
3. **Role quotient**: 絶対位置を除きrole幅・順序・可換性で商化
4. **MDL**: grammar bits + residual error + entropy proxyで採用
5. **Shuffle**: object/value world対応を交換した対照

固定ontology、辞書、手書きslot、分類器、RAG、外部LLMは使用していない。Object/valueという名称は評価時のground truthにのみ使い、モデル内部では介入応答で区別された匿名`r0/r1/r2`として扱った。

## 3 seed平均

| 条件 | Pair候補 | Multi-world候補 | Quotient候補 | MDL候補 | MDL entropy bits | MDL精度 |
|---|---:|---:|---:|---:|---:|---:|
| 既知 | 4632.2 | 1521.1 | 1681.3 | 280.6 | 8.13 | 0.0000 |
| 未知語順 | 3922.7 | 1253.7 | 1253.7 | 124.8 | 5.81 | 0.0000 |
| 未知語彙 | 4818.9 | 1564.5 | 1564.5 | 257.1 | 8.01 | 0.0000 |
| Rename | 5534.1 | 1636.9 | 1811.7 | 299.3 | 8.22 | 0.0000 |
| 別状態表現 | 733.5 | 441.5 | 489.7 | 79.2 | 6.30 | 0.0000 |
| 入れ子 | 2305.8 | 1235.9 | 1235.9 | 172.2 | 7.39 | 0.0000 |
| 主語省略 | 4499.5 | 0.0 | 0.0 | 0.0 | 0.00 | 0.0000 |
| 複数段落 | 6103.5 | 2268.4 | 2268.4 | 365.6 | 8.51 | 0.0000 |

追加診断:

- Pair grammar: 25.00
- Multi-world grammar: 15.00
- Role quotient grammar: 12.67
- MDL grammar: **1.33**
- Shuffle grammar: 29.33
- Quotient description: 2969.4 bits
- MDL description: **314.7 bits**
- MDL model: **76 bytes**
- Training: 0.002738 sec
- Inference: 既知 0.567 ms / 複数段落 1.206 ms
- Peak RSS: 159872 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Multi-world共同分節は候補数を減らした

既知条件ではPair方式の候補数4632.2に対し、Multi-worldは1521.1、Role quotientは1681.3となった。Cycle 039の約1.1万候補からも大幅に減っている。

したがって、object/value/orderを別worldで変化させ、その応答を共同監査することは、単一paired worldより強い候補空間制約として働いた。

### MDLは候補entropyをさらに圧縮

MDL方式は平均grammarを1.33個まで削減し、既知候補を280.6、複数段落候補を365.6まで減らした。

- 既知entropy: 8.13 bits
- 複数段落entropy: 8.51 bits
- Model: 76 bytes

探索爆発はCycle 039より約40分の1へ縮小した。

### しかしexecution accuracyは全条件0

Pair、Multi-world、Role quotient、MDL、Shuffleの全方式・全条件でexecution accuracyは0、null率1.0だった。

MDLは正しいprogramを選んだのではなく、数百個残る同点候補の生成grammarを極小化しただけである。

> **役割置換の可換性と短い匿名符号は、semantic variable productionの十分条件ではない。**

### Exact state boundaryとvalue bindingも0

MDL方式では全条件で、

- Exact state boundary recall: 0
- Value recall: 0
- Rename転移: 0
- 別状態表現転移: 0
- 主語省略: 候補0

だった。

匿名roleは「どの介入で区間が変化したか」を示すだけで、以下を束縛していない。

- Object identity
- State relation
- Operation
- Scope
- Goal
- Constraint
- 談話focus

### Shuffleとの差は能力へ接続しない

Shuffled alignmentではgrammar数と候補entropyが増えたため、correct multi-world対応が圧縮に有効なことは確認できた。

しかしcorrect方式もshuffle方式もaccuracy 0である。正しいworld対応へ依存する圧縮信号が存在することと、意味programが形成されたことは別である。

## 反証条件

| 条件 | 結果 |
|---|---|
| Multi-worldがpair-onlyより候補entropyを削減 | 達成 |
| Role quotientが文字列・絶対位置なしで形成 | 達成 |
| Correct alignmentがshuffleより短いgrammar | 達成 |
| Exact state/value boundary recall > 0 | 未達 |
| Execution accuracy > 0 | 未達 |
| Rename・別状態表現へ転移 | 未達 |
| 主語省略で前turn role再起動 | 未達 |
| 追加grammar bitsを予測利得で回収 | 未達 |

## 既存方式との差

既成DSLのproductionを探索したのではない。入力ごとに介入worldを比較し、変化区間から匿名role候補を生成した。またn-gramや辞書圧縮ではなく、object/value/order介入に対する可換diagramをgrammar identityに用いた。

ただし現在のroleは区間幅と相対順序に依存するsurface roleであり、意味変数、関係、階層programには到達していない。

## 資源量・探索爆発抑制

- Multi-world共同分節: `O(NL)`
- Quotient partition: `O(P log P)`
- 推論: `O(GL²V)`
- Grammar上限: 48
- Local span長: 12

1GB未満は達成した。MDL方式は既知・複数段落とも5ms未満である。

ただし弱いスマートフォンCPU実機は未検証であり、76 bytesという小ささは知能構造の圧縮ではなくgrammarの過剰剪定による。

## 系列B固有の進展

> **複数worldのrole permutationを商化し、candidate entropyをCycle 039比で大幅に削減できた。しかし匿名roleが介入応答と区間順序だけで定義される限り、state target・value・operationを束縛せず、MDLは短い全面棄権grammarを選ぶ。**

## 他系列へ返す知見

- A: Event boundary後のstate rebirthでも、役割候補のentropy削減だけではstate identityにならない。境界後予測との共同bindingが必要。
- C: Multi-world event familyはtuple共同格納ではなく、各roleを除去したとき対応rolloutだけが崩れる因果必要性を要求すべき。
- D: Replay compression errorからtraceを生成する際、短いtraceがread/write閉路を改善しない場合はMDL採用しない。
- E: Residual eigenmodeでconstraint fieldを作る際、active集合削減だけでなくcorrect boundary・execution利得を採用条件に含めるべき。

## 次の仮説

**Deletion-Causal Role Grammar from Minimal Predictive Sufficiency Sets**  
（最小予測十分集合による削除因果型role grammar）

次はrole permutationの可換性だけを証拠にしない。

1. Multi-world共同分節で匿名role候補を生成
2. 各role nodeを一つずつ削除
3. Object-role削除でtarget選択だけが崩れるか監査
4. Value-role削除でpayload共変だけが崩れるか監査
5. State-role削除でrolloutのみが崩れるか監査
6. 最小predictive sufficiency setだけをproduction化
7. Correct deletion／shuffled role／no-deletion／MDL-onlyを比較
8. Grammar bits + lesion-specific prediction loss + candidate entropyを共同最小化
9. Rename・別状態表現・主語省略への転移を必須化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
