# 系列C Causal Grounding Cycle 012

## 仮説

**Scope–Arity Program Identification from State-Crossing and Non-Target Preservation Witnesses**  
（状態横断・非対象保存witnessによる作用域・項数program同定）

系列A PR #397ではraw alias-role inventoryが独立witness集合から再収束した一方、state-staticでも最終外部能力が1.0となり、因果状態を横断しなくても解ける評価漏れが確認された。

本サイクルでは、operation identityを単一の局所差分ではなく、複数初期状態とnon-target応答にまたがる関数として監査した。候補空間にはunary/binary programと、target効果は似るがnon-targetを破壊するprogramを混在させた。

## 実験

- opaque domain: d1 / d2
- seed: 1 / 7 / 19
- opaque operation token: 4
- candidate program: 12
- candidate world: 11,880
- witness budget: 7
- initial state: 2 binary variables
- surface forms: plain / reverse / omitted / paragraph / free
- comparison:
  - Active state-crossing
  - Random
  - State-static
  - Arity/program shuffle
  - Outcome shuffle

Final評価のafterはwitness選択・候補rankingに利用していない。

## 3 seed × 2 domain平均

| 条件 | 残存world | Prospective | Inverse program | Arity | Object permanence | Counterfactual |
|---|---:|---:|---:|---:|---:|---:|
| Active | 3.83 | 0.9167 | 0.7083 | 0.8333 | 0.5729 | 0.9167 |
| Random | 24.67 | 0.7917 | 0.6250 | 0.7083 | 0.4792 | 0.7917 |
| State-static | 18.67 | 0.7396 | 0.4583 | 0.7083 | 0.4688 | 0.7396 |
| Arity/program shuffle | 3.83 | 0.3646 | 0.1250 | 0.6667 | 0.5521 | 0.3646 |
| Outcome shuffle | 2.50 | 0.0208 | 0.0000 | 0.1667 | 0.2292 | 0.0208 |

Active−Random:

- Prospective: **+0.1250**
- Inverse program: **+0.0833**
- Arity: **+0.1250**
- Object permanence: **+0.0937**
- Counterfactual: **+0.1250**

Strict progress seed: **0/3**

## 判断

**作用域・項数の因果同定上限として限定支持。能力上の正式な進歩は未認定、G1/G2未達。**

Activeはprospective、arity、counterfactualでRandomを+0.125上回り、State-staticよりさらに大きく改善した。non-targetを破壊するprogramを候補へ追加したため、単一stateの局所差分だけでは候補を除去できず、状態横断とnon-target観測が実際に必要になった。

一方、Inverse programのActive−Random差は+0.0833、Object permanenceは+0.0938で、統合gateの+0.10を満たさない。3 seed全てで全指標を通過するstrict gateは0/3だった。

したがって、今回確認できたのは「scope/arity候補を区別するための反例設計が改善した」という上限証拠であり、生の自由日本語から因果単位が創発した証拠ではない。

## 反証・切り分け

1. **State-staticではprogram familyを一意化できない**
   - 残存world 18.67
   - inverse 0.4583
   - counterfactual 0.7396

2. **Arity/program対応の破壊で能力が崩れる**
   - prospective 0.3646
   - inverse 0.1250
   - counterfactual 0.3646

3. **Outcome shuffleはほぼ全能力を消失**
   - prospective 0.0208
   - inverse 0
   - correct external outcomeへの依存を確認

4. **Object permanenceはまだ弱い**
   - Active 0.5729
   - Random 0.4792
   - non-target保存をより直接的に問うpaired witnessが必要

## 残るoracle

- operation token境界
- binary state interface
- finite program vocabulary
- raw utterance parser
- 4 token / 2 state-variableという有限設定

よって正式分類は `scope_arity_causal_identifiability_upper_bound`。

## 他系列への返却

- **Aへ**: role inventory評価へ、target effectが同じでnon-targetだけ異なるprogram対を必須追加する
- **Bへ**: operation family birthでは、set/toggleだけでなくnon-target破壊、binary relation、argument-order交換を同一候補空間に含める
- **Dへ**: Activeは上限信号を示したがraw parser/state interface oracleが残るためmemory eligible unitは0
- **Eへ**: state-crossingは有望だが、object permanenceとinverseが+0.10未満のため段階遷移証拠には不足

## 次の仮説

**Minimal Paired Intervention Sets for Joint Scope, Argument-Link, and Causal-Direction Birth**

次は単発probeではなく、同一operationについて以下を対にした最小witness集合を選ぶ。

- target stateのみ交換
- non-target stateのみ交換
- argument順序交換
- intervention順序交換
- unary/binary candidateの予測分岐
- causal direction reversal

2以上のopaque domain・3 seedで、ActiveがRandom / State-static / Arity shuffle / Argument-link shuffle / Outcome shuffleをprospective、inverse、object permanence、causal direction、counterfactual repairで各+0.10以上上回るか検証する。

## 資源

- candidate world: 11880
- survivor model: 平均 27.17 bytes
- Peak RSS: 160140 KiB
- 3 seed × 2 domain runtime: 1.0141 sec
- estimated ops: O(B*H*Q), H=11880, B=7, Q=16
- 1GB未満: 達成
- answer leakage: なし
- weak smartphone実機: 未検証
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: 未達
