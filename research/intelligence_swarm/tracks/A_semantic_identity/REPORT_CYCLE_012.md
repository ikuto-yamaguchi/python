# A Semantic Identity Cycle 012

## Hypothesis

**Paired Intervention Difference Quotients Birth Reusable Identity without Enumerated Roles**

有限role/program worldやposterior intersectionを使わず、同一commandを異なるbefore-stateで観測したpaired interventionから、raw文字n-gramとworld変化の対応を直接更新した。意味単位候補は文字区間として事前定義せず、whole-command上の局所特徴がpaired effectへ再利用できるかだけを測定した。

- opaque domain: d1 / d2
- seed: 1 / 7 / 19
- train: held表現96 episode/domain
- test: Rename、未知語順、主語省略相当、複数段落、自由日本語
- controls: Random、State-static、Pair shuffle
- final after leakageなし
- fixed ontology / enumerated role world / RAG / external LLMなし

## Results — 3 seed × 2 domain mean

| Method | Prospective | Inverse | Rename | Unknown order | Omitted | Paragraph | Free | Counterfactual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Paired | 0.1746 | 0.1567 | 0.0000 | 0.0000 | 0.0000 | 0.3333 | 0.3929 | 0.1964 |
| Random | 0.2202 | 0.2063 | 0.0000 | 0.0000 | 0.0000 | 0.4167 | 0.4881 | 0.2163 |
| State-static | 0.2083 | 0.1786 | 0.0000 | 0.0000 | 0.0000 | 0.4524 | 0.4167 | 0.2004 |
| Pair shuffle | 0.2123 | 0.1746 | 0.0000 | 0.0000 | 0.0000 | 0.4524 | 0.4286 | 0.1944 |

Strict progress: **0/3 seed**.

## Decision

**中核仮説は強く反証。能力進歩は未認定、G1未達。**

Paired条件はRandomを一つの主要指標でも上回らなかった。Rename・未知語順・省略は全方式0であり、自由日本語でもPaired 0.3929に対しRandom 0.4881だった。

> 同一表面commandを状態横断で対にし、raw n-gramと結果差を結び付けるだけでは、再利用可能な対象・変数identityは誕生しない。

paired interventionは因果反例として必要だが、表面支持が共有される同一command内でのdifference quotientは、未知表現へ同一単位を再生成する原理ではない。

## Falsification and diagnosis

- Paired > Random: 不成立
- Paired > Pair shuffle: 不成立
- Rename / unknown order / omitted transfer: 全て0
- Cross-domain再利用: 不成立
- Failure classification: `paired_surface_support_without_cross_alias_identity`

Pair shuffleもPairedと同程度だったため、学習されたものはpaired因果構造ではなく、held表現中の局所n-gram頻度とdomain-local outcome偏りで説明できる。

## Return to other tracks

- B: target/source/goal/argumentのpaired interventionは、表面token共有ではなく、表現非共有の各側で同じ選択的transitionを再生成する必要がある。
- C: paired witnessを同一command反復で構成せず、片側の表現を完全に隠したcross-expression paired basisを必須化する。
- D: acquisition-time unique unitは0。保存・干渉評価は再開不可。
- E: AF-013は反例設計として継続可能だが、`surface-shared paired difference quotient`は不採用下位仮説とする。

## Next hypothesis

**Cross-Expression Paired Intervention Equivalence from Mutual Predictive Repair**

次はpairの両側で語彙・語順・局所n-gramを共有させない。二つのraw utterance transformationが、target-state交換・non-target-state交換に対して同じ外部予測誤差を相互修復する場合だけidentity proposalを生成する。

必須比較はCorrect cross-expression pair、same-surface pair、pair shuffle、outcome shuffle、Random。2 opaque domain × 3 seedでRename、未知語順、主語省略、複数段落、自由日本語、prospective、inverse、counterfactualを評価する。

## Resources

- model bytes mean: 2230.3
- peak RSS: 110504 KiB
- runtime: 0.0658 sec / 3 seed × 2 domain
- estimated ops: O(B * |ngrams| * effects)
- 1GB未満: pass
- weak smartphone実機: 未検証
- answer leakage: none
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: 未達
