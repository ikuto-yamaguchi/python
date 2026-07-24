# C Causal Grounding Cycle 013

## Hypothesis

**Cross-Expression Paired Intervention Equivalence from Mutual Predictive Repair**

A PR #402で同一表面commandを共有するpaired difference quotientがRandom以下、B PR #403でfactor別paired token differenceが外部能力0だったため、pair両側の語彙・語順・局所n-gramを共有しない二表現が、同じtarget/non-target介入に対する予測誤差を相互修復できる場合だけ因果unit候補を形成する仮説を検証した。

## Design

- 完全語彙非共有domain: d1 / d2
- seed: 1 / 7 / 19
- raw Japanese whole utterance
- 4 operation × 2 target × binary two-state world
- canonical / reverse / omitted / paragraph / free
- sparse character 2/3-gram
- paired / random / state-static / pair-shuffle / outcome-shuffle
- final afterはcandidate生成・rankingへ不使用
- fixed ontology / handwritten slot / graph / tensor / RAG / external LLMなし

unitは、表面overlapが低い二表現が同じ外部transition signatureを予測した場合だけ生成した。

## 3 seed × 2 domain mean

| Condition | Units | Prospective | Inverse | Unknown order | Omitted | Paragraph | Free | Object permanence | Counterfactual | Abstention |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Paired | 22.33 | 0.2500 | 0.0703 | 0.0000 | 0.0000 | 0.5000 | 0.0000 | 0.1667 | 0.2500 | 0.5000 |
| Random | 27.33 | 0.1953 | 0.0625 | 0.0000 | 0.0000 | 0.3906 | 0.0000 | 0.1458 | 0.1953 | 0.5729 |
| State-static | 7.50 | 0.1354 | 0.0547 | 0.0000 | 0.0000 | 0.2708 | 0.0000 | 0.1042 | 0.1432 | 0.6589 |
| Pair shuffle | 13.67 | 0.2240 | 0.0443 | 0.0000 | 0.0000 | 0.4479 | 0.0000 | 0.1528 | 0.2318 | 0.5286 |
| Outcome shuffle | 19.17 | 0.1823 | 0.0625 | 0.0000 | 0.0000 | 0.3646 | 0.0000 | 0.1250 | 0.1823 | 0.6042 |

Strict progress: **0/3 seed**.

## Decision

**中核仮説は反証。能力進歩なし、G1/G2未達。**

PairedはRandomよりprospectiveで+0.0547、paragraphで+0.1094だったが、inverseは+0.0078、object permanenceは+0.0208に留まった。未知語順、主語省略相当、自由表現は全方式0である。Pair shuffleもprospective 0.2240、counterfactual 0.2318とPairedへ接近しており、paired対応の因果必然性は弱い。

低表面overlapかつ同じtransition signatureという条件だけでは、同じ因果単位ではなく、異なるoperation/targetが偶然同じ局所deltaを持つ場合を統合してしまう。特に`id`、既に1の状態への`set1`、既に0の状態への`set0`は同じzero deltaとなり、causal direction・program identity・target identityが失われた。

## Falsification and diagnosis

- `same transition signature across disjoint expressions implies same causal unit`: **rejected**
- cross-expression化だけではsurface-shared failureを解消しない
- transition deltaは介入前状態に条件付けないとprogramを同定しない
- mutual repairは必要性監査にはなり得るがbirth原理ではない
- candidate unit数、低surface overlap、paragraph改善は診断であり進歩ではない

## Returns

### A

同一identity候補には、単一delta一致ではなく、複数before-stateにわたる**応答関数全体の一致**と、別target交換時の選択的不変性が必要。zero-delta観測同値反例を必須化する。

### B

operation候補は`id / set0 / set1 / toggle`を、state crossing、target交換、non-target保存で分離しなければならない。factor別pair差分だけでroleをbirthしない。

### D

取得時に再同定可能なepisode unitは0。保存・干渉・忘却研究は再開不可。

### E

AF-013のpaired intervention basisは反例設計として継続可能だが、`cross-expression same-delta mutual repair`は不採用下位仮説。次の最大ボトルネックは、表面非共有表現間で**状態条件付き応答関数と選択的保存則**を同時に再生成すること。

## Next hypothesis

**Cross-Expression Causal Function Equivalence from State-Conditional Response Tensors and Selective Preservation**

表面非共有の二表現について、単一transition deltaではなく、target-state / non-target-state / argument-orderを横断した応答表を独立に推定する。同じ表だけでなく、target交換で対応成分だけが置換され、non-targetが保存される場合に限り因果unit候補を生成する。

Controls: Random, State-static, Pair shuffle, State-axis shuffle, Target-link shuffle, Outcome shuffle. 2 opaque domain × 3 seedでprospective, inverse, object permanence, causal direction, free Japanese, counterfactual repairの全てを+0.10以上要求する。

## Resources

- model bytes mean: 6494.3
- candidate units mean: 22.33
- peak RSS: 159760 KiB
- runtime: 0.4420 sec / 3 seeds × 2 domains
- graph size: 0
- estimated ops: O(P*L + U*Q*V), character 2/3-gram sparse cosine
- under 1GB: pass
- answer leakage: none
- weak smartphone device: not verified
- high-school level: failed
- native Japanese communication: failed
- completion: false
