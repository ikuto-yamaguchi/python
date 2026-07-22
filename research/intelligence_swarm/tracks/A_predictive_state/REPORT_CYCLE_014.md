# 系列A Cycle 014 研究報告

## 仮説

**Causal-Survival Probe Programs with Counterfactual Outcome Partitions**  
（反実仮想outcome分割を持つ因果生存probe program）

Cycle 013では、文字hashに基づくprobeの正候補生存率が全probeで1.0へ飽和し、意味的utilityを識別できなかった。本Cycleでは文字hashによる候補分割を廃止し、各候補をraw stateへ局所実行した際の次のoutcome channelで候補集合を分割した。

- 実行可能性
- 非対象保存
- 逆操作proxy
- future recall proxy
- 次発話予測proxy

候補を一件ずつ試すのではなく、現在の候補集合を最大分割し、かつ実行可能候補を生存させる共有probeを選択する。

## 先行研究整理

- Active inferenceでは、候補world modelを最も識別するoutcomeを選ぶ情報利得型の行動選択が研究されている。ただし正しいmodel classが候補集合に含まれることが前提になる。https://arxiv.org/abs/2512.21129
- 2025年COLTのpartition learningでは、未知partitionをqueryで識別する際のquery数・round数が解析されているが、要素・query空間自体は定義済みである。https://proceedings.mlr.press/v291/black25b.html
- 2025年ACLのcounterfactual active learningは、何を変え何を保持するかを明示したvariationが少数例学習を助けると報告するが、neuro-symbolic pipelineとLLMによる概念次元抽出を用いる。https://aclanthology.org/2025.findings-acl.50/
- active learningの一般化誤差研究では、informativenessだけでなくrepresentativenessも必要とされる。候補を大きく分割するだけでは意味的妥当性を保証しない。https://proceedings.mlr.press/v265/menden25a.html

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | A候補との判定 |
|---|---|---|---|---|
| B | clause-lattice実誤適用とrelation商 | 実誤適用で既知0.0633→0.2533 | MDL商で0.0967、未知構造0 | program生成・商誘導は棄却 |
| C | intervention persistence object node | 時系列identity形成を試行 | 288介入を3.67 nodeへ過剰統合、全精度0 | object node形成は棄却 |
| D | cross-query write/read address | write 0.0417→0.1065 | read約0.264、schema細分化 | memory address形成は棄却 |
| E | residual-cause二部attractor | seen 0.9741、局所矛盾routingに信号 | cause-edge map供給、無標識候補0 | 内部energy routingは棄却 |
| **A** | **外部outcome partitionを選択し再帰状態更新** | 本Cycleで検証 | candidate proposal・probe自律生成 | 系列固有 |

継承知見:
- B: 実際のoutcome差はsurface riskより増分情報を持つ。
- C: object候補の表面trajectoryだけではidentityにならない。
- D: target gainとnon-target damageを分離する必要がある。
- E: 原因edgeへ帰属できない残差は誤収束か全面停止を生む。

## 実装

学習器・推論器が利用するもの:
- raw日本語文字列
- raw state文字列
- 括弧・句読点から生成したspan候補
- 選択probeに対するgeneric binary outcome

利用しないもの:
- object / relation / value ID
- 形態素解析
- 固定ontology・手書きslot
- 外部LLM・RAG
- 正答文字列を返すfeedback

比較方式:
1. `hash`: 文字fingerprintで候補を分割
2. `causal`: raw stateへの局所実行outcomeで分割
3. `causal_null`: causal分割にabsolute execution fitのnullを追加

停止条件:
- 候補が1つになる
- 残りprobeの分割利得が0
- 最大5 probe
- contradictionまたはnullへ遷移

## 実験

- 例数: 60 / 180 / 540
- seed: 1 / 7 / 19
- 候補上限: 24
- probe上限: 5
- split: 既知marked、12候補曖昧性、入れ子marked、引用なし言い換え、主語省略、複数段落、候補外

## 最大540例・3 seed平均

| 条件 | recall | Hash acc/wrong | Causal acc/wrong | Causal+Null acc/wrong/null | Causal probes |
|---|---:|---:|---:|---:|---:|
| 既知 | 1.0000 | 0.4154/0.3204 | **1.0000/0.0000** | 1.0000/0.0000/0.0000 | 1.000 |
| 曖昧性 | 1.0000 | 0.0377/0.4451 | **0.1488/0.0000** | 0.1488/0.0000/0.0000 | 1.862 |
| 入れ子 | 1.0000 | 0.0636/0.6457 | **0.2019/0.0000** | 0.2019/0.0000/0.0000 | 1.290 |
| 言い換え | 0.0000 | 0/0.2012 | 0/**0.0000** | 0/0/0.0000 | 0.557 |
| 主語省略 | 0.0000 | 0/0.3920 | 0/**0.0000** | 0/0/1.0000 | 0.263 |
| 複数段落 | 0.0000 | 0/0.2333 | 0/**0.0000** | 0/0/0.8025 | 1.143 |
| 候補外 | 0 | 0/0 | 0/0 | 0/0/**1.0000** | 0.000 |

## 限定的に支持された部分

正答候補が集合内に存在する制御条件では、raw execution outcome partitionはhash fingerprintより明確に優れた。

- 既知: 0.4154 → **1.0000**
- 曖昧性: 0.0377 → **0.1488**
- 入れ子: 0.0636 → **0.2019**
- causal方式のwrong commit: 全制御条件で**0**

> 候補を文字fingerprintで分けるのではなく、候補を実行した際に異なるworld outcomeを生成する共有probeで分割する。

## 決定的な反証

**中核仮説は反証。**

1. 候補recallは1.0でも、曖昧性accuracy 0.1488、入れ子0.2019に留まり、大部分を棄権した。5個のoutcome channelでは多数候補が同じ結果を生成する。
2. 言い換え、主語省略、複数段落ではcandidate recallが0。causal probeは誤確定を0へ抑えたが、理解能力は0のまま。
3. `execute / preserve / reverse / recall / next` は手で定義したchannelで、生の日本語・世界相互作用から自律生成していない。
4. 実行器はraw state文字列の局所置換で、object、relation、operation、goal、constraint、causal edgeを形成していない。
5. nullは候補外と主語省略では1.0だが、言い換え0、複数段落0.8025で、proposal failureを安定識別できない。
6. 既知1.0はquoted spanがobject/value候補を完全供給する制御条件で、自由日本語理解の証拠ではない。

## 資源量

- model: 110 bytes
- Peak RSS: 110,988 KiB（Python runtime込み）
- 既知推論: 0.0279 ms/example
- 曖昧性推論: 0.1511 ms/example
- 引用なし最大: 0.6569 ms/example
- 候補: 最大24
- probe: 最大5
- 計算量: proposal `O(L²)`, probe selection/update `O(PH)`

1GB未満・5ms未満は達成したが、弱いスマートフォン実機では未検証。

## 系列A固有の進展

1. Raw candidate proposal
2. Candidate precision / null
3. Executable predictive outcome generation
4. Outcome-equivalence partition
5. Shared active probe scheduling
6. Recursive reversible update
7. **Probe-program self-generation**
8. Open-set semantic abstraction

今回はdelimiter付き条件で3～6に限定信号があった。Cycle 013の「正候補survivalが全probeで飽和する問題」に対し、実行outcomeはprobe間に実際の増分差を作った。しかし1・2・7・8は未成立。

## 他系列へ返す新知見

- B: destruction-vector programは候補を分割するだけでなく、共有probeとして複数候補を一度に区別できるか測る。
- C: object候補の介入partitionが同一ならobject identityを識別できない。target/non-target outcome差が必要。
- D: write/read address候補は複数query outcomeを共有probeとして使えるが、同じ結果を持つ候補は別信号が必要。
- E: residual-cause routing後の候補classに対し、外部outcomeを最大分割するprobeを選択できる。ただし候補外検知は別に必要。

## 次の仮説

**Self-Generated Probe Programs from Prediction-Error Gradients**  
（予測誤差勾配からの自己生成probe program）

次は5種類のprobeを固定供給しない。

1. 候補graphの局所edgeを削除・反転・再束縛
2. 各surgeryが生成する予測差を測る
3. 候補classを分割し、absolute residualも改善するsurgeryだけをprobe programへ昇格
4. 既知probeの組合せで説明できない残差はnull-causeへ保持
5. cross-episodeで同じ局所surgeryが再利用された場合だけ低速libraryへ統合

最低成功条件:
- 既知1.0を維持
- 曖昧性0.1488、入れ子0.2019を改善
- 言い換え・主語省略・複数段落のcandidate recallを0から改善
- 手書きprobe channel数を0にする
- 候補24以下、probe5以下、32KB以下、5ms/example以下

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
