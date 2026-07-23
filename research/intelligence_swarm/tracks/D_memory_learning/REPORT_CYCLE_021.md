# 系列D Cycle 021 研究報告

## 仮説

**Tri-Factor Endpoint Memory with Independent Object, Relation, and Value Reconsolidation**  
（object・relation・valueを独立再固定化する三因子endpoint memory）

Cycle 020ではquery/object/relation endpointを構造上分離したものの、Joint方式との能力差は0だった。一方、write/read双方・複数session・damage 0を要求するslow edgeは、干渉後latest-value recallを0.1528から0.5000へ改善した。

本Cycleではrelationに混在していたvalueを独立endpointへ分離し、raw `before / command / after / query` だけから次を形成した。

- object endpoint: before・command・queryで再出現するraw span
- relation endpoint: query・stateで再出現し、object/valueと異なるraw context
- value endpoint: before/after局所差分とcommand内の対応区間
- binding: object × relation × value
- slow binding: write/read双方、複数session、damage 0を満たすbinding

hidden object/relation/value labelは評価器専用で、学習器は使用しない。

## 先行研究整理

2025年のヒト海馬研究では、想起成功時に疎でpattern-separatedなcodeが観測された。2025年のPLOS Biology研究ではepisodic memory成功が短時間・疎・event-alignedなconnectivity stateと関連した。AAAI 2026のMISTは更新対象を局所的に制限することでplasticityと既存知識保持を両立する方向を示した。2026年のmemory buffer理論研究は、bufferが忘却と一般化へ効く条件を分離している。

これらは疎な局所更新とepisodic/semantic分業を支持するが、endpointやmemory itemは既に定義されている。生の日本語からobject/relation/value endpointを形成する問題は別に残る。

## 他4系列との重複表

| 系列 | 最新中心 | 限定信号 | 未解決 | D候補との区別 |
|---|---|---|---|---|
| A | 候補間不一致からの予測test自己生成 | 候補集合内の能動識別 | open-set candidate生成 | query policyは扱わない |
| B | 部分導出準同型によるcontext関係 | filler再利用 | context abstraction 0 | grammar・MDLは扱わない |
| C | edit対応programからのtransport map創発 | success/wrong/null分離 | transport約99% null | world operationは扱わない |
| E | basin分岐によるopen-set factor birth | null安全停止 | value recall 0 | energy dynamicsは扱わない |
| **D** | **object/relation/value endpointの独立形成とslow binding** | 今回検証 | 長期memory address | 系列固有 |

棄却した候補は、Aと重なるactive query、Bと重なるendpoint grammar圧縮、Cと重なるtransition transport map、Eと重なるenergy basinによるendpoint birthである。

## 実験条件

- seed: 1 / 7 / 19
- event数: 6 / 12
- split: seen / paraphrase / rename / alternate state / omitted subject / long distractor / combined / unseen domain
- ablation: Joint tuple / Tri-factor endpoint / Slow-only reconsolidated
- one-shot probe
- 12件干渉 + 6件rename後のlatest-value recall
- 外部依存なし

## 最大12 event・3 seed平均

| 条件 | Joint write/read | Tri-factor write/read | Slow write/read |
|---|---:|---:|---:|
| seen | 1.0000 / 0.5661 | 0.9722 / 0.5476 | 0 / 0 |
| paraphrase | 1.0000 / 0.6045 | 0.8889 / 0.3538 | 0 / 0 |
| rename | 1.0000 / 0.4857 | 0.9167 / 0.5206 | 0 / 0 |
| alternate | 0.3333 / 0.3413 | 0.3333 / 0.3492 | 0 / 0 |
| omitted | 0.9167 / 0.6541 | 0.8333 / 0.4636 | 0 / 0 |
| long | 0.8056 / 0.5714 | 0.7778 / 0.4762 | 0 / 0 |
| combined | 0.5000 / 0.5397 | 0.4722 / 0.2222 | 0 / 0 |
| unseen domain | 1.0000 / 0.6759 | 0.6944 / 0.3056 | 0 / 0 |

Tri-factorは誤読率を低下させた。

- seen: 0.4339 → 0.1270
- paraphrase: 0.3955 → 0.1005
- rename: 0.5143 → 0.2032
- unseen domain: 0.3241 → 0.0000

## 判定

**中核仮説は強く反証。endpoint分離には誤読抑制の限定信号だけが残った。**

### Tri-factorはwriteを悪化

seen writeは1.0000から0.9722、renameは1.0000から0.9167、unseen domainは1.0000から0.6944へ低下した。Object/relation/value endpointを独立形成しても、正しい三者bindingを安定して再結合できない。

### 誤伝播は減少

seen wrong readは0.4339から0.1270、paraphraseは0.3955から0.1005、unseen domainは0.3241から0へ低下した。単一tupleへ全機能を混ぜるより、endpoint分離は誤object・誤relationへの伝播を抑える可能性がある。ただしread accuracy自体はJointを上回らず、全面的な能力改善ではない。

### Slow bindingが0件

全splitでslow bindingは0だった。Value endpointがsurface contextごとに分裂し、同一object×relation×value bindingへ複数sessionのwrite/read supportが集約されなかった。Cycle 020のslow gate干渉耐性は再現しなかった。

### One-shotと干渉

One-shotはJoint 1.0、Tri-factor 1.0、Slow 0。Slow gateは一回提示学習を拒否した。

干渉後latest-value recallはJoint 0.4574、Tri-factor 0.3685、Slow 0。支配的失敗は形成済み記憶の忘却ではなく、初期value endpoint形成と三因子bindingの失敗である。

### 未知domain得点の解釈

新しいobject名がbefore/command/queryへそのまま反復するため、raw span共起でendpointを形成できる。語彙意味やobject categoryを学習した証拠ではない。

## RAG・検索との差

Tri-factor memoryは文書を検索して返すだけでなく、queryからobject/relation endpointを活性化し、commandからvalue endpointを形成して内部stateを書き換える。ただしendpoint matchingはraw文字gramと局所差分に依存し、意味推論・object permanence・goal/constraint保持には到達していない。

## 資源量

- Tri-factor model: 32,676 bytes
- Object nodes: 6.00
- Relation nodes: 6.00
- Value nodes: 9.33
- Bindings: 12.00
- Slow bindings: 0
- Training: 0.00612 sec
- Inference: 0.2007 ms/query
- Peak RSS: 116,520 KiB（Python runtime込み）
- complexity: proposal `O(L²)`、endpoint matching `O((O+R+V)G)`、sparse read/write `O(kBG)`、`B≤96`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機は未検証。

## 系列D固有の進展

1. Episodic raw trace
2. Object/relation trace分離
3. Alias/bridge transport
4. Query consequence matrix
5. Query/object/relation endpoint分離
6. **Value endpointの独立形成**
7. Three-factor binding
8. Slow reconsolidation
9. Sparse indexed retrieval
10. Episodic-to-semantic consolidation

今回、第6段階は誤読抑制へ限定信号を示したが、第7・8段階は失敗した。

> object・relation・valueを別endpointへ分けると誤読経路を減らせるが、value endpointがsurface contextごとに分裂するとsupportが集約されず、slow memoryは一件も形成されない。安定化の前に、異なるsurface value mentionを同じ局所state changeへ結び付けるvalue equivalenceが必要。

## 他系列へ返す知見

- A: active queryでendpointを絞る前に、value endpointのcross-surface equivalenceを生成する必要がある。
- B: filler nonterminalはvalue endpoint候補として有望だが、read query側relation endpointとの双方向利用を監査する必要がある。
- C: transport mapはobject/state correspondenceだけでなく、value mentionとstate changeの対応を独立生成すべき。
- E: basin birthでvalue候補を作った後、複数surfaceから同一state changeへ収束するかをslow credit条件にする。

## 次の仮説

**Value-Change Equivalence Classes from Cross-Surface Write Consequences**  
（surface横断write consequenceからのvalue-change同値類）

1. command内value候補とbefore→after変化区間を二部graph化
2. 異なるsurface commandで同じ局所state changeを作るvalue候補だけ同値類化
3. object/relation endpointは固定せず、value consequenceだけ先に再固定化
4. write成功・non-target保存・inverse readを独立credit化
5. 一回提示ではfast value edgeを即利用
6. 複数session支持後にslow value classへ昇格
7. slow value class形成後だけobject×relation bindingへ結合
8. value classのopen-set recall、one-shot、干渉後latest-value recallを主評価化

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
