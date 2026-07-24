# 系列D Memory Eligibility Cycle 003

## 統合前提

- Stage: S1 Semantic Identity Birth
- G1 / G2: 未達
- HF-001〜HF-006: 凍結継続
- Dの保存・replay・fast/slow memory最適化: 再開不可
- 参照: PR #357、#358、#359

## 新仮説

**Factorized Identity–Operation Consistency as Memory Eligibility**  
（対象同一性と操作の分離一貫性による記憶資格）

対象と操作をjoint scoreで一括選択すると、一方のsurface信号が他方の誤りを隠し得る。そこでraw Japaneseから、候補中心の関係による対象再同定、prospective deltaによる操作再同定、同じepisode witnessを用いるinverse queryを独立に監査し、未知表現・別domainで全条件を通過したepisodeだけをsemantic memory候補へ昇格する。

介入後trajectory、scar、正解after、identity/operation label、文字区間proposal、文字列retrieval、RAG、外部LLMは使用しない。

## 実装

- raw Japanese全文: signed hashed 1〜4-gram 64次元
- identity channel: candidate-centered relational multiset 32次元
- operation channel: prospective delta 16次元
- identity / operationを別行列で局所外積更新
- 8 target候補と4 operation候補を独立ranking
- inverse queryでは同じidentity + operation witnessから4発話候補をranking
- correct alignmentとidentity/operation独立shuffleを比較

## 3 seed平均

Chance: target 0.125 / move 0.25 / joint 0.03125 / inverse 0.25

| 条件 | Correct target | Correct move | Correct joint | Shuffle joint | Correct inverse | Eligible rate |
|---|---:|---:|---:|---:|---:|---:|
| Held | 0.3000 | 0.3542 | 0.1167 | 0.0750 | 0.3208 | 0.1083 |
| Rename | 0.2750 | 0.2875 | 0.0917 | 0.0583 | 0.2542 | 0.0875 |
| 未知語順 | 0.2958 | 0.3708 | 0.1375 | 0.0750 | 0.2583 | 0.1250 |
| 主語省略 | 0.2833 | 0.3458 | 0.0875 | 0.0250 | 0.2250 | 0.0833 |
| 複数段落 | 0.2917 | 0.3000 | 0.1000 | 0.0958 | 0.3000 | 0.1000 |
| 自由日本語 | 0.2542 | 0.3458 | 0.0833 | 0.0417 | 0.3125 | 0.0833 |
| 別domain | 0.2708 | 0.1833 | 0.0500 | 0.0667 | 0.2625 | 0.0500 |

厳格gateは、各seedでheld/domain jointがshuffleを0.03超上回り、held/domain inverseが0.30超、両domainでeligible episodeが存在することを要求した。

- 厳格gate通過seed: **0 / 3**
- Semantic-memory eligible unit: **0**

## 判定

**監査仮説は支持されたが、能力上の進歩は認定しない。G1未達。保存本線は凍結継続。**

Held、未知語順、主語省略、自由日本語ではjoint accuracyがchanceを上回り、Correctがshuffleを上回る弱い信号がある。しかし別domainではCorrect joint 0.0500に対してshuffle 0.0667で逆転し、move accuracyもchance未満だった。inverseも別domain 0.2625でchance近傍である。

現在のfactorized channelはheld lexical family内で対象relationと方向語を部分的に分離するが、別語彙domainへ再生成可能なidentity-operation unitではない。条件別eligible rateが非ゼロでも、domain横断・inverse・全seed一貫性を同時に通過しないためmemory eligibilityとは認めない。

これは保持失敗ではなく **initial semantics failure** である。取得資格unitが0件のため、干渉、sleep consolidation、selective forgetting、latest/obsolete競合は開始しない。

## 統合知見

- PR #357: pre-treatment relationはtarget選択に必要だが、別domainでCorrect=shuffle。
- PR #358: 四方向contrastは混線診断には使えるがoperation primitiveは未成立。
- PR #359: 座標変換可換性は必要条件寄りだが、別domain jointでCorrect=shuffle。
- 本cycle: identityとoperationを別channelへ分けても、別domainとinverseの同時資格は成立しない。

次に必要なのは保存機構ではなく、同一geometryでidentity / operation / goal / wordingを独立交換し、各因子の変化だけに選択的に応答するepisode-level eligibility witnessである。

## 他系列へ返す知見

- A: held内部分離は可能だが、別domainではoperation channelが崩壊する。語彙置換を越えるlatent transformation witnessが必要。
- B: 記憶可能なoperation条件は、同じidentityでoperation交換に追従し、別domainとinverseの双方でshuffleを上回ること。
- C: episode identityはtarget正解だけでなく、operation、inverse、domain transferを同じpre-treatment witnessで閉じる必要がある。
- E: AF-004は継続可能だが、factorized identity-operation consistencyはG1通過証拠ではない。保存本線の凍結を維持する。

## 資源量

- Model: **12,288 bytes**（float32換算）
- Peak RSS: **113,504 KiB**（Python runtime込み）
- 3 seed総時間: **7.1321 sec**
- Update: 約 **3,072 ops/episode**
- Inference: 約 **20,480 ops/query**
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 次仮説

**Four-Way Counterfactual Episode Eligibility by Selective Factor Response**

同一のpre-treatment geometryに対しidentity、operation、goal、wordingを一つずつ交換し、identity交換でtarget responseだけ、operation交換でdelta responseだけ、goal交換でselection criterionだけが変わり、wording交換では全responseが不変となる選択的応答vectorを、未知表現・別domain・inverseで再生成できるepisodeだけをmemory eligibleとする。

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
