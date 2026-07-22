# 系列D Cycle 014 研究報告

## 仮説

**Object-Relation Address Discovery by Cross-Query Write/Read Invariance**

Cycle 013では216 episodeを約9 schemaへ圧縮した一方、既知write 0.0633、read 0.0417まで崩壊した。今回はraw `before / command / after / query` から局所write ruleを作り、非対象stateと複数raw queryへの再適用で得たtarget-query gainとnon-target damageをschema統合条件へ加えた。

## 先行研究

- 2025年のlifelong dialogue memory研究は、固定粒度・固定retrievalでは長期変化を扱えず、時間・因果linkやforward/backward reflectionが必要と報告している。
- episodic/semantic memoryのadaptive compression論は、記憶を逐語保存でなく環境規則の学習・圧縮として扱う一方、驚きや環境変化を捨てない必要性を指摘する。
- associative memoryの局所可塑性研究は、自律rehearsalで相関記憶を継続追加する可能性を示す。
- 2026年のmulti-timescale memory案はfast/slow edge dynamicsによるepisodic sensitivity、consolidation、forgettingの統合を提案する。

ただし、これらは強いencoder、定義済みmemory item、既存表現を前提とし、生の日本語からobject-relation addressを形成する問題を直接解かない。

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | Dでの判定 |
|---|---|---|---|---|
| A | 因果outcomeを持つactive probe | feedback修復の下流信号 | candidate recall・semantic probe | 外部観測policyは棄却 |
| B | clause-lattice実誤適用 | 既知0.0633→0.2533 | MDL商で0.0967 | program induction自体は棄却 |
| C | intervention persistence object node | 時系列identityを検証 | 288介入を3.67 nodeへ過剰統合、精度0 | world object形成は棄却 |
| E | residual-cause二部attractor | 矛盾routing方針 | residual identifiability未成立 | energy relaxationは棄却 |
| D | cross-query write/read address | read-side非干渉を統合条件化 | 今回検証 | 系列固有 |

継承知見:
- A: 候補削減・survivalだけでは意味的正しさを保証しない。
- B: 実際の誤適用結果はsurface riskより増分情報を持つ。
- C: object node不在ではsurgeryが表面編集へ退化する。
- E: 候補classを分割しないfactorは無意味。

## 漏洩監査

初回実装では評価用object IDをlive-state辞書の索引に使っていたため、全結果を棄却した。最終実装では学習器・記憶器はraw文字列と順序だけを利用し、hidden object / field / valueはaccuracy算出時だけ使用する。

## 実験

- event数: 24 / 72 / 216
- seed: 1 / 7 / 19
- object: 8、relation proxy: 3
- split: 既知、言い換え、別状態表現、主語省略、長期distractor、combined、一回提示、50件干渉
- 比較: Surface episodic replay / 局所write program / Cross-query invariance付きprogram

## 最大216 event・3 seed平均

### Write accuracy

| 条件 | Surface | Program | Cross-query |
|---|---:|---:|---:|
| 既知 | 0.8966 | 0.0417 | **0.1065** |
| 言い換え | 0.8966 | 0.0556 | **0.1451** |
| 別状態表現 | 0.8966 | 0.0417 | **0.1080** |
| 主語省略 | 0.4414 | 0.0324 | **0.1049** |
| 長期distractor | 0.9151 | 0.0509 | **0.1080** |

### Raw-query address read

| 条件 | Surface | Program | Cross-query |
|---|---:|---:|---:|
| 既知 | 0.2639 | 0.2639 | 0.2639 |
| 言い換え | 0.2639 | 0.2778 | 0.2778 |
| 別状態表現 | 0.2639 | 0.2778 | 0.2778 |
| 主語省略 | 0.1389 | 0.2778 | 0.2778 |

## 限定支持

Cross-query条件は局所Programに対して、既知write 0.0417→0.1065、言い換え0.0556→0.1451、主語省略0.0324→0.1049へ改善した。

したがって、**write ruleを非対象stateと複数queryへ再適用し、read-side破壊をschema scoreへ入れること**には増分信号がある。

## 反証

**中核仮説は反証。**

1. Cross-queryでも既知writeは0.1065。約89%を更新できず、object-relation addressとして利用不能。
2. Read accuracyは約0.26～0.28で改善しない。query similarityがobject表面を拾うだけでrelation-specific latest valueを選べない。
3. Program 6～9 schemaに対しCross-queryは約17～22 schemaへ増えた。意味addressではなくsurface familyを細分化した可能性が高い。
4. Surface replayはwriteで圧勝するが、216 episodeを線形保存する約55KBの表面検索でありsemantic memoryとして採用不可。
5. 一回提示・50件干渉probeは、最終更新時にraw current stateを直接与えるため、長期address再発見の証拠にならず棄却。
6. 主語省略改善もfocus/object nodeを形成した結果ではなく、value周辺文字context一致に限定される。

## RAGとの差

Program方式はraw stateを書き換えて以後の内部stateを変えるため固定文書検索だけではない。ただしreadはraw文字類似で、Surfaceはepisodic nearest-neighbor replayに留まる。一般的memory reasoningは未成立。

## 破滅的忘却と表面暗記

主因は形成済みschemaの時間的消失ではなく、**object-relation addressの誤形成とwrite/read非対称性**である。Cross-queryでwriteは少し改善したがreadは変わらず、schemaは細分化した。

## 資源

- Cross-query model: 6,595 bytes
- Program model: 3,130 bytes
- Surface model: 56,596 bytes
- Cross-query schema: 16.67
- training: 0.1047 sec
- query inference: 2.9088 ms/query
- local rule reads/write: 0.1127
- Peak RSS: 14,904 KiB（Python runtime込み）
- 計算量: learn `O(NPG + NQG)`、write `O(PG)`、read `O(MG)`

1GB未満は達成。弱いスマートフォン実機検証ではない。

## 系列D固有の進展

memory address形成を次へ分離した。

1. Episodic write
2. Local transformation proposal
3. Non-target write damage
4. Cross-query read damage
5. **Bidirectional object-relation address equivalence**
6. Episodic-to-semantic consolidation

今回は3・4をsurface近似で加え、writeに限定的な増分を得た。write後にrelation-specific queryが同じnodeへ戻る第5段階は未成立。

## 他系列へ返す知見

- A: probe utilityはcandidate survivalだけでなく、write後のtarget-query改善とunrelated-query劣化を分離する。
- B: destruction-vector商にはread-side query vectorも必要。write破壊が同じでもread addressが異なる候補を統合しない。
- C: object nodeは介入trajectoryだけでなく、relation-specific queryが同じnodeへ戻ることを要求する。
- E: future-recall residualをobject-binding edgeとrelation-address edgeへ別々にroutingする。

## 次の仮説

**Bidirectional Query-Write Address Nodes with Local Binding Competition**

raw command、state diff、複数queryからobject候補、relation候補、value候補、write edge、read edgeを同時に持つaddress node候補を生成する。commandからtargetへwriteでき、relation-specific queryから同じnodeへ戻り、別object・別relationを吸収せず、paraphraseでも同じoutcomeを生む候補だけをslow schemaへ昇格する。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
