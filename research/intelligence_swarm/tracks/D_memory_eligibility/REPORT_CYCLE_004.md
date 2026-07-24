# 系列D Memory Eligibility Cycle 004

## 仮説

**Lexicon-Disjoint Bidirectional Consequence Consistency as Memory Eligibility**  
（完全語彙非共有domainでの双方向結果一貫性による記憶資格）

PR #363では、結果指紋を用いたB系列の操作接地が別domainでprospectiveとinverseの双方に強いCorrect–shuffle差を示した。ただし、domain間で一部の日本語中核表現を共有しており、そのままsemantic memory資格へ昇格できない。

本Cycleでは、selector・operation語彙を完全に非共有とした2つのopaque domain D/Eを用い、各domain 16件の観測遷移から局所更新した同一方式を監査した。

資格条件は次の同時成立とした。

1. held / 未知語順 / 自由日本語の全条件でCorrect joint > Shuffle joint
2. 全条件のinverse accuracy > 0.20
3. held joint > 32択chance 0.03125
4. seedごとに独立通過
5. 通過後のみ64件の矛盾干渉後保持を意味的retentionとして解釈

post-treatment結果はadaptation観測にのみ使用し、test時には raw Japanese + before world + hypothetical target/move だけを使用した。文字区間候補、固定ontology、共有辞書、RAG、外部LLMは使用していない。

## 3 seed平均

### Opaque domain D

| 条件 | Correct joint / inverse | Shuffle joint / inverse | 干渉後 joint / inverse |
|---|---:|---:|---:|
| Held | 0.0799 / 0.2326 | 0.0278 / 0.1667 | 0.0278 / 0.1597 |
| 未知語順 | 0.0590 / 0.2292 | 0.0451 / 0.1354 | 0.0451 / 0.1736 |
| 自由日本語 | 0.0417 / 0.2118 | 0.0521 / 0.1250 | 0.0347 / 0.1528 |

- 厳格資格通過seed: **0 / 3**

### Opaque domain E

| 条件 | Correct joint / inverse | Shuffle joint / inverse | 干渉後 joint / inverse |
|---|---:|---:|---:|
| Held | 0.1181 / 0.3229 | 0.0243 / 0.0972 | 0.0660 / 0.2188 |
| 未知語順 | 0.0729 / 0.2708 | 0.0278 / 0.0868 | 0.0417 / 0.2257 |
| 自由日本語 | 0.0660 / 0.2743 | 0.0382 / 0.0938 | 0.0347 / 0.1632 |

- 厳格資格通過seed: **1 / 3**

## 判断

**監査仮説は限定支持、能力上の進歩は未認定、G1/G2未達。保存本線は再開しない。**

### 得られた陽性

Opaque domain Eでは、完全に別語彙でもCorrectがshuffleを大きく上回った。

- Held gap: +0.0938
- 未知語順 gap: +0.0451
- 自由日本語 gap: +0.0278
- Inverseも全条件でshuffleを上回った

これはPR #363の信号が共有語彙だけで完全に説明されない可能性を示す。

### 記憶資格には未達

一方、同じ方式でもdomain Dでは自由日本語のCorrect jointがshuffleを下回り、資格seedは0/3だった。domain Eも厳格通過は1/3に留まる。

したがって、現在の結果指紋写像は、語彙非共有domainで再現可能なsemantic unitではなく、少数観測に敏感なdomain-local bindingである。

### 破滅的忘却の扱い

Domain Eでは取得時に明確な平均信号があり、64件の矛盾干渉後に、

- Held joint 0.1181 → 0.0660
- 自由日本語 joint 0.0660 → 0.0347
- Held inverse 0.3229 → 0.2188

へ低下した。

ただし資格通過が1/3 seedのみなので、系列Dの正式分類は**再現性不足を伴う取得不安定**であり、一般的なcatastrophic forgettingとは認定しない。seed 19の通過unitに限定すれば保持低下の候補証拠である。

## 系列D固有の進展

保存構造を追加せず、B系列の最初の有望信号を、

- 完全語彙非共有domain
- 双方向prospective/inverse
- 複数表現一貫性
- seed単位資格
- 取得後干渉

へ分解して監査した。

その結果、**平均能力差だけでは記憶資格にならず、domain間・seed間の再生成可能性を資格条件に含める必要がある**ことが明確になった。

## 他系列へ返す知見

- A: 同じ結果指紋方式でもopaque lexicon D/Eで挙動が分かれる。新unit birthは平均gapではなく、複数独立lexiconで同じ選択的応答を再生成する条件が必要。
- B: PR #363の結果は共有語彙だけではない可能性があるが、完全語彙非共有ではseed依存。結果指紋のどの成分がidentity/operationを支えるか選択的lesionが必要。
- C: domain D/E差を生む最小観測集合と、factor-selective interventionによる識別可能性を監査すべき。
- E: AF-005は継続可能。ただしG1/G2昇格条件へ「2つ以上の独立opaque lexiconで3/3 seed資格」を追加すべき。

## 資源量

- Model: **50,579 bytes/domain**
- Adaptation: **16 records/domain**
- Interference: **64 contradictory records**
- Peak RSS: **165,452 KiB**（Python/NumPy runtime込み）
- 3 seed総時間: **24.612 sec**
- Update: 約**12,288 ops/episode**
- Candidate scoring: 約**1,536 feature ops/query**に加え結果指紋生成
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 次の仮説

**Cross-Lexicon Consensus Eligibility from Shared Consequence Lesion Signatures**

次はdomainごとに独立した全体matrixの平均能力を比較しない。

1. 結果指紋channelを一つずつlesion
2. Opaque D/Eの双方で同じ能力成分だけが選択的に崩れるchannelを抽出
3. 2 domain × 3 seedで同符号のlesion signatureを持つunitだけ候補化
4. prospective / inverse / free Japaneseを同じunitで監査
5. 資格通過後のみfast-weight一回提示と干渉保持を開始

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
