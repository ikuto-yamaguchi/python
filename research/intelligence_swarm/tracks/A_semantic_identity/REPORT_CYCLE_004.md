# 系列A Semantic Identity Cycle 004

## 仮説

**Cross-Lexicon Selective Consequence Consensus from Factor-Specific Counterfactual Episodes**  
（因子別反実仮想episodeからの語彙非共有・選択的結果consensus）

GOV-005 / PR #366 の AF-006 に従い、単一domain平均やgeneric disagreementを意味単位とみなさず、完全語彙非共有の2 domainで同じfactor-selective response / lesion signatureが再現されるかを検証した。

### 根本前提の差

旧HF-007/HF-008のように、座標可換性・因子分離・単一domain平均を意味とみなさない。

- Domainごとに語彙・中核名詞・関係語・操作語・目的語・文型を独立化
- raw Japanese全文と介入前worldだけを使用
- identity / operation / goalの単独counterfactualを負例として局所更新
- Correct / outcome shuffleを比較
- target × move × goal の64候補をprospectiveに選択
- 同じ写像でinverse queryを評価
- response channel lesionの符号が2 domainで一致するか監査

手書きslot、固定ontology、span proposal、文字列検索、RAG、外部LLM、test時afterは使用していない。

## 3 seed平均

Joint chanceは **0.015625**、target 0.125、move 0.25、goal 0.5、inverse 0.125。

### Opaque domain D1

| 条件 | Correct joint | Shuffle joint | 差 |
|---|---:|---:|---:|
| Held | 0.1597 | 0.0347 | +0.1250 |
| Rename | 0.1319 | 0.0417 | +0.0903 |
| 未知語順 | 0.1076 | 0.0521 | +0.0556 |
| 主語省略 | 0.1111 | 0.0174 | +0.0938 |
| 自由日本語 | 0.1875 | 0.0312 | +0.1562 |
| Inverse | 0.2778 | 0.1285 | +0.1493 |

### Opaque domain D2

| 条件 | Correct joint | Shuffle joint | 差 |
|---|---:|---:|---:|
| Held | 0.1285 | 0.0451 | +0.0833 |
| Rename | 0.1458 | 0.0312 | +0.1146 |
| 未知語順 | 0.1042 | 0.0174 | +0.0868 |
| 主語省略 | 0.2188 | 0.0347 | +0.1840 |
| 自由日本語 | 0.0660 | 0.0312 | +0.0347 |
| Inverse | 0.2847 | 0.1111 | +0.1736 |

### Factor lesion

Held jointから各response channelを除去した結果：

| Domain | Baseline | Identity lesion | Operation lesion | Goal lesion |
|---|---:|---:|---:|---:|
| D1 | 0.1597 | 0.1250 | 0.0556 | 0.1042 |
| D2 | 0.1285 | 0.1007 | 0.0451 | 0.0417 |

3 channelすべてで両domainとも能力低下方向となった。特にoperation lesionは両domainで最大級の低下を示した。

## 判定

**限定支持。ただし能力上の正式進歩は未認定、G1未達。**

従来と異なり、2つの語彙非共有domainでprospectiveとinverseのCorrect-shuffle差が同時に形成され、factor lesionの符号も一致した。このため AF-006 の「選択的因果応答consensus」は候補原理として支持される。

しかし統合司令の暫定進歩条件は満たさない。

- D2自由日本語差は +0.0347 に留まる
- D2自由日本語は1 seedで差0
- D1未知語順・D2 Heldも +0.10未満
- domain間で同じlatent unitを直接共有・再生成した証拠ではなく、独立domain内で同符号の能力を得た段階
- goal channelが文面上明示的で、goal accuracyが高くなりやすい
- 弱いスマートフォン実機は未検証

したがって現在の分類は **cross-lexicon factor-selective consequence grounding with incomplete free-form consensus** であり、semantic identity gate通過ではない。

## 新しい発見

1. Generic disagreementではなくfactor-specific counterfactualを負例にすると、2 domainでCorrect-shuffle差が同時に形成された。
2. identity / operation / goal lesionの能力低下方向が2 domainで一致し、単一domain平均より強い証拠になった。
3. 最弱点は第二domainの自由日本語であり、語彙よりも自由文型・談話表現への再生成がボトルネック。
4. Domainごとの独立学習だけでは、同じunitであることを証明できない。次はdomain間で共有語彙を使わず、response orbitそのものの同値性を形成する必要がある。

## 他系列へ返す知見

- **B**: operation channelは両domainで選択的lesion効果が最も強い。実行単位候補は平均精度でなく、factor-specific lesion consensusで選別する。
- **C**: identity / operation / goal counterfactualはgeneric disagreementより有効。次は自由文型だけ変えた介入を増やし、意味因子と談話nuisanceを分離する。
- **D**: 2 domainの平均陽性だけではmemory eligibilityにしない。全seed・自由日本語・inverse・lesion符号一致を同一unit単位で要求する。
- **E**: AF-006は継続候補。HF-008の再開理由にはならず、G1は未達。

## 資源量

- Matrix: **98,304 bytes**
- Peak RSS: **111,280 KiB**（Python / NumPy runtime込み）
- 3 seed総時間: **10.311秒**
- 更新量: 約 **24,576 ops/episode**
- 推論量: 約 **24,576 ops/option × 64 = 1,572,864 ops/query**
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 次の仮説

**Domain-Independent Response-Orbit Unit Birth by Consensus-Gated Nuisance Cancellation**

1. D1/D2のモデルは独立学習のまま維持する
2. identity / operation / goal / wording counterfactualへのresponse vectorを匿名orbit化
3. domain間で同符号・同順位になるresponse channelだけをunit構成に残す
4. wording-only変化へ反応するchannelをanti-Hebbianに除去
5. 一つのdomainを完全に隠し、もう一方のorbit選択規則だけでheld-out domainのchannelを選択
6. 自由日本語、未知語順、inverseで各domain Correct-shuffle +0.10以上、3/3 seedを必須化
7. post-treatment、shared token/template/ID、domain辞書を引き続き禁止

## 状態

- Semantic Identity Gate G1: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
