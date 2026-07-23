# 系列D Cycle 016 研究報告

## 仮説

**Factorized Object/Relation Address Traces from Independent Counterexample Axes**  
（独立反例軸からの因子化object/relation address trace）

Cycle 015では、object・relation・value・write・readを一つのraw span共通部分から同時に作り、216 eventを平均2.67 nodeへ過剰統合した。既知write 0.0201、read 0、one-shot 0であり、write/read双方向性を同一nodeへ入れるだけではmemory addressにならなかった。

本Cycleではobject traceとrelation traceを独立に形成した。

- object軸: state / command / queryでの再出現、直前focus、rename候補、別object非干渉
- relation軸: before/after局所差分、command value context、relation-specific query、同一object別relation非干渉
- address: object trace × relation traceのうち、raw write executionが観測afterを再現した組だけ局所生成
- slow schema: 最大64 addressへ制限し、局所信頼度で選択的保持

## 先行研究整理

- RealMem (ACL 2026) は2,000超のcross-session project dialogueで、現在のmemory systemが動的project stateとcontext dependencyに苦戦すると報告する。
- RHELM (Microsoft Research, 2026) は現実的・異種・時間発展memoryで、multi-source aggregationとcontext reasoningが主要な弱点だと示す。
- 2025–2026年のhippocampal barcode modelは、疎なevent indexが相関経験間の干渉を減らし、content representationが柔軟なretrievalを補うという分業を示す。
- HiCL (AAAI 2026) はtop-k sparse pattern separation、episodic associative memory、prototype routing、prioritized replayを組み合わせる。
- episodic-to-semantic consolidation研究は、圧縮とidentity/information integrityを分け、provenance付きsemantic layerを独立保持する方向を示す。

これらは疎なindexとcontent/addressの分離を支持するが、多くはencoder・task prototype・既定memory itemを前提とする。生の日本語からobject/relation traceを創発する課題は未解決である。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | D候補との重複判定 |
|---|---|---|---|---|
| A | cross-world localityによるprobe graph | marked条件のsurgery libraryを高速化 | unmarked候補生成0、破壊量偏重 | 外部観測policyは棄却 |
| B | separable intervention subspaceのprogram role | rank basisでprogram/basis削減 | seen 0.2222、role非識別 | program商形成は棄却 |
| C | rank増加outcomeによるidentity basis | 既知局所更新1.0 | 未知形式0、non-target差0 | world object node形成は棄却 |
| E | raw outcome圧縮による残差basis | 既知basis routing回復 | residual/edge basis供給、unmarked0 | energy cause形成は棄却 |
| **D** | **object traceとrelation traceの独立形成・局所address結合** | 今回検証 | write/read address・継続学習 | 系列固有 |

継承知見:
- A: partition gainやsurvivalだけでは意味的probeにならない。
- B: 数値rank増加だけではobject/relation/value roleを識別しない。
- C: non-target preservationが候補classを分割しない場合、identity証拠にならない。
- E: 固定axis間の対応学習とaxis自体のopen-set生成を分ける。

## 実験条件

- event数: 24 / 72 / 216
- seed: 1 / 7 / 19
- object候補: 8 canonical object + rename surface
- relation proxy: 3種類
- split: seen / held paraphrase / rename / alternate state / subject omission / long distractor / combined
- probes: one-shot / 50件干渉後write-read
- ablation: episodic full replay / joint address / factorized / contrastive factorized

学習器はraw `before / command / after / query`文字列と順序のみを使用する。hidden object / field / valueは評価器専用。

## 最大216 event・3 seed平均

### Write accuracy

| 条件 | Episodic | Joint | Factorized | Contrastive |
|---|---:|---:|---:|---:|
| seen | 0.9306 | **1.0000** | 0.0633 | 0.0633 |
| held paraphrase | 0.9306 | **1.0000** | 0.0448 | 0.0448 |
| rename | 0.9645 | **1.0000** | 0.0540 | 0.0540 |
| alternate state | 0.9306 | 0.3349 | 0.0093 | 0.0093 |
| subject omission | 0.4336 | 0.3164 | 0.0201 | 0.0216 |
| long distractor | 0.9198 | **1.0000** | 0.0648 | 0.0648 |

### Read accuracy

| 条件 | Episodic | Joint | Factorized | Contrastive |
|---|---:|---:|---:|---:|
| seen | 0.2500 | **0.5833** | 0.3472 | 0.3472 |
| held paraphrase | 0.2500 | **0.7083** | 0.1528 | 0.1528 |
| rename | **0.3056** | 0.2917 | 0.1806 | 0.1806 |
| alternate state | 0.2639 | 0.0833 | 0.0694 | 0.0694 |
| subject omission | 0.1667 | 0.1111 | **0.1667** | 0.1528 |
| long distractor | 0.3056 | **0.6528** | 0.3611 | 0.3611 |

## 限定的に得られた信号

Factorized方式はCycle 015のbidirectional node（seen read 0）よりread側を改善し、seen read 0.3472、long read 0.3611となった。

216 episodeをobject trace 8.33、relation trace 8.67、address 8.67、model 16,663 bytesへ縮約した。object軸とrelation軸を一つのraw span intersectionへ潰さず別traceとして保持することには、read候補形成の限定信号がある。

## 決定的な反証

**中核仮説は強く反証。**

1. Factorized writeはseen 0.0633で、object/relation proposalの大半をrejectした。
2. FactorizedとContrastiveは主要splitで完全に同一で、独立反例軸の増分情報がほぼ0。
3. canonical objectは8種類なのにrename条件でobject traceは30.33へ過分裂。
4. alternate stateではrelation traceが2個、write 0.0093、read 0.0694へ崩壊。
5. Jointのseen/held/rename write 1.0はsurface context executionで、rename wrong-object rate 0.6528、alternate 0.875。
6. one-shot / interferenceの1.0は最終raw current stateとcommandを直接与える局所再実行で、長期address再発見の証拠にならない。
7. object/relation/operation/goal/constraint、複数段落の目的・訂正・因果・計画のopen-set生成は未成立。

## RAG・検索との差

Factorized memoryは局所relation traceを使ってraw stateを書き換えるため、固定文書検索のみではない。しかしreadは保存state上のsurface alias照合であり、semantic reasoningやobject permanenceには到達していない。Episodic baselineは216 episode全文を保存して全走査する検索baselineで、研究成果には採用しない。

## 破滅的忘却と表面暗記の分離

主問題は後から記憶が消える破滅的忘却ではない。seen write 0.0633、renameでobject trace過分裂、alternateでrelation trace消失、contrastive差0であり、支配的失敗はfast trace形成時のaddress proposal誤りとcross-form同値性の欠如である。

## 資源量

- factorized model: 16,663 bytes
- episodic model: 73,038 bytes
- object traces: 8.33
- relation traces: 8.67
- addresses: 8.67
- fast updates: 48.33
- rejected episodes: 202.33 / 216
- training: 0.5251 sec
- inference: 0.2335 ms/query
- Peak RSS: 160,388 KiB（Python runtime込み）
- complexity: proposal `O(L²)`、learning `O(N(Ho+Hr)G)`、sparse address `O(AG)`, `A<=64`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列D固有の進展

memory address形成を次の8段階へ更新する。

1. raw object mention proposal
2. raw relation proposal
3. object trace separation
4. relation trace separation
5. sparse local address binding
6. **cross-form equivalence with provenance-preserving alias links**
7. read/write reconsolidation
8. episodic-to-semantic consolidation

今回は第3～5段階をsurface近似で実装し、read側に限定信号を得た。

> object軸とrelation軸を分けるだけでは足りない。renameや表現変更を別traceへ分裂させず、誤ったalias統合を防ぐprovenance付きリンクが必要である。

## 他系列へ返す新知見

- A: probeはobject軸・relation軸を分けても、cross-form alias linkを作れなければ候補削減に留まる。
- B: tensor role因子には、異なるsurface viewが同一episode provenanceへ戻る制約が必要。
- C: identity basisはrenameを同じnodeへ統合するだけでなく、relation別read edgeを保持する必要がある。
- E: raw cause basis圧縮では、同一原因の言い換え分裂と異原因の誤統合を別残差にする。

## 次の仮説

**Provenance-Gated Alias Links with Reconsolidating Sparse Address Traces**  
（再固定化する疎address traceとprovenance gate付きalias link）

- fast traceはepisode provenanceを保持
- rename・paraphrase候補間に一時alias linkを作る
- alias link経由のwrite/readがtarget queryを改善しnon-target queryを壊さない場合だけ強化
- delayed contradictionでlinkを局所切断
- supportが複数episodeに広がったaddressだけslow schemaへ再固定化
- raw episodeはprovenanceとして少数だけ残し、全履歴走査を避ける

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
