# 系列C Causal Grounding Cycle 009

## 仮説

**Compositional Causal Orbit Identifiability from Minimal Factor-Crossing Witnesses**  
（最小因子交差witnessによる合成的因果orbitの同定可能性）

A PR #382は完全語彙非共有domainでbridge 0件ならsemantic対応が置換対称で同定不能であることを示した。B PR #383は4-way operation orbitが3個の独立witnessで一意化できる上限を示した。

本CycleではC固有に、対象orbitと操作orbitを個別に接地するだけでなく、**未観測のtarget×operation組合せへ反実仮想合成できるために必要な最小外部witness数**を監査した。

## 実験設計

- opaque target token: 4
- opaque operation token: 4
- latent target: 4
- latent transition: 4
- target対応24 permutation × operation対応24 permutation = **576 causal worlds**
- witness: opaque target tokenとopaque operation tokenの組に対する外部結果
- Active: 期待posterior world数を最小化
- Random: 同数witnessを無作為選択
- Outcome shuffle: queryと外部結果の対応を破壊
- budget: 0 / 1 / 2 / 3 / 4
- seed: 1 / 7 / 19
- final評価結果はwitness選択・version-space更新に不使用

評価:
- prospective target×operation
- target単体
- operation単体
- inverse query
- 未観測factor組合せのcounterfactual composition

## 3 seed平均

| Witness数 | Active残存world | Active joint/inverse | Random残存world | Random joint/inverse | Shuffle joint |
|---:|---:|---:|---:|---:|---:|
| 0 | 576.00 | 0.0000 / 0.0000 | 576.00 | 0.0000 / 0.0000 | 0.0000 |
| 1 | 36.00 | 0.0625 / 0.0625 | 36.00 | 0.0625 / 0.0625 | 0.0000 |
| 2 | 4.00 | 0.2500 / 0.2500 | 4.00 | 0.2500 / 0.2500 | 0.0000 |
| 3 | 1.00 | **1.0000 / 1.0000** | 2.33 | 0.5833 / 0.5833 | 0.0000 |
| 4 | 1.00 | 1.0000 / 1.0000 | 1.67 | 0.6667 / 0.6667 | 0.0000 |

Activeは3個のfactor-crossing witnessで576 worldを1 worldへ縮小し、全16 target×operation組合せのprospective、inverse、未観測組合せcompositionを1.0にした。Randomは3 witness時に平均2.33 worldが残り、能力は0.5833だった。

## 判断

**同定可能性仮説は支持した。ただし能力上の進歩ではなく、G1/G2は未達。**

得られた必要条件:

1. 対象4-way orbitと操作4-way orbitが独立permutationなら、同じwitnessで両因子を新規に覆う3回の交差観測により両mappingを一意化できる。
2. 一意化後は、witnessで直接観測していないtarget×operation組合せもfactor compositionにより予測できる。
3. Outcome shuffleではversion spaceが空になり、外部結果対応が因果的に必要である。
4. Random witnessは同じtargetまたはoperationを重複観測し得るため、同じbudgetでも一意化しない。

ただし、本実験は以下をoracleとして与えた上限監査である。

- target tokenとoperation tokenの境界
- unary target/operation factorization
- arity 1
- target/transitionの外部結果interface
- 有限permutation仮説空間

したがって「生の自由日本語から対象・操作・関係が創発した」とは認定しない。A/Bの結果と合わせると、次に必要なのは**segmentation、factorization、arityを同じ外部witnessで共同同定すること**である。

## 他系列へ返す知見

- A: bridge 0のzero-shotを要求せず、最小witness後の未観測表現一般化をG1候補として測る。ただしtoken境界をoracleにしない。
- B: operation単独orbitだけでなく、対象orbitとの交差witnessが未観測compositionを保証する。
- D: oracle factorization下の一意化はmemory eligibilityではない。raw Japaneseから同じfactorizationが再生成されるまで保存最適化を再開しない。
- E: G1/G2 benchmarkを「bridge 0 zero-shot」から「最小symmetry-breaking witness + 未観測token/組合せ/表現への一般化」へ修正する候補証拠。

## 次の仮説

**Joint Segmentation–Arity–Causal Orbit Birth from Minimal Interventional Witnesses**

次はoracle token境界・固定factorization・固定arityを外す。

- raw Japaneseの複数segmentation候補
- unary / binary relation候補
- target / operation / relationのpermutation orbit
- 外部介入結果

を同一version spaceで保持し、Active witnessがどのsegmentation・arity・因果mappingを同時に排除するか検証する。

進歩認定には、接地に使っていない表現・token・factor組合せ、自由日本語、inverse、counterfactual repairでCorrectがRandom／Outcome shuffleを0.10以上上回り、3 seedすべてで成立することを要求する。

## 資源量

- Model upper bound: 4608 bytes
- Peak RSS: 115516 KiB（Python runtime込み）
- Runtime: 0.077350 sec / 3 seeds
- Initial causal worlds: 576
- Estimated max probe simulations: 36864
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 状態

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
