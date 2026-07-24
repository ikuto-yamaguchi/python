# D Memory Eligibility Cycle 010

## Hypothesis

**Independent State-Crossing Reconvergence before Operation Memory Eligibility**

系列C Cycle 011は、同じ操作tokenを単一初期状態で観測するだけでは `set-to-one` と `toggle`、`noop` と `set-to-zero` が観測同値になることを示した。本サイクルは、一度のstate-crossing同定を即座に記憶資格へ昇格せず、独立した二つのwitness集合が同じ因果programへ再収束するか、矛盾取得を既存identityへ上書きせず隔離できるかを監査する。

fast weights、replay、graph、assembly、sleep consolidation、選択的忘却は実装しない。

## Setup

- opaque operation token: 3
- candidate unary programs: `const0`, `const1`, `identity`, `negation`
- injective token-to-program worlds: 24
- Correct: 各tokenをbefore=0/1の双方で観測する6 witnessを、episode identityの異なる二集合で独立取得
- Random: 各集合6件をtoken/beforeから復元抽出
- State-static: before=0だけを反復
- Conflict: 第一集合の1 outcomeを反転し、正常第二集合とのunionを監査
- seeds: 1, 7, 19
- final capabilityは候補worldだけから計算し、final outcomeをselection/rankingへ使用しない

## Results

| 指標 | State-crossing | Random | State-static |
|---|---:|---:|---:|
| 第一集合 survivor | 1.00 | 2.33 | 4.00 |
| 第二集合 survivor | 1.00 | 2.33 | 4.00 |
| 二集合 intersection | 1.00 | 1.67 | 4.00 |
| 同じunique programへ再収束 | 1.00 | 未達 | 0.00 |
| Prospective | 1.0000 | 0.9444 | 0.7778 |
| Program mapping | 1.0000 | 0.8889 | 0.5556 |

Conflict audit:

- 矛盾第一集合 survivor: 0.33
- 矛盾集合 + 正常第二集合 survivor: 0.00
- 取得競合検出率: 1.00

## Decision

**上限監査仮説は支持する。ただし能力進歩、G1、G2、正式なmemory eligibilityは未達。**

独立したstate-crossing witness集合は3/3 seedで同じunique causal program mappingへ再収束し、state-static集合は二集合を重ねても4候補を残した。したがって、同じtokenを複数回見ることではなく、異なる初期状態を横断して同じ応答関数を再同定することが、operation episodeを同じ記憶対象とみなす必要条件である。

矛盾取得は全seedでversion-space conflictとして検出でき、既存identityへの上書きを拒否できた。

しかし本実験は以下をoracleとして与える。

- operation token境界
- binary state interface
- unary scope
- 4関数からなる有限program family
- target/state variableの観測形式

したがって、生の自由日本語から操作・状態変数・作用域が創発した結果ではない。正式分類は **state_crossing_operation_eligibility_upper_bound / oracle_to_raw_grounding_gap**。formal memory eligible unitは0であり、保持失敗や破滅的忘却ではなく、raw semantic acquisition未成立である。

## Cross-track returns

- **A**: 同一表現の反復ではなく、初期状態交換後にも同じ対象・変数identityが維持される反例を必須化する。
- **B**: `set-one vs toggle`、`noop vs set-zero`を状態横断で分離し、operation family自体をraw発話からbirthする必要がある。
- **C**: scope/arity birthではstate crossingとnon-target preservationを同じ独立witness集合で満たすこと。
- **E**: memory資格に独立state-crossing再収束とconflict quarantineを追加する。ただしoracle上限を進歩へ数えない。

## Next hypothesis

**Independent Scope–Arity Reconvergence from State-Crossing and Non-Target Preservation Witnesses**

unary scopeを外し、単一target作用、二対象関係作用、non-target破壊、argument-order交換を含む候補programを、重複しない二つのwitness集合が同じscope/arity/programへ再収束できるか監査する。operation familyやarity multisetをoracleで与える限り正式資格は0とする。

## Resources

- model upper bound: 576 bytes
- peak RSS: 160,644 KiB (Python runtime included)
- runtime: 0.0017 sec / 3 seeds
- candidate worlds: 24
- estimated probe evaluations: 864
- update: candidate elimination only, <=24 checks/witness
- 1GB未満: 達成
- weak smartphone実機: 未検証
- answer leakage: なし

## Status

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- Formal memory eligibility: 未達
- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: 未達
