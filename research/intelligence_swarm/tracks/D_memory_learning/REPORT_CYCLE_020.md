# 系列D Cycle 020 研究報告

## 仮説

**Bipartite Query–Object–Relation Addresses with Endpoint-Specific Reconsolidation**  
（endpoint別再固定化を持つ二部query–object–relation address）

Cycle 019では、relation-selective bridge linkがRename writeを0.3548→0.3804へ限定改善した一方、readは0.3611→0.3472へ悪化した。単一linkがwrite template transport、object identity、relation selection、value retrievalを同時に担っていたことが主因候補だった。

本Cycleではmemoryを次へ分離した。

- query endpoint: query文字列からobject候補へ向かう疎edge
- state object endpoint: state内で持続する対象候補
- relation endpoint: query/command contextから形成する匿名relation候補
- relation/value edge: object endpointとrelation endpointを結ぶ局所write/read trace
- fast edge: write証拠だけで即時利用
- slow edge: write/read双方、複数session、damage 0を満たす場合のみ再固定化

## 先行研究整理

2025年のSparse Memory Finetuningは、全パラメータではなく高活性memory slotだけを更新することで、新知識獲得時の既存能力低下を大幅に抑えた。MoRAMはrank-1 key/value memory atomの自己活性化で細粒度の連続学習を行う。2025–2026年のweighted sparsity / meta-plasticity研究も、更新領域と可塑性を局所制御する方向を支持する。

一方、これらはmemory slot、key、encoder、task表現が既に存在する。今回の課題は、生の日本語からquery endpoint・object endpoint・relation edgeそのものを形成する上流問題である。

## 他4系列との重複表

| 系列 | 最新中心 | 限定成功 | 主失敗 | Dとの分離 |
|---|---|---|---|---|
| A | surprisal位相同期cell | candidate recall部分回復 | 選択精度0.105未満 | 予測境界生成は扱わない |
| B | 置換閉包program非終端 | 既知精度0.7889 | 未知形式0、絶対MDL悪化 | grammar/圧縮は扱わない |
| C | 介入footprint hyperedge | alternate 0.1991 | operation transportほぼ0 | 因果world modelは扱わない |
| E | factor swap残差role | object recall一部回復 | value recall全条件0 | energy/attractorは扱わない |
| **D** | **query/object/relation endpoint分離とslow reconsolidation** | 今回検証 | 長期read/write address | 系列固有 |

継承知見:
- A: candidate recall成立前の時間creditはfailureを固定する。
- B: 圧縮・反例符号化は候補生成とは別問題。
- C: 実行不能とwrong transportを分ける。
- E: nullを保持し、候補外でjunk attractorへ一意化しない。

## 実験条件

- event数: 12 / 24 / 48
- seed: 1 / 7 / 19
- split: seen / held paraphrase / rename / alternate state / subject omission / long distractor / combined
- ablation:
  1. joint fast edge
  2. bipartite endpoint edge
  3. slow endpoint-specific reconsolidation
- one-shot
- 48 event相当の干渉後canonical/alias × 全relation latest-value recall
- 学習器はraw before / command / after / queryと順序のみ使用
- hidden object / field / valueは評価器専用

## 最大48 event・3 seed平均

### Write / Read

| 条件 | Joint write/read | Bipartite write/read | Slow write/read |
|---|---:|---:|---:|
| seen | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| held | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| rename | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| alternate | 0.0208 / 0.0278 | 0.0208 / 0.0278 | 0.0000 / 0.2222 |
| omission | 0.1875 / 0.1944 | 0.1875 / 0.1944 | 0.0417 / 0.1389 |
| combined | 0.0751 / 0.0556 | 0.0751 / 0.0556 | 0.0751 / 0.0972 |

### 継続学習probe

- one-shot write: joint=0.0000, bipartite=0.0000, slow=0.0000
- 干渉後latest-value recall: joint=0.1528, bipartite=0.1528, slow=0.5000

## 判定

**中核仮説は強く反証。slow reconsolidationに限定的な干渉耐性信号がある。**

### 1. JointとBipartiteの能力増分が0

全splitでJointとBipartiteのwrite/read/wrong-readが完全に同一だった。endpointをデータ構造として分けただけで、異なる候補classや更新規則を形成していないためである。

### 2. seen / held / rename / longでnode形成0

raw object候補条件が厳しすぎ、主要splitでobject・relation・edgeが一件も形成されなかった。endpoint分離以前にspan proposalが崩壊している。

### 3. slow edgeは干渉後recallを改善

干渉後latest-value recallは0.1528→0.5000へ上昇した。write/read双方・複数session・damage 0を要求するgateが、表面的なfast edgeを除外する限定信号を持つ可能性がある。

ただし通常splitでは、alternate read 0.2222、combined read 0.0972に留まり、wrong readはそれぞれ0.1389 / 0.2361である。一般的なobject permanenceや継続学習成立の証拠ではない。

### 4. one-shotは全方式0

一回提示直後でもwriteできず、少数例高速学習は成立していない。これは忘却ではなく、初期endpoint/address形成失敗である。

### 5. subject omissionの見かけ上の信号は採用不能

omissionではJoint write 0.1875、read 0.1944だが、直前focusと状態表面contextへ依存する。談話中の複数objectから省略主語を解決した証拠ではない。

### 6. slow edgeはread/writeを混ぜる問題を完全には解かない

Slow方式はcombined readを0.0972へ上げる一方、wrong readも0.2361へ増やした。object endpointとrelation/value edgeの独立性がまだ弱く、同一objectの別relationを取り違える。

## RAG・検索との差

本実装は文書検索ではなく、query endpointからobject endpointとrelation endpointを別々に活性化し、relation/value edgeを通じて内部stateを更新・読出しすることを目指す。

しかし現状は最大64個のstate/edgeを走査し、文字gram類似へ依存しているため、semantic memoryではなく疎な表面transducerに留まる。

## 破滅的忘却と表面暗記の分離

- one-shot 0
- seen/held/renameでnode形成0
- endpoint ablation増分0
- slow gateのみ干渉probe改善

よって支配的失敗は破滅的忘却ではなく、**memory形成前のendpoint proposal・relation binding失敗**である。

## 資源量

- Slow model: 33611 bytes
- Object nodes: 6.33
- Relation nodes: 11.33
- Edges: 59.00
- Slow edges: 9.00
- Fast updates: 69.33
- Training: 0.02224 sec
- Inference: 0.2623 ms/example
- Peak RSS: 112116 KiB（Python runtime込み）
- Complexity: proposal `O(L²)`、learning `O(N(A+R)G)`、read/write `O(k(A+R)G)`、`k≤64`

1GB未満・5ms未満は小規模制御条件で達成。弱いスマートフォン実機では未検証。

## 系列D固有の進展

1. Episodic raw trace
2. Object/relation trace separation
3. Alias/bridge transport
4. Query consequence matrix
5. Query/object/relation endpoint separation
6. **Read/write dual-supported slow edge**
7. Endpoint-conditioned local plasticity
8. Sparse indexed retrieval
9. Episodic-to-semantic consolidation

今回、第6段階に干渉耐性の限定信号が出た。一方、第5段階は形式的分離に留まり、能力増分0だった。

## 他系列へ返す知見

- A: candidate cellをmemoryへ固定する際は、生成時の予測信号だけでなくread/write双方の再現を要求する。
- B: nonterminalをslow libraryへ入れる前に、生成と逆引きの双方で利用可能かを監査する。
- C: effect hyperedgeはforward executionだけでなくquery-conditioned inverse retrievalで反証する。
- E: attractor edgeの局所学習はfree/nudgedだけでなくwrite/read dual consequenceを分離して測る。

## 次の仮説

**Tri-Factor Endpoint Memory with Independent Object, Relation, and Value Reconsolidation**  
（object・relation・valueを独立再固定化する三因子endpoint memory）

次はrelation/value edgeを分離する。

1. query→object endpoint
2. query→relation endpoint
3. command→value endpoint
4. object×relation→current value binding
5. write evidenceはvalue edgeだけ更新
6. read evidenceはobject/relation endpointだけ更新
7. 三因子が一致した場合だけslow bindingへ固定
8. top-k sparse indexで全走査を廃止
9. canonical/alias × 全relationのlatest-value recallを主評価にする

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
