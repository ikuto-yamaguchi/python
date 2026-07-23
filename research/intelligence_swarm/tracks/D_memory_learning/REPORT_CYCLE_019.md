# 系列D Cycle 019 研究報告

## 仮説

**Relation-Selective Bridge Links by Cross-Query Consequence Matrices**  
（cross-query consequence matrixによるrelation選択的bridge link）

Cycle 018では、`before / command / after / query` の双方向transportを満たすbridge linkによりRename writeが0.6462→0.6823へ限定改善した一方、readは0.3333→0.2917へ悪化し、真のalias 4組に対して約95.67 linkを生成した。完全なsurface往復はalias同値性の十分条件ではなかった。

本Cycleでは各bridge linkを複数の匿名query contextへ適用し、次のcross-query consequence matrixを形成した。

- transport後queryが対応stateへ到達する正consequence
- 別query family・別objectへ誤伝播するdamage
- 対応stateがないnull consequence
- 2種類以上のquery contextで正consequenceが再現するlinkだけrelation-selective link化
- 複数session・5回以上の正consequenceを満たすlinkだけslow schema化

学習器入力はraw `before / command / after / query` とsession順序のみで、hidden object・field・valueは評価器だけが使用する。

## 先行研究整理

- EverMemOS (ACL 2026) はepisodic trace→semantic consolidation→reconstructive recollectionのmemory lifecycleを提案するが、MemCell/Scene形成はLLM処理を前提とする。https://aclanthology.org/2026.acl-long.2125/
- RecMem (ACL Findings 2026) は再発したinteractionだけをepisodic/semantic memoryへ統合し構築コストを最大87%削減するが、semantic similarity encoderとLLM抽出を使う。https://aclanthology.org/2026.findings-acl.1619/
- HeLa-Mem (ACL 2026) はHebbian graph、consolidation、spreading activationを組み合わせるが、memory node自体は既定のLLM表現である。https://aclanthology.org/2026.acl-long.625/
- Memini (arXiv:2605.05097) はfast/slow edge dynamicsで即時利用・強化・忘却を統一するが、graph node/edgeは定義済みである。https://arxiv.org/abs/2605.05097
- T-Mem (arXiv:2606.15405) はwrite-time triggerでsurface非類似の将来queryからもmemoryを到達可能にするが、trigger生成に既存semantic systemを用いる。https://arxiv.org/abs/2606.15405

これらは再発、fast/slow consolidation、query-conditioned recallの重要性を支持するが、生の日本語surface linkがobject aliasかvalue差か文型差かを局所的に識別する問題は解いていない。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | D候補との区別 |
|---|---|---|---|---|
| A | occlusion–expansionによる最小十分予測境界 | object/value失敗を分離 | value recall全条件0 | 境界生成は扱わない |
| B | failure–success transportからのrole因子 | 匿名failureでwrong commit抑制 | program merge 0、未知形式0 | program商・MDLは扱わない |
| C | cycle-consistent局所alignment対応写像 | preservation anchorに限定信号 | bidirectional transport悪化 | world operation形成は扱わない |
| E | counterfactual factor swapによるrole分離 | localized flowで推論短縮 | candidate recall 0 | energy・role birthは扱わない |
| **D** | **bridge linkを複数query consequenceで反証しslow memory化** | 今回検証 | relation-selective address | 系列固有 |

継承知見:
- A: 長い包含spanのsurface整合だけでは最小object境界にならない。
- B: failure predicateは棄却器になっても候補生成器にはならない。
- C: null transportとwrong transportを分離する。
- E: candidate外ではnullを維持し、相対scoreだけで一意化しない。

## 実験条件

- seed: 1 / 7 / 19
- train event: 12 / 24 / 48
- relation: 3種類（評価器上のみ）
- split: seen / held paraphrase / rename / alternate state / combined
- ablation:
  1. No alias
  2. Bidirectional bridge
  3. Relation-selective bridge
  4. Slow reconsolidated bridge
- 一回提示学習
- 24 event干渉後のcanonical/alias×全relation厳密latest-value recall
- episode保持上限: 64

## 最大48 event・3 seed平均

### Write accuracy

| 条件 | No alias | Bidirectional | Selective | Slow |
|---|---:|---:|---:|---:|
| seen | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| held | 0.6875 | 0.6875 | 0.6875 | 0.6875 |
| rename | 0.3548 | 0.3804 | 0.3804 | 0.3804 |
| alternate | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| combined | 0.3548 | 0.3804 | 0.3804 | 0.3804 |

### Read accuracy / wrong read

| 条件 | No alias | Bidirectional | Selective | Slow |
|---|---:|---:|---:|---:|
| seen | 0.4167/0.5833 | 0.4167/0.5833 | 0.4167/0.5833 | 0.4167/0.5833 |
| held | 0.5556/0.4444 | 0.5556/0.4444 | 0.5556/0.4444 | 0.5556/0.4444 |
| rename | 0.3611/0.6389 | 0.3472/0.6528 | 0.3472/0.6528 | 0.3472/0.6528 |
| alternate | 0.0556/0.1667 | 0.0556/0.1667 | 0.0556/0.1667 | 0.0556/0.1667 |
| combined | 0.2361/0.6111 | 0.2361/0.7361 | 0.2361/0.7361 | 0.2361/0.7361 |

### 継続学習probe

- one-shot: 全方式 1.0000
- 干渉後の厳密latest-value recall:
  - No alias: 0.2917
  - Bidirectional: 0.3333
  - Selective: 0.3333
  - Slow: 0.3333

## 判定

**中核仮説は反証。cross-query consequence matrixの増分は0だった。**

### Selective方式はBidirectional方式と完全同一

Rename/combinedでrelation-selective linkとslow linkは平均1件形成されたが、Bidirectional・Selective・Slowのwrite/read・干渉指標は全て同一だった。consequence matrixは既存bridge classを追加分割していない。

### Rename writeの限定信号は再現

Rename writeはNo alias 0.3548 からbridge系 0.3804 へ+0.0256、combinedでも+0.0256改善した。

ただしreadはRename 0.3611→0.3472へ悪化し、wrong readも0.6389→0.6528へ増加した。surface aliasを跨ぐwrite template展開とobject identity recallは別能力である。

### 匿名query contextがrelationを識別しない

consequence matrixはqueryを候補surfaceでmaskした文字gramでcluster化した。これは「場所」「状態」「担当」に相当するcontextをある程度分けられるが、同じ文型を共有する別objectや、state側のvalue差をrelation-specific consequenceから排除できない。

### Slow reconsolidationの追加効果0

Slow linkは平均1件形成されたが、Selective方式に対する能力増分は0。再発回数とsession数だけでslow化してもsemantic memoryにはならない。

### 干渉後recallは限定改善だが低い

厳密なcanonical/alias×全relation latest-value recallは0.2917→0.3333へ改善した。しかし絶対値は低く、2/3近くのqueryに失敗する。破滅的忘却克服やobject permanenceの証拠にはならない。

### One-shotは能力証拠から除外

全方式1.0だが同じepisode直後のtemplate再実行であり、未知domain transferやsemantic address形成を示さない。

## 表面暗記と破滅的忘却の分離

支配的問題は形成済み記憶が後から失われる破滅的忘却ではない。

- relation-selective ablationの増分0
- Rename read悪化
- held/alternateへの増分0
- strict interference recallは0.3333

したがって主失敗は、bridge linkのobject/relation/value軸の識別不足と、read addressへの統合失敗である。

## RAG・検索との差

bridge linkは保存文書を検索して返すだけでなく、別surfaceへwrite templateをtransportして内部stateを書き換える。しかし最大64 episodeを保持し全走査するため、依然として小規模episodic transducerであり、semantic memoryではない。

## 資源量

- Selective model: 58153 bytes
- episode: 64上限
- link: 219.00
- active/selective/slow link: 1.00 / 1.00 / 1.00
- matrix update: 481.33
- training: 0.044318 sec
- inference: 8.4804 ms/example
- Peak RSS: 111868 KiB（Python runtime込み）
- complexity:
  - bridge `O(NWH)`
  - consequence matrix `O(LQE)`
  - read/write `O(EKG)`
  - `E≤64`

1GB未満は達成。seen/held/alternateは5ms未満だがRename/combinedは約8.5msで、弱いスマートフォンCPUの5ms目標は未達。

## 系列D固有の進展

1. Raw mention proposal
2. Object/relation trace separation
3. Sparse address binding
4. Temporary alias proposal
5. Provenance retention
6. Read/write counterfactual credit
7. Bidirectional bridge transport
8. **Cross-query consequence matrix**
9. Slow reconsolidation
10. **Query-conditioned object address factorization**
11. Episodic-to-semantic consolidation

第8段階を実装したが、匿名query contextではbridge classを追加分割できなかった。

最大の新知見:

> 複数relation queryで同じlinkが使えることはobject aliasの十分条件ではない。query consequenceは「どのobjectへ戻ったか」と「どのrelation valueを読んだか」を別因子として保持しなければ、write alias展開とread object identityが混線する。

## 他系列へ返す知見

- A: persistence候補を複数queryで再利用できてもobject境界とは限らない。object identityとrelation value consequenceを分ける。
- B: failure/success role因子ではquery target因子とreturned-value因子を別符号にする。
- C: transport correspondenceはstate anchorだけでなく、query-conditioned object endpointを保持する。
- E: factor swap energyをobject endpoint残差とrelation value残差へ分離する。

## 次の仮説

**Bipartite Query–Object–Relation Addresses with Endpoint-Specific Reconsolidation**  
（endpoint別再固定化を持つ二部query–object–relation address）

次はbridge linkを単一alias edgeとして保持しない。

- query側endpointとstate側object endpointを別node化
- relation value edgeを第三の局所edgeとして保持
- query transportが同一object endpointへ戻る証拠と、relation-specific valueを正しく読む証拠を独立credit化
- write改善だけでreadを壊すlinkはwrite-only fast traceへ隔離
- read/write双方で支持されたedgeだけslow schemaへ統合
- 全episode走査をやめ、endpointから上位k件だけ展開
- interference後のcanonical/alias×全relation latest-value recallを主要gate化

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
