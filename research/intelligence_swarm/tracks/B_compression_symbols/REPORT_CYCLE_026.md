# 系列B Cycle 026 研究報告

## 仮説

**Executable Binding Graphs from Role-Exchange Consequence Factorization**  
（役割交換consequenceの因子分解からの実行可能binding graph）

Cycle 025では可逆な文字列交換からrole seedと短いMDL libraryを形成したが、全splitでexecution accuracyが0だった。今回はraw `before / command / after / future`から、object node・value node・state-change endpointを生成し、forward after生成、inverse before復元、non-target保存を満たす三角形だけをbinding graphへ採用した。

## 先行研究整理

- ICLR 2025のSR4MDLはdescription lengthをsymbolic regressionの探索目標にして式回収を改善したが、式文法と数値入出力空間は定義済み。
  - https://proceedings.iclr.cc/paper_files/paper/2025/hash/a402493de088886740b5939f666a6e56-Abstract-Conference.html
- NeurIPS 2025のProgram Synthesis via Test-Time Transductionは有限program hypothesis classをtest inputで絞るが、program候補classと外部LLMを前提にする。
  - https://proceedings.neurips.cc/paper_files/paper/2025/hash/35678513540026a9e3bf0d49d7e6f624-Abstract-Conference.html
- COLT 2025のtwo-part-code MDL解析はdescription penalty次第でunder/over-regularizationが起こることを示し、短さ単独を能力証拠にできない。
  - https://proceedings.mlr.press/v291/zhu25a.html
- TheoryCoder-2は経験からabstractionを学んでplanningへ使うが、LLMと既存program-synthesis agentを利用する。
  - https://arxiv.org/abs/2602.00929

## 他系列との重複表

| 系列 | 最新中心 | 支配的失敗 | Bとの分離 |
|---|---|---|---|
| A | 局所残差routingによるpredictive responsibility | commitment責任が負 | 予測状態・談話責任は扱わない |
| C | Multi-witness state-variable fiber | success event間identity class 0 | 因果mechanism identityは扱わない |
| D | Memory要素除去によるcredit isolation | 誤factorをslow固定 | 長期memory再固定化は扱わない |
| E | Residual-mediator constraint hyperedge | constraint edge 0 | energy dynamicsは扱わない |
| **B** | **実行可能三部binding graph＋絶対MDL** | graph選択・variable binding | 系列固有 |

系列Cも複数witnessと対応edgeを扱うが、Cは因果state-variable identityとcounterfactual rolloutを採否基準とする。Bはforward/inverse導出、可逆圧縮、graph metadata込み総記述長を中心にする。

## 実験条件

- seed: 1 / 7 / 19
- train: 48 / 144 / 288 episode
- test: 24例 / split / seed
- split: 既知、未知語順、未知語彙、Rename、別状態表現、入れ子、主語省略、複数段落
- ablation: Exact context / Executable graph / MDL-gated graph
- 上限: object 32、value 32、endpoint 32、triangle 64
- hidden object・field・old/new labelは評価器だけで使用

## 最大288例・3 seed平均

| 条件 | Exact accuracy / pair recall | Graph accuracy / pair recall | MDL accuracy / pair recall |
|---|---:|---:|---:|
| 既知 | 0 / 0 | 0 / **0.0139** | 0 / **0.0139** |
| 未知語順 | 0 / 0 | 0 / 0 | 0 / 0 |
| 未知語彙 | 0 / 0 | 0 / **0.0139** | 0 / **0.0139** |
| Rename | 0 / 0 | 0 / 0 | 0 / 0 |
| 別状態表現 | 0 / 0 | 0 / 0 | 0 / 0 |
| 入れ子 | 0 / 0 | 0 / 0 | 0 / 0 |
| 主語省略 | 0 / 0 | 0 / 0 | 0 / 0 |
| 複数段落 | 0 / 0 | 0 / 0 | 0 / 0 |

追加診断:

- Object node: 6
- Value node: 5
- State endpoint: 32
- Binding triangle: 64
- Raw candidate: 3,124.33
- Forward/inverse audit: 1,855
- 既知graph平均生成候補: 5.99
- 複数段落graph平均生成候補: 5.99
- Literal description: 283,045 bits
- MDL graph description: 26,112 bits

## 判定

**中核仮説は強く反証。**

### Training witnessでは実行可能triangleが形成

Positive witness上のforward after生成、inverse before復元、non-target保存を要求しても64件のtriangleが形成された。Cycle 025の単なる交換可能seedより厳しい条件を通過した点は前進である。

### Held-out executionは全面0

全splitでexecution accuracyとcommit率は0だった。既知・未知語彙でpair recall 0.0139の微小信号はあるが、能力値として採用できない。Graphは複数triangleから異なるafterを同scoreで提案し、全面tie・棄権へ退化した。

> 局所的に実行可能な三角形を集めても、入力ごとにどの三角形を選ぶかというrelation・scope・operation identityがなければprogramにならない。

### MDLは約90.8%短縮したが能力0

総記述長は283,045 bitsから26,112 bitsへ短縮したが、execution accuracyは0のまま。MDLは再び短い失敗libraryを選択した。

### 支配的失敗

1. Object nodeは文字shape classでobject identityではない
2. Value nodeはrelationごとの値domainを分離しない
3. Endpointは局所prefix/suffixでrelation identityを持たない
4. Triangle間の競合を解くnegative witnessがない
5. 主語省略ではobject候補がcommandに存在しない
6. Rename・別状態表現ではsurface nodeをtransportできない

## 反証条件

支持には、GraphがExactをexecution accuracyで上回り、未知形式の少なくとも一つでpair recallを実質的に増やし、wrong commitを増やさずcommit率を正にし、MDL短縮と能力改善を同時に満たす必要があった。今回はtriangle形成とMDL短縮だけが成立した。

## 探索爆発抑制・資源

- 各episodeのobject/value候補は最大8
- observed shape-compatible tripleだけ監査
- triangleはpositive 3以上・wrong 0・inverse 3以上
- 計算量: span `O(NL²)`、audit `O(NK_oK_v)`、推論 `O(TL²)`
- Graph model: 14,701 bytes
- 学習: 0.081秒
- 既知推論: 4.62 ms/example
- 複数段落: 17.46 ms/example
- Peak RSS: 112,140 KiB（Python runtime込み）

1GB未満。既知は5ms未満だが複数段落と弱いスマートフォンCPU実機は未達。

## 系列B固有の進展

1. Surface candidate
2. Reversible span anchor
3. Role-exchange seed
4. **Executable binding triangle――training witnessでは成立**
5. Triangle selection・negative explanation――未成立
6. Relation/scope-conditioned binding graph
7. Hierarchical executable grammar
8. MDL consolidation

核心的知見:

> binding seedの次に実行graphが必要という順序は正しかった。しかし、局所forward/inverse実行を満たすtriangleだけでも不十分で、複数triangleを反例で分離し入力ごとに選択する説明機構が必要である。

## 他系列へ返す知見

- A: 正の予測責任だけでなく競合候補を切るnegative witnessが必要
- C: positive witness fiberにもheld-out negative witnessによるclass選択が必要
- D: positive creditだけでなく他endpointへの誤読consequenceを保持する必要
- E: triadic hyperedgeが複数形成された際にtieを解くnegative constraintが必要

## 次の仮説

**Contrastive Binding Graph Selection by Minimal Negative Witness Cuts**  
（最小negative witness cutによる対照的binding graph選択）

1. Triangleごとにpositive / wrong / noexec witnessを別保持
2. 同じ入力で競合するtriangle pairを抽出
3. 出力が異なる最小文字区間をnegative test候補化
4. Held-out episodeで正triangleだけが保存するnon-target・future consequenceをcut化
5. Cut集合が最小のtriangleを入力固有programとして採用
6. Unknown形式ではunknown cutを保持し無理に確定しない
7. Accuracy・commit coverage・wrong binding・MDLを同時評価

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
