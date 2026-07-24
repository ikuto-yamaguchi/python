# D Memory Eligibility Cycle 012

## Hypothesis

**Independent Cross-Expression Causal-Function Reconvergence before Memory Eligibility**

C Cycle 013のsingle-delta unitをそのまま保存対象にせず、語彙・語順・alias・文型が重ならない二つの取得集合から、各表現の4 before-stateに対する完全応答関数を独立に構成した。同じ応答tensorへ再収束する表現対だけをepisode identity候補とした。

比較条件:

- Paired state-complete acquisition
- Random acquisition
- State-static acquisition
- Pair shuffle
- Outcome shuffle
- Conflict acquisition

2 opaque domain、seed 1/7/19。final evaluation afterは取得、候補生成、rankingに使用していない。fast weights、replay、graph、consolidationは未実装。

## 3 seed x 2 domain mean

| Condition | Set1 units | Set2 units | Reconverged | Same unique | Prospective | Inverse | Unknown order | Omitted | Paragraph | Free | Object permanence | Counterfactual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Paired | 8.00 | 8.00 | 10.00 | 0.000 | 0.7721 | 0.6589 | 0.8203 | 0.5000 | 0.8203 | 0.8438 | 0.7321 | 0.7721 |
| Random | 3.50 | 3.50 | 1.67 | 0.167 | 0.3003 | 0.1380 | 0.3333 | 0.0729 | 0.3490 | 0.3698 | 0.2772 | 0.2925 |
| State-static | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Pair shuffle | 8.00 | 8.00 | 10.00 | 0.000 | 0.7721 | 0.6589 | 0.8203 | 0.5000 | 0.8203 | 0.8438 | 0.7321 | 0.7721 |
| Outcome shuffle | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Strict progress: **0/3 seed**. Formal memory eligible units: **0**.

Conflict audit:

- support-disjoint quarantine: 0.0000
- predictive disagreement: 0.6667
- quarantined: 0.6667

## Decision

**中核仮説は反証。能力進歩、G1/G2、正式な記憶資格は未達。**

PairedはRandomよりprospective +0.4718、inverse +0.5208、object permanence +0.4549となった。しかしPairedとPair shuffleは全指標で完全同率である。

応答tensorが一致するだけでは、どの独立表現同士を同じ経験として結ぶべきか決まらない。`id`、特定stateでのset、異なるtargetに対する対称関数が同じtensor orbitへ衝突し、平均10 unitが再収束した。各集合単独または集合間でsame-unique unitは0である。

したがって高いclosed-loop能力は、正しいepisode identityではなく、同一応答tensorを共有する複数unitの集合予測で説明できる。Pair shuffle無影響は決定的反例である。

## Failure classification

- initial semantics failure
- tensor-equivalence collision
- acquisition-unit non-uniqueness
- pair-correspondence irrelevance
- conflict absorption

取得時成功がないためcatastrophic forgettingではない。保存、干渉、保持率、replay、sleep consolidation、selective forgettingは評価対象外で凍結継続。

## Returns

- A: 同じ応答関数だけでなく、target交換時に対応する表現成分だけが交換されるcross-expression witnessが必要
- B: program response tensorにargument-link、goal、causal directionの選択的変換署名を追加する必要
- C: Pair shuffleが能力を維持する候補はepisode identityではない。state-axis/target-link/argument-link shuffleを同時に破る必要
- E: closed-loop高値を記憶進歩に数えず、各取得集合単独のsame-unique再収束とpair correspondence necessityを必須化

## Next hypothesis

**Transformation-Indexed Episode Identity from Cross-Expression Equivariance, not Response Equality**

次は応答tensorの値が等しいだけではunit化しない。target state交換、target identity交換、non-target交換、argument順序、causal direction、goal変更に対し、二表現の予測関数が同じ変換則で共変することを要求する。各独立集合が単独で同じ変換-indexed unitへ一意再収束し、Pair/State-axis/Target-link/Argument-link shuffleで外部能力が各+0.10以上低下する場合だけ記憶資格候補とする。

## Resources

- model bytes mean: 119604.5
- capacity units mean: 10.00
- peak RSS: 113156 KiB
- runtime: 6.2510 sec
- estimated ops: O(2 domains * 3 seeds * U1*U2*F + Q*U*F)
- 1GB未満: pass
- answer leakage: none
- weak smartphone実機: 未検証
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: 未達
