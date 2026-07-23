# 系列D Cycle 018 研究報告

## 仮説

**Bridge-Episode Alias Equivalence by Reversible State-Trajectory Transport**  
（可逆state trajectory transportによるbridge episode alias同値性）

Cycle 017では、query共起・cross-session provenanceから一時alias linkを提案したが、read/write改善とnon-target preservationを同時に満たすslow linkは0件だった。本Cycleでは、二つのsurface spanを置換したとき、`before / command / after / query` の4 viewがA→B・B→Aの双方で完全にtransportできる隣接bridge episodeだけをalias同値性証拠として使う。

## 先行研究整理

- TiMem (ACL Findings 2026) は時間階層を第一級構造としてraw conversationから上位memoryへ統合するが、semantic-guided consolidationを前提とする。https://aclanthology.org/2026.findings-acl.1091/
- HeLa-Mem (ACL 2026) はepisodic graphとHebbian distillationによるsemantic memoryを分離するが、LLM reflectionがmemory itemを構造化する。https://aclanthology.org/2026.acl-long.625/
- RHELM (Microsoft Research, May 2026) は時間発展・異種情報源のmemoryでmulti-source aggregationとcontext reasoningが主要な弱点だと示す。https://www.microsoft.com/en-us/research/publication/beyond-static-dialogues-benchmarking-realistic-heterogeneous-and-evolving-long-term-memory/
- Memini (arXiv:2605.05097) はfast/slow edge dynamicsで即時利用・強化・忘却を同一機構へ統合するが、graph node/edgeは既に与えられる。
- Episodic-to-Semantic Consolidation Without Identity Drift (arXiv:2607.01988) はprovenance付きsemantic layerを分離するが、field identityは定義済みである。

これらはprovenance・時間階層・fast/slow統合の重要性を支持するが、生の日本語surface間の同値性証拠をどう形成するかは解いていない。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | D候補との区別 |
|---|---|---|---|---|
| A | persistence/change予測による二視点境界birth | 境界・action共同提案を反証 | pair recall 0、junk境界増殖 | 境界探索は扱わない |
| B | 匿名failure-cause商 | 反例符号化を実装 | MDL 6.66倍悪化、未知形式0 | program商・MDLは扱わない |
| C | before/after双方向transportからstate anchor | conditional counterfactual漏れを除去 | transport coverage 0 | world operation形成は扱わない |
| E | responsibility-localized frustration flow | null保持で誤確定抑制 | candidate recall 0 | energy/candidate birthは扱わない |
| **D** | **bridge episodeによるalias同値性とslow reconsolidation** | 今回検証 | 長期memory address | 系列固有 |

継承知見:
- A: candidate recall成立前の誤差creditはfailureを固定する。
- B: episode indexを保存するだけではsemantic consolidationでなく記録量増加になる。
- C: execution failureを因果outcomeへ混ぜず、transport coverageを独立測定する。
- E: candidate absence時はnullを保持し、相対scoreだけで一意化しない。

## 最小実装

学習器入力はraw `before / command / after / query` とsession順序のみ。hidden object/field/valueは評価専用。

1. 近接episodeの4 view間で単一区間差分を抽出
2. A→B置換が4 view全てを再現するforward supportを計測
3. B→A置換が4 view全てを再現するreverse supportを計測
4. 双方向supportを満たすlinkだけread/write候補展開に使用
5. 複数session・複数supportを満たすlinkだけslow link化
6. 全episodeは64件へ上限制限

アブレーション:
- No alias
- Bidirectional bridge link
- Slow reconsolidated link

## 実験条件

- seed: 1 / 7 / 19
- train event: 12 / 24 / 48
- held-out test: 学習とは別seed
- split: seen / held paraphrase / rename / alternate state / combined
- one-shot: 1 episode直後
- interference: bridge 10 event + 24 event干渉

## 最大48 event・3 seed平均

### Write accuracy

| 条件 | No alias | Bidirectional | Slow |
|---|---:|---:|---:|
| seen | 0.6667 | 0.6667 | 0.6667 |
| held | 0.9028 | 0.9028 | 0.9028 |
| rename | 0.6462 | **0.6823** | 0.6823 |
| alternate | 0.6806 | 0.6806 | 0.6806 |
| combined | 0.6555 | **0.6823** | 0.6823 |

### Read accuracy

| 条件 | No alias | Bidirectional | Slow |
|---|---:|---:|---:|
| seen | 0.3750 | 0.3750 | 0.3750 |
| held | 0.2917 | 0.2917 | 0.2917 |
| rename | 0.3333 | 0.2917 | 0.2917 |
| alternate | 0.1667 | 0.1667 | 0.1667 |
| combined | 0.3333 | 0.2917 | 0.2917 |

## 判定

**中核仮説は反証。ただしrename writeに限定信号がある。**

### 限定支持: rename write +0.0361

rename held-out writeはNo alias 0.6462 からBidirectional 0.6823へ約0.0361改善した。combinedでも0.6555→0.6823へ改善した。

これは、4 viewを完全往復transportできるbridgeがsurface aliasを跨ぐ局所write template展開に使えるという限定信号である。

### Readは悪化

rename readは0.3333→0.2917へ悪化し、wrong readは0.7083。bridge linkはobject identityを選んだのでなく、query/stateの表面候補を増やして誤object選択を増やした。

### Slow linkは平均1.67件だけ

rename/combinedでslow linkは平均1.67件。Cycle 017の0件から形成自体は進んだが、能力はBidirectionalと同一であり、slow reconsolidationの追加効果は0。

### Link proposalが過剰

renameで総link 95.67件、combinedで80.67件。真のcanonical-alias組は4組しかない。局所単一区間差分はvalue、状態、文型差もalias候補として大量に混入させる。

### held/alternateへ一般化しない

held・alternateはalias ablationの能力増分0。bridgeは同一trajectoryの完全surface置換に強く依存し、未知言い換え・異state表現の意味同値性を獲得していない。

### One-shot/interferenceは無効な能力証拠

全方式1.0だが、one-shotは同じepisode直後のtemplate再実行、interferenceは「何らかのstateを返せたか」を数える弱い指標である。canonical/aliasが同じ最新field valueへ戻る厳密評価ではないため、長期object permanenceの証拠には採用しない。

### 表面暗記と破滅的忘却の分離

支配的問題は形成済み知識の消失ではない。bridge link形成後もread悪化、held/alternate増分0、slow追加効果0であり、主失敗はalias候補の意味選別とrelation-specific address不足である。

## RAG・検索との差

本方式は保存文書を返すだけでなく、bridge linkを介してwrite templateを別surfaceへtransportし、raw stateを更新する。ただしepisode templateを最大64件保存し全走査するため、現状はsemantic memoryではなく小規模episodic transducerに近い。

## 資源量

- Bidirectional model: 25940 bytes
- episodes retained: 64上限
- links: 95.67
- slow links: 1.67
- fast updates: 66.67
- training: 0.001621 sec
- inference: 10.6040 ms/example
- Peak RSS: 111360 KiB（Python runtime込み）
- complexity: bridge `O(NWH)`、read/write `O(EKG)`、`E≤64`

1GB未満は達成。rename推論は10ms超で、弱いスマートフォンCPUの5ms目標は未達。

## 系列D固有の進展

1. Raw mention proposal
2. Object/relation trace separation
3. Sparse address binding
4. Temporary alias proposal
5. Provenance retention
6. Read/write counterfactual credit
7. **Bidirectional bridge transport**
8. Slow reconsolidation
9. Relation-specific alias address
10. Episodic-to-semantic consolidation

第7段階はrename writeへ限定信号、第8段階はlink形成のみで能力増分0。

最大の新知見:

> 完全な双方向trajectory transportは、surface aliasを跨ぐwrite template再利用の必要条件になり得る。しかしobject同値性の十分条件ではない。value・文型差も同じ可逆差分を作るため、relation-specific read/write consequenceでlinkを再反証する必要がある。

## 他系列へ返す知見

- A: persistence候補はsurface往復可能性だけでなく、別relation queryで同じobjectへ戻るかを測る。
- B: failure quotientは可逆transport可能でも、object/value/relationのどのaxisか未識別なら圧縮しない。
- C: latent state anchorには双方向transportに加え、relation-specific intervention consequenceが必要。
- E: reversible birthは削除可逆性だけでなく、別query factorへの誤伝播energyを測る。

## 次の仮説

**Relation-Selective Bridge Links by Cross-Query Consequence Matrices**  
（cross-query consequence matrixによるrelation選択的bridge link）

- bridge linkごとに複数relation queryを実行
- link経由でtarget relationのwrite/readが改善し、non-target relationを保存するか行列化
- object aliasなら複数relationで同一objectへ戻るが、value aliasなら単一relationだけに局在するという反証を使う
- consequence rankを増やすのではなく、target改善・non-target非破壊・null保持の三条件を必須化
- slow schemaには少数のprovenance反例とconsequence matrixのみ保持

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
