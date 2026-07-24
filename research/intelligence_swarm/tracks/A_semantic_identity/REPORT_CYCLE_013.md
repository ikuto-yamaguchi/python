# A Semantic Identity Cycle 013

## 仮説

**Cross-Expression Transformation-Indexed Identity from Selective Equivariance Signatures**

応答値の一致やsame-deltaをidentity条件にせず、raw表現が `target / state / goal / operation` の各介入軸に対して示す選択的な変化・保存signatureを学習し、別表現でも同じ変換則が再生成されるかを検証した。

- 2 opaque domain
- seed: 1 / 7 / 19
- raw文字1〜3-gram
- canonical / reverse / omitted / paragraph / free / rename
- Correct / Random / Axis shuffle / Signature shuffle
- final test afterは候補生成・rankingに未使用
- fixed ontology / RAG / external LLM / graph / memory optimizationなし

## 3 seed × 2 domain平均

| 条件 | Prospective | Inverse | Identity hold | Counterfactual | Rename | 未知語順 | 主語省略 | 複数段落 | 自由日本語 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Correct | 0.6194 | 0.2583 | 0.6194 | 0.6194 | 0.0667 | 0.8500 | 0.8167 | 0.7500 | 0.6833 |
| Random | 0.5000 | 0.2444 | 0.5000 | 0.5000 | 0.1000 | 0.7000 | 0.6167 | 0.6167 | 0.4833 |
| Axis shuffle | 0.3139 | 0.1306 | 0.3139 | 0.3139 | 0.0833 | 0.3833 | 0.3500 | 0.3833 | 0.5000 |
| Signature shuffle | 0.2583 | 0.1167 | 0.2583 | 0.2583 | 0.0167 | 0.4833 | 0.2833 | 0.3667 | 0.2667 |

Strict progress: **0/3 seed**

## 判断

**限定的な外部信号は得られたが、中核仮説は正式には未成立。能力進歩は未認定、G1未達。**

CorrectはRandomに対して、prospective +0.1194、未知語順 +0.1500、主語省略 +0.2000、自由日本語 +0.2000だった。Axis/Signature shuffleでは主要能力が大きく崩れ、変換軸とsignatureの対応は外部利用に寄与している。

ただし、RenameはCorrect 0.0667でRandom 0.1000を下回り、Inverse差も +0.0139に留まった。3 seedすべてで全対照を+0.10上回るstrict gateは0/3だった。

さらに本実験では `target/state/goal/operation` の介入軸ラベルとworld state interfaceを校正側へ与えている。したがって、生の自由日本語から介入軸そのものが創発した証拠ではなく、**oracle-axis conditional upper bound** に限定する。

## 反証・切り分け

- response equalityではなくaxis-indexed signatureへ移行すると、shuffle感度と一部外部能力差は生じた。
- しかしRenameとInverseへ再利用できず、表現変換を越えるindividual identityには未到達。
- raw n-gram prototypeはepisode-local語順には耐えるが、完全な表面置換には耐えない。
- `known intervention axis + raw surface prototype` をsemantic birthとみなす下位仮説は不採用。

## 他系列への返却

- B: operation signatureは軸ラベル既知のままでは不十分。target/source/goal/argument軸そのもののbirthが必要。
- C: Rename失敗を分離するため、表面全置換後にも同じ軸別共変行列を再生成できる反例を追加する。
- D: same-unique raw unitは成立せず、memory eligible unitは0。保存研究は再開不可。
- E: AF-014は継続可能だが、oracle-axis upper boundを能力進歩へ数えない。

## 次の仮説

**Latent Intervention-Axis Birth from Commutator Sparsity across Fully Renamed Expression Families**

次は介入軸ラベルを与えず、複数の外部変更を匿名変換として保持する。異なる表現familyで、同じ最小成分だけを選択的に変え、他成分を保存する匿名交換子patternが再出現した場合のみaxis候補を生成する。Rename、inverse、自由日本語でCorrectがRandom / Axis shuffle / Target-link shuffle / Outcome shuffleを各+0.10以上上回ることを要求する。

## 資源量

- model: 7834.5 bytes mean
- peak RSS: 110540 KiB
- runtime: 0.1238 sec / 3 seed × 2 domain
- complexity: O(N * |axes| * sparse_ngrams)
- 1GB未満: 達成
- answer leakage: なし
- 弱いスマートフォン実機: 未検証
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: 未達
