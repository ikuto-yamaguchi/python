# D Memory Eligibility Cycle 009

## 仮説

**Independent-Witness Reconvergence under Episode-Local Syntax and Unknown Arity Support**

C Cycle 010で、全episodeへ固定語順を強制すると真の因果候補が候補空間から消え、episode-local syntax orbitを許すと候補支持が回復することが判明した。本cycleでは、その一度の回復を記憶資格とせず、重複しない二つのwitness集合が同じmapping・arity・argument linkへ独立再収束するか、矛盾取得を上書きせず隔離できるかを監査した。

## 設定

- seed: 1, 7, 19
- operation: zero/unary/binaryを含む4種
- surface form: prefix / suffix / interleave / reverseをepisodeごとに変動
- 初期候補: 6,912
- 第一witness集合5件、重複しない第二集合5件
- Active / Random / arity shuffle / conflict outcome
- final評価はbefore + commandのみ
- fast weights、replay、sleep consolidation、forgetting最適化は不使用

## 結果

| 指標 | Active | Random |
|---|---:|---:|
| 第一集合残存候補 | 1.0000 | 2.3333 |
| 第二集合残存候補 | 1.0000 | 2.3333 |
| 同一unique候補へ再収束 | 1.0000 | 0.3333 |
| 独立集合intersection | 1.0000 | 1.0000 |
| Prospective closed-loop | 0.9688 | 0.9688 |
| Inverse | 1.0000 | 1.0000 |
| Repair | 0.9323 | 0.9323 |
| Mixed-order | 0.9681 | 0.9681 |
| Counterfactual | 0.9583 | 0.9583 |

矛盾witness集合と正常な第二集合のintersectionは全seedで0となり、取得競合検出率は1.0だった。arity shuffleではprospective 0.5156、inverse 0.5365、repair 0.4740まで低下した。

## 判断

**独立再収束の上限監査は支持。ただし正式なmemory eligibilityと能力進歩は未認定。**

Activeは3/3 seedで、重複しない二集合を同じunique候補へ収束させた。Randomもintersectionとして真候補を残したためclosed-loop能力は同等だが、各集合単独では余分な候補を残した。したがってActiveの価値は能力向上ではなく、一意な再同定に必要なwitness効率にある。

一方、この実験はopaque対象文字集合、opaque操作文字集合、operation family、arity候補multisetを与えている。raw自由日本語からsegmentation・factorization・arityが創発した結果ではない。よってformal memory eligible unitは0、失敗分類は `oracle_to_raw_grounding_gap` とする。

## 保存研究

G1未達のため、fast weights、replay、sleep consolidation、selective forgetting、latest/obsolete競合、長期干渉保持、容量最適化は凍結継続。

## 他系列への返却

- A: 同一意味に単一global語順を要求せず、独立witness集合ごとに局所syntax orbitを保持する。
- B: operation記憶資格にはarity shuffleでforward/inverse双方が選択的に崩れることを要求する。
- C: episode identity候補は、重複しないwitness集合で同じmapping・arity・argument linkへ再収束する必要がある。
- E: oracle上限では3/3再収束したが、formal eligibilityは0。stage遷移根拠にはしない。

## 次

**Independent-Witness Raw Segmentation–Arity Reconvergence without Character-Class Oracles**

対象文字集合・操作文字集合・operation familyを外し、raw utteranceの複数segmentation/factorization候補を二つの独立witness集合が同じ構造へ再収束させられるか監査する。片方だけで成立する構造、boundary shuffle、factor shuffle、arity shuffle、outcome shuffleを拒否する。

## Resources

- model: 78 bytes（surviving candidate）
- candidate: 6,912
- peak RSS: 110,736 KiB
- runtime: 12.3504 sec / 3 seeds
- estimated ops: O(2 × B × H × Q), B=5, H=6,912
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

高校生級知能、ネイティブ日本語コミュニケーション、完成はいずれも未達。
