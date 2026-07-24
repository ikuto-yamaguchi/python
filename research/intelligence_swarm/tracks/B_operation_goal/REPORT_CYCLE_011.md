# B Operation/Goal Cycle 011

## 仮説

**Role-Specific Paired Lesion Birth without Enumerated Programs**

HF-014の有限program列挙・posterior intersection救済を使わず、同一before-state内でtarget/source/goal/operationの一要素だけが異なるraw発話pairを抽出し、発話中で変化した匿名token集合とworld transition差を共同対応させた。候補は各pair取得時に生成し、後段intersectionによる救済は行わない。

比較はPaired、Random、State-static、Pair-response shuffle、Outcome shuffle。2 opaque domain、seed 1/7/19、標準・言い換え・未知語順・入れ子・複数段落・自由表現を評価した。final afterはcandidate生成・rankingに不使用。

## 結果

| 条件 | 候補数 | Prospective | Inverse | Goal | Repair | Abstain |
|---|---:|---:|---:|---:|---:|---:|
| Paired | 0.333 | 0 | 0 | 0 | 0 | 1.0 |
| Random | 0.167 | 0 | 0 | 0 | 0 | 1.0 |
| State-static | 0.000 | 0 | 0 | 0 | 0 | 1.0 |
| Pair shuffle | 0.167 | 0 | 0 | 0 | 0 | 1.0 |
| Outcome shuffle | 0.333 | 0 | 0 | 0 | 0 | 1.0 |

全表現条件で同じ結果。strict progressは0/3 seed。

## 判断

**中核仮説は強く反証。能力進歩なし、G1/G2未達、formal operation proposal 0。**

一要素だけが異なるpaired episodeから匿名token集合を生成しても、平均候補は0.33件に留まり、operation・target・source・goalを同時に提供する取得時unitは成立しなかった。候補を緩めればsurface差分が増えるだけで、外部rolloutに必要なargument bindingへ接続しない。

今回の根本的失敗は、paired差分のfactor名を知らなくても「変化したtoken集合の外部応答」がroleを一意化すると仮定した点にある。実際には同じworld transition差を、operation変更、target変更、source変更、goal変更、nuisance変化の複数説明が共有する。role-specific lesionは既に成立したroleの必要性監査には使えるが、role birth原理ではない。

## 反証分類

- acquisition-time role underbirth
- paired-difference explanation aliasing
- target/source/goal joint-binding failure
- initial operation semantics failure
- candidate-support failure

## 他系列へ返す条件

- A: raw identity候補は、target/source/goal交換pairのどれで再利用されるかだけでなく、他の交換では不変である排他的識別性が必要。
- C: lesion前に各raw roleが独立paired setでsame-unique再収束すること。role名を与えた選択的lesionは因果birth証拠にしない。
- D: 取得時closed-loop 0のためmemory eligible unit 0。保持・忘却研究は再開不可。
- E: AF-013はpaired反例basisとして維持できるが、`paired token difference implies role birth`は不採用下位仮説。

## 次仮説

**Mutual-Exclusion Role Birth from Orthogonal Paired Intervention Bases**

同じraw token集合が、対応factor交換では予測を変え、他factor交換では不変で、target/non-target保存を満たし、語彙非共有domainの独立取得集合でも同じ介入応答型へ再生成される場合だけoperation unit候補へ昇格する。Correct、pair shuffle、factor shuffle、state-static、outcome shuffleを比較する。

## 資源

- model mean: 43 bytes
- candidate mean: 0.333
- paired trials: 16
- peak RSS: 168884 KiB
- runtime: 0.0311 sec / 3 seeds × 2 domains
- complexity: pair generation O(N^2 L), inference O(C*36)
- 1GB未満: pass
- answer leakage: none
- weak smartphone実機: 未検証
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: 未達
