# A Semantic Identity Cycle 011

## Hypothesis

**Nonparametric Alias-Role Inventory Birth from Independent State-Crossing Witnesses**

固定された観測class数を与えず、raw characterを `object / operation / nuisance` のいずれへ割り当てるかを6000候補のversion spaceで保持した。対象・操作には複数aliasを許し、prefix / suffix / interleave / reverse / paragraph / omittedをepisode-local nuisanceとして混在させた。

比較条件はActive、Random、State-static、Outcome shuffle、Alias lesion。2つの独立8-witness集合とseed 1/7/19を使用し、final afterは候補選択・rankingに使用していない。

## Results

| Method | Set1 | Set2 | Intersection | Prospective | Inverse | Unknown order | Paragraph | Omitted | Counterfactual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Active | 1.00 | 1.00 | 1.00 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Random | 5.67 | 3.00 | 1.67 | 0.925 | 0.908 | 0.970 | 0.926 | 0.905 | 0.925 |
| State-static | 4.00 | 3.33 | 1.00 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Outcome shuffle | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Alias lesion | 1.00 | 1.00 | 1.00 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

Strict progress seeds: **0/3**。

## Decision

**上限条件ではraw alias-role inventoryが独立witness集合から再収束した。しかし能力進歩は未認定、G1未達。**

Activeは各独立集合をunique候補へ収束させたが、state-staticでも二集合intersection後の外部能力が1.0となった。したがって本設定ではstate crossingは候補削減効率に寄与しても、最終外部能力の必要条件ではない。

これはidentity/operation割当がtoken共起と有限program familyだけで決まり、before-stateの因果多様性を必要としないbenchmark漏れを示す。

- `state_crossing_is_required_for_raw_role_inventory_birth`: rejected in this benchmark
- Activeのunique reconvergenceは診断であり進歩ではない
- Alias lesion後も1.0であり、alias単体ではなくrole集合として利用される
- Outcome shuffleで全能力0のため外部結果依存はある

残存oracleはbinary state interface、latent role vocabulary、finite candidate sample、unary target interface、既知のlatent semantic function数。正式分類は `finite_role_vocabulary_and_binary_state_upper_bound`。

## Returns

- B: 同一tokenが異なるstateで候補programを分離する反例を必須化
- C: `set-one vs toggle`, `identity vs set-zero` をraw role birth benchmarkへ統合
- D: oracle program vocabularyが残るためmemory eligible unit 0
- E: Active unique化を進歩へ数えず、state-crossingが外部能力差を生むbenchmarkへ修正

## Next

**Raw State-Variable and Program-Family Co-Birth from Observationally Equivalent Token Roles**

state=0で観測同値となるprogram対を含め、raw token role、state variable、operation familyを同時に候補化する。Active state-crossingがRandom / state-static / family shuffle / outcome shuffleを自由日本語、未知語順、inverse、counterfactualで各+0.10以上上回るかを2 domain・3 seedで検証する。

## Resources

- candidates: 6000
- model bytes mean: 18
- peak RSS: 168892 KiB
- runtime: 7.4426 sec / 3 seeds
- estimated ops: O(2*B*H*Q), H=6000, B=8
- 1GB未満: pass
- weak smartphone実機: 未検証
- answer leakage: none
- 高校生級・ネイティブ日本語コミュニケーション・完成: 未達
