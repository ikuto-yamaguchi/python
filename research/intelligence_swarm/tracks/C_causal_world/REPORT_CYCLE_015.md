# 系列C Cycle 015 研究報告

## 仮説

**Identity-Selective Intervention Partitions with Null Object Nodes**  
（帰無object nodeを持つ対象選択的介入分割）

Cycle 014では、時系列focus・clause anchor・介入trajectoryから288介入を平均3.67 nodeへ圧縮したが、全split精度0だった。trajectory clusterはobject identityではなかった。

本Cycleでは、学習時のraw before/command/afterから局所node候補を形成し、推論時には各nodeを状態中の複数clauseへ再適用する。target clauseだけを変更し、非対象clauseを壊さない候補を優先し、説明不能または同率の場合はnull objectへ棄権する。

## 先行研究整理

2025年のcausal abstraction識別研究は、before/after介入対から潜在因果構造を識別できる粒度が、介入集合のcoverageに依存することを示す。2025年のscore-based CRLでは一般変換下で各nodeへの複数介入が識別性に必要とされる。2025年のobject-centric temporal contrast研究は時間的一貫性制約がobject discoveryを改善する一方、slot表現自体は強い視覚encoderから得ている。2026年のCausal-JEPAもobject-level latent interventionがcounterfactual推論を改善するが、object候補は既に供給済みである。

- https://proceedings.mlr.press/v258/li25g.html
- https://www.jmlr.org/papers/v26/24-0194.html
- https://openaccess.thecvf.com/content/CVPR2025/html/Manasyan_Temporally_Consistent_Object-Centric_Learning_by_Contrasting_Slots_CVPR_2025_paper.html
- https://arxiv.org/abs/2602.11389

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | C候補との判定 |
|---|---|---|---|---|
| A | causal outcomeによるactive probe | marked seen 1.0 | unmarked candidate recall 0 | 外部probe policyは棄却 |
| B | destruction-vector e-graph | executable seen 0.6222 | quotient 0.1778、未知表現0 | program quotientは棄却 |
| D | cross-query write/read address | writeを0.0417→0.1065 | read約0.264、schema細分化 | memory addressは棄却 |
| E | residual-cause bipartite routing | 手書きroutingでseen 0.9778 | routing自己誘導・candidate proposal未成立 | energy routingは棄却 |
| C | identity-selective intervention partition | 今回検証 | open-form identity proposal | 系列固有 |

継承知見:
- A: outcomeで候補を分けても候補集合外は救えない。
- B: 実誤適用はsurface riskより増分情報を持つ。
- D: write成功とread addressは別能力。
- E: 残差は原因edgeへ局所帰属しなければならない。

## 実験

- train: 48 / 144 / 432 episode
- test: 120例/split/seed
- seed: 1 / 7 / 19
- 3 relation proxy、最大3 clause
- 比較: surface replay / partition / non-target selective / selective+null
- split: seen、未知言い換え、別状態表現、主語省略、複数段落、計画変更
- learner入力: raw Japanese before/command/afterと順序のみ
- hidden object/field/valueは評価専用

## 最大432学習例・3 seed平均

| 条件 | Surface | Partition | Selective | Selective+Null |
|---|---:|---:|---:|---:|
| seen | 0.9750 | 1.0000 | 1.0000 | 1.0000 |
| held paraphrase | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| alternate state | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| subject omission | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| paragraph | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| plan change | 0.0139 | 0.0000 | 0.0000 | 0.0000 |

## 判定

**中核仮説は反証。**

### 限定的に支持された部分

seen制御条件ではpartition方式が1.0、モデル約4.95KB、推論約0.021ms/exampleで、432 episodeを36局所nodeへ縮約した。対象anchorと局所write boundaryが既知形式に一致する場合、対象選択的clause更新を軽量に再実行できる。

### 決定的な失敗

1. 未知言い換え・別状態表現・主語省略・複数段落は全て0。nodeは意味的objectではなく既知command/state contextの表面組である。
2. non-target selective ablationはpartitionと全accuracyが同一。非対象damageは最終候補classを一つも分割せず、増分情報0。
3. nullは未知条件を全面拒否するだけで、object proposal failureを修復しない。
4. 計画変更は0。後続の撤回・最終goalを解析せず、最初に一致したvalue contextを使う。
5. seen 1.0は学習済み形式と同じclause構造の制御条件で、object permanence・因果理解の証拠ではない。
6. Surface replayのseen 0.975は432 episode全文を約129.5KB保存する文字類似検索で、採用不能。

重要な否定結果:

> 対象選択的な誤適用を実行しても、候補object anchorとrelation boundaryが表面context由来なら、既知形式の局所編集器に留まる。non-target preservationは、候補間で異なる破壊結果を生まない限りobject identityを識別しない。

## 相関暗記と因果理解の反証条件

- 既知形式のみ成功し、paraphrase/alternateで0ならsurface correlation。
- target/non-target surgeryを外したablationと同じなら因果選択性なし。
- rename・主語省略で同一nodeへ戻れなければobject permanenceなし。
- order/plan changeで結果が変わらなければevent/goal dynamicsなし。
- nullが全面拒否するだけならopen-set理解なし。

今回、すべて因果理解側の条件を満たさなかった。

## 資源量

- selective model: 4951 bytes
- node: 36
- training: 0.0110 sec
- inference: 0.0203 ms/example
- mean candidates: 1.142
- Peak RSS: 111588 KiB（Python runtime込み）
- complexity: learn `O(NQG)`, infer `O(HCG)`, `C<=3`

1GB未満・5ms未満は満たすが、弱いスマートフォン実機では未検証。

## 系列C固有の進展

object形成を次の7段階へ更新した。

1. raw mention/object proposal
2. local intervention executability
3. identity-selective non-target outcome partition
4. null object calibration
5. rename・主語省略でのtemporal rebinding
6. relation-bearing edge接続
7. event・goal・order planning

今回は既知形式で2を成立させた。3はablation差0、1・4～7は未成立。

## 他系列へ返す新知見

- A: outcome probeは、候補classを実際に分割するtarget/non-target差がなければ取得しない。
- B: destruction vectorが同一の候補をさらに圧縮してもroleは創発しない。object proposalの独立ゲートが必要。
- D: memory addressは既知surface anchorではなくrename・省略後も同じnodeへ戻る必要がある。
- E: non-target preservation残差が候補edge間で差を持たない場合、cause nodeへ昇格させるべきでない。

## 次の仮説

**Cross-Episode Identity Basis Discovery by Rank-Increasing Intervention Outcomes**  
（rank増加介入outcomeによるepisode横断identity basis発見）

固定のtarget/non-target probeを増やさない。候補object spanの削除・再束縛・rename・focus継承を実行し、episode横断outcome matrixのrankを増やし、かつ同じ候補分割を再現する介入だけをidentity basisへ追加する。rankを増やせない候補は同値のまま保持し、無理にobject nodeへ統合しない。

最低成功条件:
- held / alternate / omittedのいずれかを0から改善
- selective ablationとの差を明確化
- node 3～24
- 32KB未満
- 5ms/example未満

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
