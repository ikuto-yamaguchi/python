# 系列B Cycle 025 研究報告

## 仮説

**Role-Exchange Binding Seeds from Cross-Episode Permutation Tests**  
（episode横断の役割交換検定からのbinding seed）

Cycle 024では、command・state change・future observationの三者交差により、明示的に再出現するobject/value区間を完全回収できた。しかしRename・主語省略ではobject seedが消失し、得られたものはsemantic bindingではなくsurface anchorだった。

今回は同一文字列の再出現を証拠にせず、異なるepisode間でobject候補だけ、またはvalue候補だけを交換した。交換後に以下が同時成立する候補contextだけを匿名role seedへ昇格した。

- 交換した因子だけが全観測viewで一貫して変化
- before→afterの非対象文字列を保存
- source→targetとtarget→sourceの逆交換で元の導出を復元
- 4回以上の交換support
- success率0.8以上、wrong率0.2以下
- role seed形成後だけ局所programを作成
- metadata込み総記述長がliteral符号より短い場合だけMDL libraryを保持

固定ontology、手書きslot、辞書、n-gram暗記、RAG、外部LLM、Transformerは使用していない。学習器はraw `before / command / after / future`だけを使用し、hidden object・field・valueは評価器だけで使用した。

## 先行研究整理

- Nominal anti-unificationはbindingを含む項の一般化において、atom集合の制約下で変数renaming・α同値まで一意な最小一般化を構成できる。ただし項構造とbinderは入力として与えられる。
- 2025年ICMLのNon-Asymptotic Length Generalizationはminimum-complexity interpolatorの有効性を示す一方、一般化可能性は仮説classの同値性判定可能性に依存する。MDLだけでは表現class外のbindingを生成しない。
- Compositional Generalization via Forced Rendering of Disentangled Latentsは、潜在因子が分離されていても出力空間で再結合を強制しなければ、superpositionによる暗記へ戻ることを示す。
- 2025年のTask Generalization with Autoregressive Compositional Structureは、操作が既知の合成構造を持つ場合の指数的task generalizationを示すが、操作・変数自体は事前定義される。

今回の課題は、それらより上流にある、生の日本語から交換可能なroleとbindingを生成する問題である。

## 最新PR・他系列との重複表

| 系列 | 最新中心 | 限定信号 | 支配的失敗 | Bとの分離 |
|---|---|---|---|---|
| A Cycle 025 | commitment終了event gate | wrong carry抑制 | carry率0の全面終了 | 予測責任・談話stateは扱わない |
| C Cycle 025 | 環境mechanism残差event identity | 評価監査 | 64 eventがNull支配で1 classへcollapse | 因果transition identityは扱わない |
| D Cycle 024 | 双方向query-state endpoint identity | wrong read抑制 | stable endpoint 0、全面棄権 | 長期memory endpointは扱わない |
| E Cycle 024 | 介入交換子によるfactor role | Null安全停止 | constraint edge不在、交換子0 | energy順序非可換性は扱わない |
| **B Cycle 025** | **導出viewのrole交換・逆導出・絶対MDL** | 今回検証 | role seedからprogram生成 | 系列固有 |

Eの交換子は介入順序差、Cのfactor swapはstate transition identityを中心とするため棄却した。Bは交換後の**可逆導出符号と総記述長**だけを中心機構・採否条件とした。

## 実験条件

- Seed: 1 / 7 / 19
- 学習episode: 48 / 144 / 288
- Test: 48例 / split / seed
- 条件: 既知、未知語順、未知語彙、Rename、別状態表現、入れ子、主語省略、複数段落
- Raw role候補: 約3037.67
- Role交換監査: 約47818
- Object/value role seed上限: 各32
- Program上限: 64
- Ablation: Surface recurrence / Role-exchange permutation / Role-exchange + absolute MDL

## 最大288例・3 seed平均

| 条件 | Surface accuracy / pair recall | Permutation accuracy / pair recall | MDL accuracy / pair recall |
|---|---:|---:|---:|
| 既知 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 未知語順 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 未知語彙 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| Rename | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 別状態表現 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 入れ子 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 主語省略 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

追加診断:

- Surface object/value seeds: 32 / 32
- Permutation object/value seeds: 32 / 32
- Permutation programs: 64
- Surface literal description: 209536 bits
- MDL library description: 44544 bits
- Permutation model: 10604 bytes
- MDL model: 10594 bytes

## 判定

**中核仮説は強く反証された。**

### Role seedは多数形成されたが能力は0

交換監査を通過したobject/value role seedは各32、programは64形成された。しかしPermutation方式は全splitでaccuracy・pair recallとも0、null率1.0だった。

つまり交換によって「このcontextの区間は置換しても観測viewが壊れにくい」という性質は検出できたが、その区間を新入力のobject/valueへ束縛し、state transitionを実行するcontextへ変換できなかった。

### 交換検定がsurface contextをroleと誤認

約47,818件の交換を監査したが、採用されたseedはobject・valueの意味roleではなく、局所文字contextの交換耐性だった。異なる文字列を複数viewへ一括置換すれば整合性と逆交換は自明に満たせる。

> **可逆な文字列交換は、可逆な変数束縛ではない。**

交換対象の区間が、state内のどの変数・relation・scopeへ作用するかを表すbinding graphがないため、role seedから実行可能programへ進めなかった。

### Surface方式もほぼ全面null

Cycle 024では候補recallだけを測ったため明示surface anchorが1.0だった。今回は候補から実際のafterを生成する統合testへ進めた結果、Surface方式も既知条件を含めaccuracy 0、null率0.9931だった。

これはCycle 024の高得点が実行可能program能力ではなく、候補包含率だったことを明確化した。

### MDLは記述長を短縮したが能力を追加しない

MDL符号長は約209,536 bitsから44,544 bitsへ短縮した。しかしaccuracy・pair recallは0のままである。

短くなったのは失敗するsurface context libraryであり、意味generalizationではない。MDL利得だけを採用条件にすると、**短いが実行不能な文法**を選ぶ。

### 未知形式・省略へ転移しない

未知語順、未知語彙、Rename、別状態表現、主語省略、複数段落の全てでpair recall 0だった。object identity、relation、scope、談話focus、操作は創発していない。

## 反証条件

仮説支持には最低でも以下が必要だった。

1. Role-exchange方式がSurface方式より既知実行accuracyを改善
2. Rename・主語省略でpair recallを0より増加
3. Wrong bindingを増やさずheld形式へ転移
4. Source→target／target→sourceの両方でstate transitionを再現
5. MDL短縮と能力改善を同時達成
6. 形成seedがhidden role別評価でsurface contextを超えて再利用

今回はMDL短縮だけを満たし、1〜4・6を満たさない。

## 探索爆発抑制

- Raw候補をepisodeあたりobject/value各12へ制限
- 交換occurrenceを各160件へ制限
- 交換support 4以上
- Success 0.8以上、wrong 0.2以下、inverse 0.8以上
- Role seed各32、program64
- MDL不利なlibraryは棄却

推定計算量:

- Candidate生成 `O(NL²)`
- Role交換audit `O(R²L)`
- Program library `O(OV)`
- 推論 `O(PL²)`
- `R≤160、O,V≤32、P≤64`

## 資源量

- Model: 10604 bytes
- 学習時間: 0.1868 sec
- 推論時間: 0.0237 ms/example
- Peak RSS: 111000 KiB前後（Python runtime込み）
- Candidate: 3037.67
- Permutation test: 47818

1GB未満・5ms未満は小規模制御条件で達成した。弱いスマートフォンCPU実機は未検証。

## 系列B固有の進展

> **候補包含率と実行可能program能力を分離した結果、Cycle 024のsurface anchor 1.0は構造創発ではないことが確定した。可逆交換とMDL短縮だけではvariable bindingにならず、交換結果をstate変数へ結ぶ実行graphが必要である。**

系列Bの段階:

1. Raw clause proposal
2. Local execution
3. Failure quotient
4. Filler nonterminal
5. Context abstraction
6. Three-way surface anchor
7. **Role exchange and inverse derivation――今回反証**
8. Executable binding graph
9. Hierarchical MDL consolidation

## 他系列へ返す知見

- A: commitment候補を除去・交換して予測が保たれても、談話object bindingの証拠にはならない。positive responsibilityを実際の次turn生成で測る。
- C: factor swapの残差signatureだけでevent identityを作らず、交換後transitionの実行成功を必須化する。
- D: endpoint区間の双方向再構成だけでなく、そのendpointを用いたread/write実行を同時評価する。
- E: constraint edge候補の介入順序差だけでなく、edge経由で正しいstate更新が起きることを要求する。

## 次の仮説

**Executable Binding Graphs from Role-Exchange Consequence Factorization**  
（役割交換consequenceの因子分解からの実行可能binding graph）

次はcontext seedを直接program化しない。

1. Object候補・value候補・state change候補を三部graphとして保持
2. Objectだけ交換した結果、state内のobject endpointだけが変わるedgeを生成
3. Valueだけ交換した結果、change endpointだけが変わるedgeを生成
4. Non-target保存を独立edgeにする
5. Forward実行とinverse reconstructionの双方で成功した三角形だけbinding graph化
6. Graphを用いてheld/Rename/省略のafterを実際に生成
7. Graph metadata込みMDLとliteral符号を比較
8. Candidate recallではなくexecution accuracy・wrong binding・open-form coverageを主評価化

系列Cの因果transition identityとは異なり、Bは**導出graphの可逆符号化・再利用・総記述長**を中心にする。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
