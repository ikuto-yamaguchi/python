# 系列C Cycle 022 研究報告

## 仮説

**Executable Effect Hypergraphs from Contrastive Transition Transport**  
（contrastive transition transportからの実行可能効果hypergraph）

Cycle 021では、raw before/after差分から効果footprintを先にclusterしたが、seenを含む主要条件でoperation transport候補が0だったため、hyperedgeは能力を変えなかった。

本Cycleでは順序を逆転し、各局所transition ruleを全episodeへ再実行して、transport outcomeを `success / wrong / null` に分離した。複数surfaceでsuccessが再現し、wrong率が低く、同じnon-target footprintを持つruleだけをhyperedgeへまとめる。

## 先行研究整理

- 近年の因果表現学習は、未知介入targetを含む場合でも、十分に多様な環境変化があれば潜在因果変数を識別できる条件を解析している。ただし観測変数・環境・混合過程は明示的に定式化されている。
- Generative Intervention Modelsは、摂動特徴から未知のatomic intervention分布を学ぶが、潜在因果graphと摂動feature空間を前提とする。
- PatchWorldはoffline trajectoryから実行可能なsymbolic belief-state programを帰納し、counterexample-guided repairで局所修正する。しかしworld-model program生成に外部構造とコード表現を使う。
- Object-centric world model研究は、物体表現が計算効率と長期予測を改善し得ることを示すが、slot・encoder・object annotation等を前提とする場合が多い。

したがって、生の日本語からobject/state/operation候補を形成し、未知surfaceへ実行可能にtransportする上流問題は依然未解決である。

## 他4系列との重複表

| 系列 | 最新中心 | 限定成功 | 主失敗 | Cで棄却・分離した方向 |
|---|---|---|---|---|
| A | self-generated predictive test | 候補集合内のactive識別 | open-set候補生成なし | query policyは扱わない |
| B | partial derivation homomorphism | filler置換に限定信号 | context abstraction 0 | grammar/MDLは扱わない |
| D | tri-factor endpoint memory | slow edgeの干渉耐性 | endpoint open-set形成なし | 長期memoryは扱わない |
| E | bifurcation-guided factor birth | null安全停止 | value recall 0 | energy basinは扱わない |
| **C** | **success/wrong/null transport後のeffect hypergraph** | 今回検証 | 実行可能因果operation | 系列固有 |

継承知見:
- A: candidate recallがない状態でactive queryを行っても候補外構造は生成できない。
- B: noexecを意味差として扱うと未知surfaceの同値性検査前に分裂する。
- D: forward write成功だけではinverse retrievalやobject identityを証明しない。
- E: basin安定性は意味的正しさの代替にならない。

## 実験条件

- 学習例数: 48 / 144 / 288
- seed: 1 / 7 / 19
- test: seen / held paraphrase / rename / alternate state / subject omission / paragraph / plan change / counterfactual
- rule上限: 64
- 比較:
  1. Surface rule
  2. Contrastive transport reliability
  3. Executable effect hypergraph
- hidden object / field / valueは評価器のみ
- 外部LLM、RAG、形態素解析、固定ontology、手書きslotは不使用

## 最大288例・3 seed平均

| 条件 | Surface | Transport | Hypergraph |
|---|---:|---:|---:|
| seen | 0.0000 | 0.0000 | 0.0000 |
| held paraphrase | 0.0000 | 0.0000 | 0.0000 |
| rename | 0.0000 | 0.0000 | 0.0000 |
| alternate state | 0.1528 | 0.1528 | 0.1528 |
| subject omission | 0.0000 | 0.0000 | 0.0000 |
| paragraph | 0.0000 | 0.0000 | 0.0000 |
| plan change | 0.0000 | 0.0000 | 0.0000 |
| counterfactual | 0.0000 | 0.0000 | 0.0000 |

Transport audit（平均）:

- success: 158
- wrong: 4
- null: 18270
- recurrent hyperedges: 4.33

## 判定

**中核仮説は強く反証。**

### 1. Transport reliabilityの能力増分が0

Surface / Transport / Hypergraphは全splitで完全に同じaccuracy・null率・candidate数となった。

Transport success/wrong/nullを明示的に数えても、test時に実行可能なrule集合を一件も追加分割しなかった。

### 2. null transportが支配

64 ruleを学習したが、全training episodeへのtransport auditは平均:

- success 158
- wrong 4
- null 18,270

であり、約99%が実行不能である。

success率の高いruleだけを選んでも、そのsuccessは同一surface contextの反復に集中している。未知表現へoperationを運ぶ証拠ではない。

### 3. Hyperedge 4.33件を形成しても空の分類器

平均4.33個のhyperedgeを形成したが、seen / held / rename / omission / paragraph / plan / counterfactualではcandidate 0、null率1.0だった。

Effect groupingは、実行可能transitionが既にある場合の後段圧縮にはなり得るが、operation transport自体を生成しない。

### 4. alternate state 0.1528は表面信号

alternate stateだけaccuracy 0.1528、candidate 0.7847だったが、3方式が完全同一である。

区切り記号と短いstate contextが偶然一致した結果であり、contrastive transportやhypergraphの成果ではない。

### 5. sequential counterfactual coverageは実質0

- coverage: 0.0213
- conditional accuracy: 0.6667

coverageは約2.1%しかないため、因果合成能力として採用しない。

### 6. 相関暗記と因果理解の分離

- 同一surfaceのtrain auditにはsuccessがある
- held / rename / paragraph / plan / counterfactualでは実行候補0
- hyperedge形成後も能力差0
- sequential composition coverage 0.0213

したがって観測されたsuccessは局所文字contextの再出現であり、object permanence・relation identity・causal direction・planningの証拠ではない。

## 資源量

- Hypergraph model: 68094 bytes
- Rule: 64
- Hyperedge: 4.33
- 学習時間: 0.008425 sec
- 推論時間: 0.023270 ms/example
- Peak RSS: 114328 KiB（Python runtime込み）
- 推定計算量:
  - rule抽出 `O(NL)`
  - transport audit `O(PNG)`
  - hypergraph形成 `O(P)`
  - 推論 `O(PG)`
  - `P <= 64`

1GB未満・5ms未満は小規模制御条件で達成した。弱いスマートフォン実機では未検証。

## 系列C固有の進展

因果world model形成段階を更新する。

1. Raw event proposal
2. Local transition extraction
3. Success/wrong/null transport separation
4. Transport reliability
5. Effect footprint
6. Executable effect hypergraph
7. **Open-form transport map generation**
8. Object/relation/state-variable identity
9. Counterfactual composition
10. Goal/constraint planning

今回、第3段階を明示的に実装したが、能力増分は0だった。

核心的知見:

> **Success/wrong/nullを分離することは評価の健全化には必要だが、未知surfaceへのtransport写像を生成しない。既存ruleの信頼度を測るだけでは、実行不能の99%を因果operationへ変えられない。**

## 他系列へ返す知見

- A: predictive testを行う前に、candidate actionが未知state表現へ実行可能かを独立評価する。
- B: partial homomorphismでnoexecをunknown扱いにしても、新しいtransport mapを生成しなければcontext abstractionは進まない。
- D: slow edgeはread/write支持だけでなく、未知surfaceへのtransition executionを監査する。
- E: null basin・candidate basinの分岐位置だけでなく、生成factorが実際にstate transitionをtransportするかを必須gateにする。

## 次の仮説

**Transport-Map Birth from Cross-Episode Edit Correspondence Programs**  
（episode横断edit対応programからのtransport map創発）

次は既存ruleの信頼度rankingをやめ、transport写像そのものを生成する。

1. before/afterの保存segmentと変化segmentを局所edit graph化
2. 異episode間でedit graphの部分対応候補を生成
3. commandの変化区間を対応先state segmentへ写す小さなcorrespondence programを帰納
4. source→targetとtarget→sourceで局所transitionを再現する場合だけ保持
5. object/value/relationを個別にswapし、どの対応edgeが壊れるかを反証
6. success/wrong/nullは写像candidateの評価に使い、nullを通常failureと混ぜない
7. 学習済みsurfaceを含まないheld/rename/alternateでtransport coverageを主指標化
8. 実行可能mapだけでcounterfactual compositionを評価

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
