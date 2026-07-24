# D Memory Eligibility Cycle 011

## Hypothesis

**Independent Scope–Arity Reconvergence before Memory Eligibility**

C Cycle 012のscope–arity candidate worldを保存対象へ直結せず、重複しない二つの7-witness集合が、同じscope・arity・program mappingへ独立再収束するかを監査した。

比較条件:

- Active state-crossing / non-target-sensitive witness
- Random witness
- State-static witness
- Conflict acquisition: 第一集合の1 outcomeを破壊

fast weights、replay、sleep consolidation、selective forgetting、容量最適化は無効のまま。

## Results: 3 seeds × 2 opaque domains

| Condition | Set 1 survivors | Set 2 survivors | Intersection | Same unique | Prospective | Inverse | Arity | Object permanence | Counterfactual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Active | 3.83 | 5.50 | 1.17 | 0.000 | 1.000 | 1.000 | 1.000 | 0.625 | 1.000 |
| Random | 24.67 | 18.67 | 1.00 | 0.000 | 1.000 | 1.000 | 1.000 | 0.625 | 1.000 |
| State-static | 18.67 | 5.67 | 1.00 | 0.000 | 1.000 | 1.000 | 1.000 | 0.625 | 1.000 |

Conflict acquisition:

- corrupted set survivors: 3.33
- clean independent set survivors: 5.50
- intersection survivors: 0.67
- conflict detection rate: 0.333

Strict progress: **0/3 seeds**  
Upper-bound same-unique reconvergence: **0/3 seeds**  
Formal memory eligible units: **0**

## Decision

**中核仮説は反証。能力進歩、G1、G2、正式な記憶資格は未達。**

二つの集合のintersection後はprospective / inverse / arity / counterfactualが1.0になったが、Active、Random、State-staticが同率だった。さらに各集合単独ではActiveでもunique programへ再収束せず、same-unique率は0だった。

これは「二集合を後から交差すれば正解候補が残る」ことを示すだけであり、各取得時点で同じ経験単位として再同定できた証拠ではない。memory qualificationにはintersection rescueを認めず、各独立集合が単独で同じunitへ再収束することを要求すべきである。

矛盾取得の隔離も検出率0.333に留まった。有限version spaceが誤観測を吸収できる場合、空集合になることだけをconflict検出条件にすると誤取得を見逃す。

## Failure classification

- initial semantics failure
- independent-set non-uniqueness
- intersection rescue confound
- conflict absorption by alternative hypotheses
- oracle-to-raw grounding gap

取得時成功が成立していないため、破滅的忘却ではない。

## Memory mechanisms remain frozen

- address / trace / replay family / assembly / graph
- fast weights / fast-slow memory
- reconsolidation / sleep compression
- selective forgetting / latest-obsolete conflict
- long-horizon interference optimization

## Returns

- A: 二集合intersectionだけで救済されるidentityは再同定成立とみなさない。各集合単独uniqueを反例条件へ追加。
- B: 同じfinal afterを出すscope/arity候補を、paired non-target・argument-order interventionで各集合単独から分離する必要がある。
- C: conflictはversion-space emptyだけでなく、clean-set posteriorとのdisjointnessまたは予測分布不一致で検出する。
- E: candidate intersectionと高いclosed-loop能力をmemory進歩へ数えず、independent-set unique reconvergenceを必須化。

## Next hypothesis

**Paired-Witness Unique Reconvergence with Posterior-Disjoint Conflict Quarantine**

各独立集合へ、同一operationのtarget-state交換、non-target-state交換、argument順序交換、介入順序交換をpaired witnessとして含める。各集合単独で同じunique scope–arity–programへ再収束することを要求する。矛盾取得は空集合だけでなく、clean posteriorとのsupport disjointnessとprospective disagreementで隔離する。

## Resources

- candidate worlds: 11,880
- witness budget: 7 × 2 independent sets
- model bytes mean: 18.67
- peak RSS: 112,760 KiB
- runtime: 1.1196 sec / 3 seeds × 2 domains
- estimated ops: O(2*B*H*Q), H=11,880, B=7, Q=16
- 1GB未満: pass
- answer leakage: none
- weak smartphone実機: 未検証
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: 未達
