# B Operation / Goal Cycle 010

## 仮説

**Set-Valued Operation-Core Birth from State-Crossing Counterfactual Coverage**  
（状態横断反実仮想coverageからの集合値operation core創発）

PR #393の単一token outcome-entropy inventory失敗を受け、operationを一文字roleへ割り当てる前提を廃止した。raw command中の1〜3文字からなる非連続集合を候補化し、複数初期状態・対象交換・goal変更・語順変動を越えて同じ観測transition signatureを再現する集合だけをoperation core候補とした。

### 設計

- 3-bit world
- unary `set / flip` と binary `copy / swap` をsynthetic環境に含む
- operation表現は2文字の非連続core
- object alias、goal token、nuisance、語順、入れ子、段落を混在
- 2つの完全語彙非共有domain
- Active state-crossing / Random / State-static
- Family shuffle / Outcome shuffle
- seed 1 / 7 / 19
- final test afterは候補生成・rankingに不使用

A PR #397のraw alias-role upper-boundは正式G1 proposalではないため、対象slotや文字classを入力として渡していない。モデルはraw文字集合とbefore/after witnessだけから候補集合を作る。

## 3 seed平均

| 条件 | Active prospective | Random | State-static | Active inverse | Active abstention |
|---|---:|---:|---:|---:|---:|
| d0 Held | 0 | 0 | 0 | 0 | 1.0 |
| d0 Rename | 0 | 0 | 0 | 0 | 1.0 |
| d0 未知語順 | 0 | 0 | 0 | 0 | 1.0 |
| d0 入れ子 | 0 | 0 | 0 | 0 | 1.0 |
| d0 複数段落 | 0 | 0 | 0 | 0 | 1.0 |
| d0 自由記述 | 0 | 0 | 0 | 0 | 1.0 |
| d0 目的変更 | 0 | 0 | 0 | 0 | 1.0 |
| d0 失敗修正 | 0 | 0 | 0 | 0 | 1.0 |
| d1 Held | 0 | 0 | 0 | 0 | 1.0 |
| d1 Rename | 0 | 0 | 0 | 0 | 1.0 |
| d1 未知語順 | 0 | 0 | 0 | 0 | 1.0 |
| d1 入れ子 | 0 | 0 | 0 | 0 | 1.0 |
| d1 複数段落 | 0 | 0 | 0 | 0 | 1.0 |
| d1 自由記述 | 0 | 0 | 0 | 0 | 1.0 |
| d1 目的変更 | 0 | 0 | 0 | 0 | 1.0 |
| d1 失敗修正 | 0 | 0 | 0 | 0 | 1.0 |

追加診断:

- Active core候補: **47.00**
- Random core候補: **64.33**
- State-static core候補: **0.00**
- Outcome-shuffle core候補: **2.00**
- Active model: **1,664.7 bytes**
- Strict progress: **0 / 3 seed**

## 判断

**中核仮説は強く反証。能力進歩は未認定、G1/G2未達、formal operation proposalは0件。**

ActiveとRandomでは、正しい外部witnessに依存するset-valued core候補がそれぞれ平均47.0件、64.3件形成された。State-staticでは0件となり、複数before-stateを横断しなければ候補集合自体が安定しないことは確認できた。Outcome shuffleでは平均2件まで崩れたため、候補形成は正しい言語―結果対応に依存している。

しかし全方式・全domain・全表現でprospective、inverse、goal変更、failure repairは0、abstentionは1.0だった。

> **非連続token集合が複数状態で同じ粗い結果signatureを共有しても、target、source、goal、argument linkを一意に束縛できなければ実行可能operationにはならない。**

### 反証の核心

今回のtransition signatureは、変更数、0→1/1→0、non-target保存数を表す。これは局所差分よりstate-crossingに強いが、次を失っている。

- どのobjectがtargetか
- binary operationのsourceはどれか
- set操作のgoal値
- 同じeffect signatureを生む別programの区別
- command中のargument集合とworld objectの対応

そのため多数の候補afterが同点になり、全面棄権した。候補数やoutcome依存性は診断であり外部能力ではない。

## 失敗分類

- `set_valued_core_without_argument_binding_failure`
- `coarse_transition_signature_aliasing`
- `scope_arity_source_target_underdetermination`
- `initial_operation_semantics_failure`
- `candidate_birth_without_executable_support`

## 他系列へ返す知見

- **A**: alias-role候補には、同じ結果signatureとの共起だけでなく、対象交換時に対応targetだけが交換されるargument-binding反例が必要。
- **C**: state crossingだけでは不足。target lesion、source lesion、argument-order交換、non-target保存を組み合わせ、各role削除が対応rolloutだけを壊す必要がある。
- **D**: core候補は形成されたがclosed-loop利用0のためmemory eligible unitは0。保持失敗ではなく取得時semantics failure。
- **E**: set-valued token集合への拡張だけではsingle-token仮説の失敗を解消しない。外部能力0なのでAF-012の下位仮説として不採用候補。

## 次の仮説

**Argument-Linked Operation Birth from Role-Specific Intervention Lesions**  
（役割別介入lesionによるargument-linked operation創発）

次は粗いtransition signatureをoperation identityにしない。

1. 非連続token集合候補を生成
2. target候補だけ交換したpaired witnessを生成
3. source候補だけ交換したpaired witnessを生成
4. goal候補だけ交換したpaired witnessを生成
5. 各language role lesionが対応するworld transition成分だけを壊す候補を保持
6. target/source/order/goalのjoint bindingを持つ候補だけでprospective rollout
7. Active / Random / State-static / role shuffle / argument-link shuffle / outcome shuffleを比較
8. 2 opaque domain × 3 seedでCorrectが全対照を+0.10以上上回ることを要求

## Resources

- Candidate core upper bound: 256
- Peak RSS: 112,504 KiB
- Runtime: 16.6053 sec / 3 seeds
- Complexity: training `O(B·L³)`, inference `O(C·K)`
- 1GB未満: 達成
- 弱いスマートフォンCPU実機: 未検証
- Answer leakage: なし
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: false
