# 系列B Operation / Goal Cycle 009

## 仮説

**Nonparametric Operation-Inventory Birth from Outcome-Conditioned Token Roles**  
（外部結果に条件付けた匿名token役割からの非パラメトリック操作inventory創発）

GOV-010 / AF-011とA PR #392を受け、Aがraw alphabetからcharacter classを再収束できた上限結果を、操作family・class cardinality・arity multisetを与えない条件へ拡張した。

learnerには対象文字集合、操作文字集合、nuisance文字集合、operation family数、各operationのarity、goal方向、global surface templateを与えていない。episodeごとのraw commandとbefore/after外部結果だけから、各文字について次を推定した。

- 特定world成分の変化との選択的関連 → anonymous argument token候補
- outcome signatureの条件entropy → anonymous operation token候補
- どちらにも安定しない文字 → nuisance候補
- changed-object count / delta / permutation / global changeからoperation prototypeとarityを同時birth
- prefix / suffix / interleave / reverse / paragraph / omitted / freeをepisode-local nuisanceとして混在

Final評価のafterは候補生成・rankingに使用していない。

## 最新系列との重複回避

| 系列 | 最新中心 | Bで成果対象にしない領域 |
|---|---|---|
| A PR #392 | raw character-classとmappingの独立witness再収束 | 対象/操作文字class同定そのもの |
| C PR #389 | episode-local syntax orbitによるcausal candidate support回復 | 因果world identityとcounterfactual closure |
| D PR #390 | 独立witness集合の再同定とconflict隔離 | memory eligibility / retention |
| E PR #391 | HF-013凍結、AF-011優先 | governance判断 |
| **B** | **operation family数・arity・goal方向を与えず、外部結果から実行可能inventoryをbirth** | 今回の固有対象 |

## 比較条件

- Active witness: token/outcome共起のnoveltyとsignature coverageを最大化
- Conservative: coverageを保つ保守条件（今回の最小実装ではActiveと同じ選択）
- Random witness
- Global-template control
- Outcome shuffle
- seed: 1 / 7 / 19
- witness budget: 18

## 3 seed平均

| 条件 | Active joint | Random joint | Shuffle joint | Active inverse | Active goal | Active abstain |
|---|---:|---:|---:|---:|---:|---:|
| Held | 0.0069 | 0.0139 | 0.0000 | 0.0347 | 0.0139 | 0.9653 |
| 未知語順 | 0.0000 | 0.0069 | 0.0000 | 0.0417 | 0.0208 | 0.9583 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 | 0.0139 | 0.0069 | 0.9861 |
| 複数段落 | 0.0069 | 0.0000 | 0.0000 | 0.0764 | 0.0278 | 0.9236 |
| 自由記述 | 0.0069 | 0.0139 | 0.0000 | 0.0347 | 0.0139 | 0.9653 |
| 目的変更 | 0.0069 | 0.0278 | 0.0000 | 0.0278 | 0.0069 | 0.9722 |
| 失敗修正 | 0.0069 | 0.0278 | 0.0000 | 0.0347 | 0.0278 | 0.9653 |
| 別領域 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0278 | 0.9583 |

追加診断:

- Active born operation token: **0.33**
- Random born operation token: **2.00**
- Active argument token: **6.33**
- Active nuisance token: **5.33**
- Active model: **270 bytes**
- Peak RSS: **111008 KiB**（Python runtime込み）
- 3 seed × 5方式 runtime: **0.3178 sec**
- Active平均実行時間: **0.0249 sec / seed**
- candidate pool: 90
- witness budget: 18
- 推定計算量: train `O(B·L·S)`、推論 `O(K·A)`、K≤4、A≤2

## 判断

**中核仮説は強く反証。能力上の進歩は未認定、G1/G2未達、正式operation proposalは0件。**

### operation inventoryがほぼbirthしない

Activeでは平均0.33個しかoperation tokenが形成されず、Randomの2.0個を下回った。外部結果signatureのentropyを小さくする文字をoperation候補とするだけでは、mixed syntax・goal文字・nuisanceを分離できない。

### ActiveはRandomより悪い

Held jointはActive 0.0069、Random 0.0139。目的変更と失敗修正でもRandomがActiveを上回った。Outcome shuffleは全面棄権となったため、正しい外部対応へ依存する微弱信号はあるが、CorrectがRandomを改善していない。

### abstentionが支配

Activeは主要条件で92〜99%棄権した。候補数削減や安全な棄権ではなく、操作primitiveを形成できず実行不能になった結果である。

### 別領域one-shotでも0

完全に異なる文字集合の第二domainへ4 calibration episodeを与えてもjoint/inverseは0だった。世界結果signatureだけでは、新しい語彙から同じ操作inventoryを再生成できない。

### 根本原因

現在のtoken単位統計は、文字が単独でoperationを表すことを暗黙に仮定している。実際には、operation identityは次の共同構造としてbirthする必要がある。

- 複数tokenにまたがる匿名発話変換
- 引数集合との結合
- goal条件による同一operation内の分岐
- zero/unary/binary/global effectの反実仮想coverage
- episode-localな省略・語順・段落表現を越える独立再収束

したがって、character classを得た後に各文字のoutcome entropyでoperation familyへ分類する方式は、A PR #392の後段利用としても不十分である。

## 失敗分類

- `tokenwise_operation_role_assumption_failure`
- `nonparametric_inventory_underbirth`
- `goal_operation_entanglement`
- `cross_domain_rebirth_failure`
- `initial_operation_semantics_failure`

## 他系列へ返す知見

- **A:** character classの再収束だけではoperation利用可能性にならない。単一文字classではなく、同じargument変換を予測する複数token発話変換候補が必要。
- **C:** operation proposalは0。因果監査前に、goalを変えてもoperation coreが維持され、argumentのみ交換したcounterfactual coverageを持つ候補を要求する。
- **D:** acquisition時joint/inverseがほぼ0なのでmemory eligibilityは0。保持失敗やcatastrophic forgettingではない。
- **E:** AF-011は継続可能だが、`token outcome entropy creates operation inventory` を不採用下位仮説として登録すべき。

## 次仮説

**Set-Valued Utterance-Transformation Birth from Goal-Conditional Counterfactual Coverage**  
（goal条件付き反実仮想coverageからの集合値発話変換創発）

次は文字ごとのrole分類をやめる。

1. 各episodeについて複数のraw substring集合・非連続token集合を匿名候補化
2. object交換、goal交換、argument追加/削除、順序交換を行うcounterfactual witnessを生成
3. 同じworld transition familyを維持し、goalだけで方向が分岐する集合変換をoperation core候補化
4. zero/unary/binary/global effectをfamily名なしで分裂・統合
5. Active / Random / tokenwise / set-shuffle / outcome-shuffleを比較
6. 重複しない第二witness集合で同じset-valued operation coreへ再収束することを要求
7. 未使用token、主語省略、複数段落、自由記述、別domainでprospective/inverse/goal/repairを評価

## 状態

- Stage: S1継続
- G1: 未達
- G2: 未達
- formal operation proposal: 0
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
