# 系列C Causal Grounding Cycle 004

## 仮説

**Active Consequence Disambiguation Identifiability under Opaque-Domain Utterances**  
（不透明語彙domainにおける能動結果識別の因果接地可能性）

A Cycle 003では、新domainで16件の正しい観測遷移を与えるとdomain内held・主語省略・複数段落・自由日本語に弱い改善が生じた一方、rename、未知語順、inverse、第二domainは成立しなかった。

本Cycleでは、観測数を増やすのではなく、現在の候補モデル群が最も異なる結果を予測する発話を先に観測すれば、少数観測で因果単位を識別できるという仮説を検証した。

- 候補pool: 4 relation × 4 transition × 3表現 = 48発話
- 観測budget: 2 / 4 / 8 / 16
- Active: bootstrap model ensembleの予測不一致最大化
- Random: 同budgetの無作為選択
- Shuffle: Active選択発話と結果の対応だけをshuffle
- 選択時にtest outcomeは不使用
- test時にpost-treatment outcomeは不使用
- span proposal、文字列retrieval、domain辞書、共有identity、外部LLMなし

## 最新系列との重複回避

- A Cycle 003: 正しい少数観測によるdomain-local utterance–consequence再結合
- B Cycle 002: identity / operation / goal / directionの四方向contrast
- C Cycle 003: 座標変換可換な介入前relation
- D Cycle 003: identity–operation分離memory eligibility
- E GOV-004: AF-005 cross-domain consequence-invariant grounding

本Cycleは新しいgraph・tensor・低rank差分を作らず、**どの観測を選べば候補因果単位が識別可能になるか**だけを監査した。

## 3 seed平均

Joint chanceは1/16 = 0.0625、inverse chanceは0.25。

| Budget | Method | Held | Rename | 未知語順 | 複数段落 | 自由日本語 | Inverse | 第二domain |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 2 | Active | 0.0556 | 0.0972 | 0.0660 | 0.0972 | 0.0694 | 0.3021 | 0.0625 |
| 2 | Random | 0.0729 | 0.0486 | 0.0590 | 0.0486 | 0.0729 | 0.2951 | 0.0729 |
| 2 | Shuffle | 0.0729 | 0.0625 | 0.0451 | 0.0694 | 0.0521 | 0.2639 | 0.0625 |
| 4 | Active | 0.0521 | 0.0938 | 0.0660 | 0.0694 | 0.0868 | 0.2465 | 0.0660 |
| 4 | Random | 0.0938 | 0.0694 | 0.0799 | 0.0972 | 0.0764 | 0.3125 | 0.0660 |
| 4 | Shuffle | 0.0625 | 0.0486 | 0.0556 | 0.0660 | 0.0486 | 0.2326 | 0.0625 |
| 8 | Active | 0.0660 | 0.0799 | 0.0729 | 0.0799 | 0.0451 | 0.2882 | 0.0521 |
| 8 | Random | 0.1076 | 0.0660 | 0.0694 | 0.0694 | 0.0625 | 0.2604 | 0.0590 |
| 8 | Shuffle | 0.0451 | 0.0312 | 0.0660 | 0.0486 | 0.0590 | 0.2569 | 0.0833 |
| 16 | Active | 0.0833 | 0.1076 | 0.0833 | 0.0833 | 0.0694 | 0.3056 | 0.0729 |
| 16 | Random | 0.1076 | 0.1076 | 0.0556 | 0.0729 | 0.0938 | 0.2778 | 0.0729 |
| 16 | Shuffle | 0.0694 | 0.0764 | 0.0903 | 0.0694 | 0.0764 | 0.2361 | 0.0451 |

Activeが選択した異なるrelation×transition組数:

- budget 2: 2.00
- budget 4: 3.67
- budget 8: 7.00
- budget 16: 13.00

## 判断

**中核仮説は反証。能力上の進歩は未認定。G1未達。**

Activeは、budget 16のrename 0.1076、inverse 0.3056など一部でshuffleを上回った。しかし、同budgetのRandomに対して安定した優位がない。

- budget 8 held: Active 0.0660 < Random 0.1076
- budget 16 held: Active 0.0833 < Random 0.1076
- budget 4 inverse: Active 0.2465 < Random 0.3125
- 第二domainでは全budgetでchance近傍で、budget 8はActive 0.0521 < Shuffle 0.0833

したがって、現在のbootstrap ensembleの不一致は、意味的に識別力のある介入ではなく、文字featureと未学習候補の不安定性を主に測っている。

> **候補モデル間の予測不一致を最大化するだけでは、観測がどの潜在因果因子を識別するかは保証されない。**

A Cycle 003の「2-shotが4-shotより良い」という非単調性は、観測数だけでなく選択原理が必要であることを示した。しかし本Cycleにより、一般的なensemble disagreementも十分な選択原理ではないと分かった。

## 因果接地上の発見

能動観測が意味接地へ寄与するには、単なる予測分散ではなく、少なくとも次の**選択的結果分解**が必要である。

1. identityだけが異なる候補を分ける観測
2. operationだけが異なる候補を分ける観測
3. goalだけが異なる候補を分ける観測
4. wording変更では結果予測を変えない監査
5. domain変更後も同じ選択的結果を持つこと

現状のwhole-utterance consequence matrixは、どの不一致がidentity、operation、goal、surface wording由来かを区別しない。そのためActiveは高分散だが因果的に無関係な発話を選べる。

## 他系列へ返す知見

- **A:** 次のactive選択はensemble entropyではなく、identity/operation/goal/wordingのどれを分離する観測かを明示的に監査する必要がある。未知語順・renameを同じunitへ束縛できない限り、観測選択だけでは解けない。
- **B:** 五方向contrastから各factorに選択的な結果差を作る反例generatorが必要。単なる候補不一致はoperation primitiveの証拠にならない。
- **D:** Active観測後も第二domainとinverseの資格を満たさないためeligible unitは0。保存・干渉・sleep統合は再開不可。
- **E:** AF-005は継続可能だが、`generic ensemble disagreement → semantic grounding`という下位仮説は不採用にすべき。

## 資源量

- Matrix: **16384 bytes**
- 3 seed総実行時間: **13.1233 sec**
- Peak RSS: **110532 KiB**（Python + NumPy runtime込み）
- Update: **4096 ops/観測**
- Inference: **4096 ops/候補 × 16候補**
- Active selection: `O(B * P * E * K * T * C)`
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 次の仮説

**Factor-Selective Active Intervention by Expected Cross-Domain Invariance Gain**  
（期待cross-domain不変性利得による因子選択的能動介入）

次は総予測不一致を最大化しない。各観測候補について、

- identity交換ならtarget応答だけが変わる
- operation交換ならtransition応答だけが変わる
- goal交換なら選択基準だけが変わる
- wording交換なら応答が不変

という選択的response signatureを予測し、未知domainでこの分離を最も改善する観測を選ぶ。

進歩条件は、rename・未知語順・自由日本語・第二domainのすべてでActiveがRandom/Shuffleを+0.10以上上回り、inverse > 0.40、3/3 seed正方向とする。

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
