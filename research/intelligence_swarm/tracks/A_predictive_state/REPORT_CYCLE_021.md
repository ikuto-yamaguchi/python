# 系列A Cycle 021 研究報告

## 仮説

**Active Query Disambiguation over Surprise-Synchronized Predictive Cells**  
（驚き同期予測cellに対する能動query識別）

Cycle 020では、command / before / after / futureのcharacter-level surprisal peakを同期させることで、seen pair recall 0.2500、held 0.3125、rename 0.2917まで候補生成を部分回復した。しかし、候補選択精度は0.105未満で、同期cellは意味roleではなくsurface prediction rhythmに留まった。

本Cycleでは候補境界を増やさず、同期cellから得たobject/value pair候補を同時保持し、複数future horizon・after・before persistence・non-target preservationについて、候補集合を最も分割するqueryを能動選択した。query outcome後に候補状態を再帰更新し、最大4 queryで一意化またはnull停止する。

## 先行研究整理

- Active Task Disambiguation (ICLR 2025) は、曖昧なtask specificationに対して情報利得を最大化する質問を選ぶ枠組みを示す。ただしLLMが候補task空間を生成済みである。
- Active Inference with Dynamic Planning and Information Gain (Entropy 2025) は、低次元潜在状態上でepistemic valueとgoal-directed planningを統合するが、観測・行動空間は定義済みである。
- Active inference and artificial reasoning (2025) はexpected information gainでworld-model hypothesisを識別する構造学習を論じるが、仮説集合は与えられる。
- PSR研究ではtest/historyの選択が性能を大きく左右し、有限の不十分なtest集合をnaiveに選ぶと劣化することが知られている。

本Cycleの上流課題は、生の日本語から生成した不完全なcandidate cell集合に対して、queryが意味bindingを識別できるかである。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | Aとの区別 |
|---|---|---|---|---|
| B | 置換閉包program非終端 | seen 0.7889、wrong 0.0028 | 未知形式0、MDL 1.63倍悪化 | grammar・圧縮は扱わない |
| C | 介入footprint hyperedge | alternate 0.1991 | operation transportほぼ0 | world effect algebraは扱わない |
| D | endpoint別slow memory | 干渉後recall 0.5 | 主要split node 0 | 長期memoryは扱わない |
| E | 固定点basin曲率 | null安全停止 | value recall 0、曲率能力増分0 | energy basinは扱わない |
| **A** | **同期cellを能動queryで分割し再帰状態更新** | 今回検証 | query semantics・open-set cell | 予測状態軸固有 |

重複棄却:
- Bのcontext nonterminal化はprogram grammarであり棄却。
- Cのtransition transport/hypergraphはworld operation形成であり棄却。
- Dのquery endpoint memoryは長期read/write addressであり棄却。
- Eのbasin分岐candidate birthはenergy dynamicsであり棄却。

継承知見:
- B: 候補内再利用と未知形式生成は分ける。
- C: 実行不能を意味outcomeとして数えない。
- D: query endpointとreturned valueを混線させない。
- E: nullを常時保持し、候補外で無理に一意化しない。

## 実装

- Character trigram predictor（attentionなし）
- command / before / after / future1 / future2のsurprisal peakから同期cellを生成
- persistence候補最大6、change候補最大6、pair最大16
- query family:
  - future1 presence
  - future2 presence
  - after change
  - before persistence
  - non-target preservation
- 各queryでcandidate outcome partitionを算出し、最大分割queryを選択
- environment observation後にactive setを再帰更新
- 最大4 query、改善なし・平坦化・一意化で停止
- active+nullでは正答pairが候補集合外、または一意化不能ならnull保持

Hidden object/valueは評価器とenvironment observationの生成だけに使用し、learnerのcandidate proposal・score・query selectionには使用していない。

## 最大144 episode・3 seed平均

| 条件 | Pair recall | Passive精度 | Active精度 | Active誤確定 | Active+Null誤確定 | 平均query |
|---|---:|---:|---:|---:|---:|---:|
| seen | 0.2361 | 0.0000 | **0.2361** | 0.7639 | 0.0000 | 1.22 |
| held | 0.3750 | 0.0000 | **0.3750** | 0.4167 | 0.0000 | 1.40 |
| rename | 0.3472 | 0.0000 | **0.2917** | 0.3611 | 0.0000 | 1.39 |
| alternate | 0.2361 | 0.0000 | **0.2361** | 0.7639 | 0.0000 | 1.21 |
| nested | 0.0000 | 0.0000 | 0.0000 | 0.3889 | 0.0000 | 0.65 |
| omitted | 0.0000 | 0.0000 | 0.0000 | 0.7222 | 0.0000 | 1.00 |
| paragraph | 0.0000 | 0.0000 | 0.0000 | 0.1944 | 0.0000 | 0.64 |
| plan | 0.0000 | 0.0000 | 0.0000 | 0.1250 | 0.0000 | 0.93 |

## 判定

**中核仮説は部分支持だが、一般知能原理としては反証。**

### 限定支持: 候補集合内ではqueryが正答をほぼ完全に回復

- seen: pair recall 0.2361、active accuracy 0.2361
- held: pair recall 0.3750、active accuracy 0.3750
- alternate: pair recall 0.2361、active accuracy 0.2361
- rename: pair recall 0.3472に対しactive accuracy 0.2917

Passive方式は複数候補を保持したまま一意化できずaccuracy 0だった。Active queryは平均1.2〜1.4回で候補集合を縮約し、seen/held/alternateでは候補集合内の正答をすべて選択した。

これはCycle 020の「candidate recallはあるが選択できない」ボトルネックに対する明確な増分である。

### しかしquery outcomeが評価環境依存

Environmentはhidden正解pairに対するfuture/after/persistence outcomeを返す。これは正解文字列を直接渡してはいないが、現実世界・ユーザー・外部観測から同等の情報を得る機構は未実装である。

したがって、今回示したのは、**適切な観測oracleが存在する場合の候補識別policy**であり、自律的な日本語理解そのものではない。

### 候補外では危険

NullなしActiveはpair recall 0の条件でも誤確定した。

- nested wrong: 0.3889
- omitted wrong: 0.7222
- paragraph wrong: 0.1944
- plan wrong: 0.1250

Active+Nullは全splitでwrong commitを0へ抑えたが、候補外条件は全面棄権であり能力増分はない。

### Renameでは候補集合内でも一部失敗

Rename pair recall 0.3472に対しaccuracy 0.2917。複数候補が同じfuture/after包含outcomeを持ち、query familyの識別力が不足した。

Object alias・relation・valueを分けたquery outcomeではなく、文字包含proxyを使っているためである。

### 長距離・省略・計画変更は未解決

- nested / paragraph / plan pair recall 0
- omitted object endpointなし
- 旧案・新案・revision scopeなし
- 複数段落のdistractorを跨ぐ時間的抽象化なし

Active queryは候補集合を生成せず、候補外を救済できない。

## 再帰状態更新

- seen: initial 16.0 → final 1.0、更新1.22回
- held: initial 16.0 → final 4.13、更新1.19回
- rename: initial 16.0 → final 4.65、更新1.17回
- alternate: initial 16.0 → final 1.0、更新1.21回

候補active setの再帰更新は成立した。ただし内部状態はobject/relation/goal graphではなく、candidate pair集合である。

## 資源量

- Active model: 12435 bytes
- Predictive prototypes: 64
- Training: 0.01156 sec
- Inference:
  - seen 7.705 ms/example
  - held 7.896 ms/example
  - rename 7.758 ms/example
  - paragraph 2.511 ms/example
- Peak RSS: 111632 KiB（Python runtime込み）
- 計算量:
  - char prediction `O(NL)`
  - cell alignment `O(Hc(Hb+Ha+Hf))`
  - active query `O(QH)`, `Q≤5`, `H≤16`

1GB未満は達成。active条件ではseen/held/renameが約7.7〜7.9msで、弱いスマートフォン5ms目標は未達。実機未検証。

## 既存方式との差

- Transformer attentionなし
- 固定slot/ontologyなし
- LLM/RAGなし
- 一方向分類ではなく候補を同時保持し、観測queryで再帰更新
- 単純active learningと異なり、instance labelを質問せずfuture/after/persistenceの予測outcomeでlatent pairを分割
- PSRに近いが、test集合は固定意味変数ではなくraw同期cellから生成された候補へ適用

## 系列A固有の進展

予測状態形成を次へ更新する。

1. Raw prediction-error stream
2. Surprise peak event
3. Cross-stream phase alignment
4. Persistence/change候補
5. Candidate pair active set
6. **Information-gain query selection**
7. **Observation-conditioned recursive state update**
8. Open-set query/cell co-generation
9. Temporal abstraction
10. 自由日本語統合

今回、第6〜7段階には明確な限定信号が出た。一方、第8段階がないため候補外入力を救済できない。

核心的知見:

> 適切な予測候補が集合内にある場合、少数のfuture-horizon queryはsurface scoreより強く候補を識別できる。しかしqueryはcandidate recallを増やさず、観測oracleとquery semanticsが未形成なら一般知能にはならない。

## 他系列へ返す知見

- B: nonterminal候補が複数残る場合、導出結果を最も分割するheld-out testを能動選択できる。ただしunknown productionは生成しない。
- C: effect hyperedgeが実行可能なら、future/non-target outcome queryでcandidate edgeを少数回で分割できる。
- D: endpoint候補のread/write双方を一括scoreせず、候補endpointを分けるquery consequenceを逐次観測する価値がある。
- E: basin候補が複数ある場合、曲率rankingより候補partitionを増やすnudge outcomeの方が識別力を持ち得る。ただしnull gate必須。

## 次の仮説

**Self-Generated Predictive Tests from Candidate Disagreement Residuals**  
（候補間不一致残差からの予測test自己生成）

次は固定5 query familyを廃止する。

1. 候補pairごとのmulti-horizon予測文字列を生成
2. 候補間で最も異なる局所観測区間をtest候補化
3. Testを実行した際の観測可能性・non-target costを評価
4. 固定query名なしでinformation gain / cost比が最大のtestを選択
5. 候補集合外では、既存testの全outcome不一致をopen-set cell birth信号へ返す
6. Query後にcell境界・pair bindingを再帰更新
7. 長距離・省略・計画変更でcandidate recallが増えるか独立評価

成功条件:
- 固定query familyよりheld/rename selection精度を改善
- nested/omitted/paragraph/plan pair recallを0から改善
- wrong commit 0（null維持）
- 平均query 3以下
- 5ms/example以下
- 32KB以下

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
