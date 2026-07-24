# A Semantic Identity Cycle 009

## Decision

**限定支持。ただし能力進歩は未認定。S1 / G1未達を維持する。**

## Starting state

GOV-009により研究段階は `minimal-witness joint structure identification` へ移行した。bridge 0の完全未知語彙zero-shotは置換対称性により同定不能であり、HF-012として能力gateから凍結された。系列Aの役割は、oracle token境界を外し、raw Japanese上の分節候補と対象・変数orbitを最小外部witnessで共同同定することである。

## Hypothesis

**Minimal-Witness Joint Boundary–Orbit Identification from Raw Concatenated Opaque Commands**

文字境界を与えない5文字のopaque commandについて、全境界位置と左右の役割を列挙し、反復構造だけから4対象・4操作の候補分節を生成する。その後、learnerが選択した3件の外部witnessにより、境界・対象mapping・操作mappingを同じversion spaceで縮約する。

固定ontology、対応辞書、shared ID、RAG、外部LLM、final test outcomeは使用していない。文字区間をsemantic unitとして先に採用して後段選別するHF-001系とは異なり、境界候補は意味資格を持たず、外部witnessで因果mappingと同時に制約される。

## Experiment

- opaque対象token: 4
- opaque操作token: 4
- raw command: 空白なし連結文字列
- 境界: learnerへ非公開
- 初期仮説: 1,152
- witness budget: 3
- seed: 1 / 7 / 19
- 比較: Active / Random / Outcome shuffle
- 評価: 未観測対象×操作組合せ、未知語順、inverse

## Results

| 条件 | 残存仮説 | 未観測prospective | 未知語順 | inverse |
|---|---:|---:|---:|---:|
| Active | 2.00 | 0.6923 | 0.7500 | 0.6923 |
| Random | 2.67 | 0.6154 | 0.6875 | 0.6154 |
| Outcome shuffle | 0.00 | 0.0000 | 0.0000 | 0.0000 |

Active − Randomはprospective / inverseで **+0.0769**、未知語順で **+0.0625**。Active − Outcome shuffleは大きいが、統合司令の進歩条件 `+0.10以上` を満たさない。

Activeのprospectiveは3 seedすべて0.6923で正方向だったが、3 witness後も平均2仮説が残り、一意なsemantic structureへ収束していない。

## Interpretation

### Supported

- oracle境界を外しても、反復するraw character structureと少数の外部結果を共同制約することで、未観測組合せへchanceを超えて一般化できる。
- outcome対応を破壊するとversion spaceが空になり、外部結果が実際にmappingを拘束している。

### Not supported

- Active witness選択はRandomを実質的基準の+0.10以上で上回らない。
- 分節候補の生成には、全commandが「2因子の単純連結」であるという強いsynthetic構造が残る。
- 主語省略、複数段落、自然な自由日本語、可変arity、関係表現は未評価。
- inverseは有限全単射仮説空間の対称性に依存し、raw Japanese上の独立能力とはまだ言えない。

したがって正式分類は **partial raw-boundary identifiability under a two-factor concatenation upper bound** であり、Semantic Identity Birthではない。

## Cross-track returns

- **B:** operation token境界を固定せず、複数の語順・可変arityを含む同一version spaceへ拡張する必要がある。
- **C:** Active selectorの利得が小さい原因を、未被覆factorと残存境界対称性に分解し、最小witness下限を設計する。
- **D:** 残存2仮説のためmemory eligibilityは拒否。独立witness集合で同じ境界・mappingへ再収束するまで保存を開始しない。
- **E:** AF-010は継続可能。ただし単純連結反復だけをraw segmentation birthとみなす下位仮説は上限監査に限定する。

## Next hypothesis

**Independent-Witness Boundary and Variable-Arity Reconvergence from Mixed-Order Raw Utterances**

次は固定二因子連結を外し、同じ意味を持つ発話に、前後入替、余剰語、ゼロ項・単項・二項候補を混在させる。重複しない二つのwitness集合が同じ境界・arity・mappingへ独立収束するかを検証する。

進歩条件は、未使用token・未知語順・主語省略・複数段落・自由日本語・未観測組合せでActiveがRandom / boundary shuffle / arity shuffle / outcome shuffleを各+0.10以上、3 seedすべてで上回ること。

## Resources

- model upper bound: 18,432 bytes
- peak RSS: 110,384 KiB
- runtime: 7.607 sec / 3 seeds
- selector estimate: 18,432 operations / round
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## Status

- Semantic Identity Gate G1: 未達
- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: 未達
