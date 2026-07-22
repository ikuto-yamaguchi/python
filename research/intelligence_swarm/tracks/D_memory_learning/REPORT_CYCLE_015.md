# 系列D Cycle 015 研究報告

## 仮説

**Bidirectional Query-Write Address Nodes with Local Binding Competition**  
（局所binding競合を持つ双方向query-write address node）

Cycle 014ではcross-query damageをwrite schemaへ加えることで既知writeを0.0417から0.1065へ改善したが、readは約0.264のまま変わらなかった。本Cycleではwrite ruleとread retrievalを別機構にせず、raw `before / command / after / query` からobject候補、relation候補、value抽出context、state write edge、query read patternを同時に持つaddress nodeを形成した。

## 先行研究

- HeLa-Mem (ACL 2026) はepisodic graphの共活性とHebbian distillationからsemantic memoryを形成するが、LLM reflectionと既存semantic表現を前提とする。https://aclanthology.org/2026.acl-long.625/
- ACL 2026のdialog memory graph比較は、graphの有無だけでなくmemory constructionとretrieval設計が性能を左右すると分析する。https://aclanthology.org/2026.acl-long.1232/
- 長期対話memoryではnoise accumulation、reasoning degradation、persona inconsistencyが有限context下で問題になる。https://aclanthology.org/2026.acl-long.614/
- 外部memoryでも安定性・可塑性問題は消えず、representationとretrieval organizationへ移る。https://arxiv.org/abs/2604.27003
- context continuityとevent segmentationは単一の予測信号だけでは説明し切れない。https://www.nature.com/articles/s41562-026-02403-w

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | Dでの判定 |
|---|---|---|---|---|
| A | counterfactual outcome active probe | marked seen 1.0、誤確定0 | unmarked candidate recall 0、probe供給済み | 外部観測policyは棄却 |
| B | destruction-vector e-graph | executable seen 0.6222 | quotient 0.1778、未知形式0 | program商形成は棄却 |
| C | identity-selective intervention partition | seen 1.0、36 node | unknown/omission/paragraph 0、ablation差0 | world object形成は棄却 |
| E | residual-cause bipartite attractor | 手書きrouting下seen 0.9778 | routing mapと候補供給、unmarked 0 | energy routingは棄却 |
| D | query-write同一address node | write/read非対称を同一nodeで解く | 今回検証 | 系列固有 |

継承知見:
- A: outcome分割でもproposal failureは救えない。
- B: 実行vectorが同じでもrole同値とは限らない。
- C: known anchorでの局所実行成功はobject permanenceではない。
- E: residualは原因edgeへroutingしなければ誤収束する。

## 実装

学習器が利用するのはraw日本語文字列と順序だけで、hidden object / relation / valueは評価器のみが使用する。

1. stateから長さ2～12のraw span格子を生成。
2. state・command・queryに共通するspanをobject候補とする。
3. state・queryに共通し、changed valueと異なるspanをrelation候補とする。
4. before/after diffとcommand中new span周辺からwrite edgeを形成。
5. query共活性、non-target state damageを局所統計へ蓄積。
6. write/read compatibilityが高い候補だけをnode統合。
7. 推論時に上位2候補marginが小さければ棄権。

比較:
- `episodic`: episode全文の文字類似replay
- `write_only`: queryとの双方向制約なし
- `bidirectional`: query-write node＋局所競合
- `no_competition`: 競合棄権なし

## 実験

- event数: 24 / 72 / 216
- seed: 1 / 7 / 19
- object: 8、relation proxy: 3
- split: seen、held paraphrase、alternate state、subject omission、long distractor、combined、一回提示、50件干渉read
- 外部依存なし、CPU実行

## 最大216 event・3 seed平均

### Write accuracy

| 条件 | Episodic | Write-only | Bidirectional | No competition |
|---|---:|---:|---:|---:|
| seen | 0.8966 | 0.0201 | 0.0201 | 0.0201 |
| held | 0.8966 | 0.0000 | 0.0000 | 0.0000 |
| alternate | 0.8966 | 0.0139 | 0.0139 | 0.0139 |
| omission | 0.4414 | 0.0123 | 0.0123 | 0.0123 |
| long | 0.9151 | 0.0170 | 0.0170 | 0.0170 |

### Read accuracy / abstention

| 条件 | Episodic read | Write-only read | Bidirectional read | Bidirectional abstain | No competition read |
|---|---:|---:|---:|---:|---:|
| seen | 0.2639 | 0.0000 | 0.0000 | 0.5972 | 0.0833 |
| held | 0.2500 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| alternate | 0.2639 | 0.0417 | 0.0417 | 0.2778 | 0.0833 |
| omission | 0.1389 | 0.0833 | 0.0833 | 0.0000 | 0.0833 |

- one-shot: episodic 1.0、bidirectional 0.0
- 50-interference read: episodic 0.6667、bidirectional 0.0

## 判定

**中核仮説は強く反証。**

1. **双方向制約の増分情報が0**: seenでwrite-onlyとbidirectionalのwrite、read、node数、model sizeが同一。query共活性条件は最終候補classを分割しなかった。
2. **216 eventを2.67 nodeへ過剰統合**: 本来8 object × 3 relationに対応するaddress構造から大きく不足し、表面context clusterへ潰れた。
3. **seen write 0.0201、read 0**: 約98%の更新に失敗し、競合で59.72%棄権しても正解0。
4. **競合なしは誤object選択**: read 0.0833へ上がるがwrong-object rate 0.875。競合は誤確定を棄権へ変えただけ。
5. **held paraphraseでnode生成0**: 全216 episodeがrejectされ、write/read 0。三者raw span intersectionが言い換えで崩壊。
6. **one-shot・干渉readとも0**: 少数例学習、継続学習、再固定化は未成立。
7. **episodic baselineは検索方式**: seen write 0.8966だが216 episode全文を約72KB保存し、queryごとに216件を読む。readは0.2639でsemantic consolidationではない。

## RAG・検索との差

AddressNodesはqueryで文書を検索するだけでなくraw stateへwriteし、以後の内部stateを変える。しかし形成nodeは意味addressでなくsurface clusterで、一般的memory reasoningは未成立。Episodic baselineは比較用の全文保存＋文字類似検索であり、採用対象ではない。

## 破滅的忘却と表面暗記

one-shot 0、seen write 0.0201、seen read 0、held node 0、interference read 0である。形成済み知識が後から消える破滅的忘却より前に、address proposal、binding、read/write equivalenceが成立していない。主因は表面暗記と過剰統合。

## 資源

- Bidirectional model: 6,438 bytes
- Episodic model: 72,333 bytes
- Bidirectional nodes: 2.67
- Training: 0.2249 sec
- Query inference: 0.0661 ms/query
- Mean fast updates/write: 2.287
- Mean read candidates: 2.667
- Peak RSS: 159,824 KiB（Python runtime込み）
- 計算量: proposal `O(L²)`、learn `O(NHG)`、write/read `O(HG)`、episode候補上限24

1GB未満・5ms未満は満たすが、弱いスマートフォン実機測定ではなく、能力も成立していない。

## 系列D固有の進展

1. raw mention proposal
2. object候補とrelation候補の分離
3. write edge形成
4. read edge形成
5. bidirectional address equivalence
6. local binding competition
7. episodic-to-semantic consolidation

今回は3～6をraw span共通部分で同時近似したが、1・2が未成立のためsurface clusterへ崩壊した。

> writeとreadを同一nodeへ入れるだけではaddressにならない。object候補とrelation候補が独立に再束縛可能で、互いに異なる反例を持つ必要がある。

## 他系列へ返す知見

- A: shared probe前にobject候補とrelation候補を別proposal空間へ分離しないと全候補が同じoutcomeになる。
- B: program outcome rankはobject-binding軸とrelation-binding軸を分けて測る。
- C: identity basisはrelation-specific queryで同じnodeへ戻るだけでなく、別relation queryで別edgeへ分かれる必要がある。
- E: future-recall residualをobject bindingとrelation bindingへ分けても、候補生成が同じraw span intersectionならrouting差は生まれない。

## 次の仮説

**Factorized Object/Relation Address Traces from Independent Counterexample Axes**  
（独立反例軸からの因子化object/relation address trace）

次はobject-relation nodeを一度に提案しない。

- object trace: rename、主語省略、別relation query、別episode再出現
- relation trace: 同一object上の別field、query言い換え、value置換、非対象relation保存

object traceとrelation traceの直積は、実際にwrite/read outcomeを変える組だけ局所的に作り、全直積を列挙しない。slow schema統合前にobject軸だけ反転する反例とrelation軸だけ反転する反例の双方を要求する。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
