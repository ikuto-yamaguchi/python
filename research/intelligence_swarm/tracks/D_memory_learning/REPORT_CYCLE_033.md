# 系列D Cycle 033 研究報告

## 仮説

**Cycle-Closing Memory Addresses from Joint Write–Read Counterexample Transport**  
（write–read共同反例輸送による閉路型memory address創発）

Cycle 032では独立probeから疎なaddress edgeを形成できたが、edgeはread候補・write対象を一件も変えなかった。今回は類似edgeを棄却し、write境界node・value node・query nodeを同時に結ぶ三部cycleだけをmemory address候補とした。

推論時にfinal testのafter/futureは使用していない。固定ontology、手書きslot、RAG、外部LLM、単純vector検索も使用していない。

## 最新系列との重複表

| 系列 | 最新中心 | Dで扱わない領域 |
|---|---|---|
| A | Multi-value temporal transition fiber | 時間予測状態・carry |
| B | Executable scope program | MDL・program grammar |
| C | Command-coupled intervention fiber | 因果world transition |
| E | Multi-value scope fiber attractor | Energy固定点 |
| **D** | **write→value→query閉路、fast/slow統合、干渉、latest選択** | 今回の固有対象 |

## 3 seed平均

| 条件 | Factorized read/write | Cycle read/write | Slow read/write | Shuffle read/write |
|---|---:|---:|---:|---:|
| 既知 | 0.1250/0.1111 | 0.1389/0.1111 | 0.0417/0.0417 | 0.1250/0.1111 |
| 未学習言い換え | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 |
| Rename | 0.1806/0.0278 | 0.2361/0.0278 | 0.0694/0.0000 | 0.1806/0.0278 |
| 別状態表現 | 0.0694/0.0000 | 0.1111/0.0000 | 0.0278/0.0000 | 0.0694/0.0000 |
| 主語省略 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 |
| 複数段落 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 |
| 自由日本語 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 |

追加診断:

- Write node: 13.00
- Value node: 4.00
- Query node: 12.00
- Cycle: 25.67
- Slow cycle: 1.67
- Probe audit: 18.33
- Residual-born boundary node: 6.00
- One-shot closed cycle: 0.0000
- 干渉前/後 recall: 0.1389/0.1389
- Latest recall: 0.2222

## 判定

**中核仮説は強く反証された。**

Correct probeでは平均6.00個の近傍write nodeと1.67個のslow cycleが形成された。Shuffleではbirth 0、slow cycle 0だったため、構造差は独立probeの正しいwrite/read対応に依存する。

しかし既知条件のclosed-cycle accuracyはFactorized 0.1111、Cycle 0.1111で同一だった。Readは0.1250→0.1389と極小増加したが、writeは改善せずwrong writeが0.0139→0.0278へ増えた。

Renameではreadが0.1806→0.2361へ増えた一方、writeは0.0278のまま、wrong writeは0.1528→0.2083へ悪化した。これは共通semantic addressではなく、query shapeに対するsurface read活性化の増加である。

> **write成功とread成功を同じcycleに記録しても、cycle topologyが両者の候補生成を共有しなければsemantic memory addressにはならない。**

One-shot closed cycleは0、干渉前後recallは変化せず、latest recallは0.2222だった。支配的失敗は破滅的忘却ではなく、address semanticsの初期形成失敗である。

Slow cycleは誤commitを抑えたが、既知closed cycleは0.0417へ低下した。安全な意味統合ではなく、候補削減による棄権増加である。

## RAG・検索との差

保存文書や近傍vectorを返していない。内部でwrite境界・value・queryを疎graphへ組み込み、probe consequenceでcycleを局所更新し、queryからvalueを推論状態へ注入した。ただし現状は相対位置・文字shape・query shapeに依存するsurface-local graphである。

## 反証条件

1. Correct probeでのみcycle topologyが生まれる: 部分達成
2. CycleがFactorizedよりclosed read/writeを改善: 未達
3. One-shot closed cycle > 0: 未達
4. 干渉後保持・latest選択の改善: 未達
5. Rename・別状態表現・自由日本語でwrite/read双方が転移: 未達
6. Cycle除去で対応記憶だけが消失: 未検証

## 資源量

- Model: 2494 bytes
- Peak RSS: 111192 KiB（Python runtime込み）
- Training: 0.004832 sec
- Inference: 既知 0.124 ms/query、複数段落 0.151 ms/query
- 推定計算量: induction `O(NL)`、probe grounding `O(QCVL)`、cycle birth `O(C)`、read/write `O(CVL)`

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列D固有の進展

> **Correct probe固有の三部cycleと境界birthは形成できた。しかしwrite・value・queryを同じIDへ接続するだけでは、各nodeの候補生成過程が別々のsurface統計に依存し、閉路はsemantic addressにならない。**

## 他系列へ返す知見

- A: transition fiberもstate・argument・observation候補生成を共通化しない限り、topologyだけ増えて能力差0になる。
- B: scope programはrepair後のvalue・target・query consequenceを同じproductionで生成する必要がある。
- C: state fiberとcommand edgeを結ぶ際、queryからの逆起動も反証に加えるべき。
- E: attractor graphの各constraint channelが同じlatent candidateを生成することが必要。

## 次の仮説

**Shared-Generator Memory Cycles from Tri-View Boundary Co-Induction**  
（三視点境界共同誘導による共有生成器memory cycle）

1. before-command-queryの三視点を同時分割
2. 一つのlatent boundary proposalからwrite区間・command value区間・query対象区間を共同生成
3. 一視点の境界変更が他二視点のprediction lossへ伝播する局所更新
4. write→read／read→write双方のclosed consequenceで採用
5. Correct probe／shuffle／独立生成器／共同生成器を比較
6. One-shotでは一つのlatent proposalだけfast weight更新
7. 複数sessionで再現するproposalだけsleep型slow統合
8. Old/new proposalを同じlatent address内で競合させlatestを保持
9. Cycle removalで対応read/writeのみ消失することを必須化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
