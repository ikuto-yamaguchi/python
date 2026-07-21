# 系列E Cycle 007 — Scope-Contrastive Factor Proposal with Reversible Attractor Selection

## 結論

Cycle 006では、action/no-opという実行結果の異なる2候補を与えると、少数候補・平均約1.46 sweepでも正のmarginを形成できた。一方、未学習命令、入れ子、複数段落、計画変更は0で、最大のボトルネックは候補graphのproposalだった。

本サイクルでは文・段落境界から、command attachment、condition scope、action/no-op branch、訂正時のfirst/last commandが異なる候補格子を生成し、branch固有の局所energyで緩和した。

最大96例・3 seed平均では、通常・未知context・未知command・入れ子・複数段落はすべて0で、attractor方式はほぼ全面棄権した。計画変更だけは0.1833、margin 0.0538を得たが、通常能力を失っており採用できない。中核仮説は反証である。

## 他系列との重複表

| 系列 | 現在の中心機構 | 成功 | 失敗・未解決 | 本サイクルとの境界 |
|---|---|---|---|---|
| A | entropy整合型の多ターン確認 | 既知feedbackでは約log2(K) bitで候補分離 | 未知feedbackで誤確信 | 外部観測を選ばず、内部scope候補を緩和 |
| B | 効果条件付きprimitive MDL | 一回効果bridgeで未知述語0.4917、約3.3KB | role/scope/別状態表現が未成立 | primitive誘導ではなく生成済みscope/branch候補の選択 |
| C | 介入効果同値condition quotient | 一回効果bridge後の未知context 1.0、486B | zero-shot 0.2833、branch種類固定 | condition node形成ではなくattachment/scopeの競合 |
| D | 反実仮想fast write/read memory graph | 明示的one-shot 0.6611 | 代名詞・更新先・長文質問が崩壊 | 長期記憶でなく即時factor graph inference |
| E候補 | 文区間scope格子＋局所energy | 計画変更で限定margin | candidate recallと構造同型性が崩壊 | 本系列固有 |

Cのcondition quotient、Bのprimitive橋渡し、Dの記憶統合を中心に置く候補は重複のため棄却した。Aの外部質問も採らず、Eではscope・attachment・revision policyが異なる候補を内部緩和することに限定した。

## 先行研究整理

Energy-based structured predictionではenergy最小化だけでなく、出力構造・factor分解・推論近似が性能を決める。2025年のtest-time adaptation研究でも、entropy低下だけでは正しさやenergy低下を保証せず、識別的な信号が必要と報告されている。今回の結果も、内部不確実性やenergyを下げても正しい候補構造が存在しなければ誤収束・全面棄権になることを支持する。

参考:
- Park et al., *Rethinking Entropy in Test-Time Adaptation: The Missing Piece from Energy Duality*, NeurIPS 2025.
- Hu et al., *Test-Time Learning for Large Language Models*, ICML 2025.
- Tu and Gimpel, *Learning Approximate Inference Networks for Structured Prediction*, 2018.
- Cortes et al., *Structured Prediction Theory Based on Factor Graph Complexity*, 2016.

## 仮説

**Scope-Contrastive Factor Proposal with Reversible Attractor Selection**

> 生の複数文入力から、command位置、condition scope、branch、訂正時の採用commandが異なる少数候補を生成し、branch固有の局所整合性energyで反復緩和すれば、固定された末尾condition切出しを使わず、入れ子・複数段落・計画変更を正のmarginで選別できる。

単なるHopfield記憶とは異なり、保存パターンへの最近傍復元ではなく、入力ごとに生成したscope/attachment/branch/revision候補を実行し、その局所factor energyを比較する。

### 停止条件

- 最良候補の `(command, scope, branch, revision)` が前sweepと同一
- 最大8 sweep
- 最良・次点marginが0.005未満なら棄権

### 反証分類

- 局所最適: 誤候補に正marginで収束
- 発散: 8 sweep以内に最良候補が安定しない
- 候補崩壊: 正答実行候補が候補集合に含まれない
- 平坦化: margin 0で全面棄権

## 実装

`scope_contrastive_attractor_cycle7.py`

モデルに固定entity/value一覧、意味slot名、形態素解析器、ontology、RAG、外部LLMは与えていない。句点・改行から文単位を作り、最大2文の連続scope、各文のcommand候補、action/no-op、first/last revisionを組み合わせる。候補上限は32。

energyは、command view整合、branch別scope整合、attachment整合、訂正時の弱いrecency factorから構成した。factor重みは固定であり、平衡伝播や局所可塑性を成立させたものではない。

## 実験条件

- train sizes: 24 / 48 / 96
- seeds: 1 / 7 / 19
- 各split 20件/seed
- 通常、未知context、未知command、入れ子、入れ子＋未知context、複数段落、計画変更
- flat baselineとattractorを比較
- 候補上限32、最大8 sweep

再現:

```bash
cd research/intelligence_swarm/tracks/E_constraint_relaxation
python scope_contrastive_attractor_cycle7.py
```

## 最大96例・3 seed平均

| 指標 | flat | attractor |
|---|---:|---:|
| 通常精度 | 0.0000 | 0.0000 |
| 通常棄権 | 0.3000 | 1.0000 |
| 未知context精度 | 0.0000 | 0.0000 |
| 未知command精度 | 0.0000 | 0.0000 |
| 入れ子精度 | 0.0000 | 0.0000 |
| 入れ子＋未知context | 0.0000 | 0.0000 |
| 複数段落 | 0.0000 | 0.0000 |
| 計画変更 | 0.0000 | **0.1833** |
| 計画変更margin | 0.0000 | **0.0538** |
| 通常平均sweep | 1.0 | 2.0 |
| 通常活性候補 | 1 | 24 |
| 入れ子活性候補 | 1 | 32 |
| モデルサイズ | — | 54,618 B |
| 学習時間 | — | 0.00113 s |
| 通常推論 | 0.178 ms | 16.30 ms |
| 計画変更推論 | 0.625 ms | 20.69 ms |
| Peak RSS | — | 13,764 KiB |

推定score評価量は `O(S*H*(C+B))`。`S`はsweep、`H≤32`、`C≤48` command view、`B≤64` scope view/branch。モデルは1GB未満だが、能力0のまま16〜24msを消費するため、弱いスマートフォン向け原理として採用しない。

## 決定的な反証

1. **Candidate recall崩壊**: 文字差分と短区間分割では対象・値・predicate・助詞を安定分離できず、正しい実行programが候補集合へ入らない。
2. **意味的非同型性不足**: 文区間が違っても多くの候補が同じaction/no-op結果を生成し、通常splitはmargin 0へ平坦化した。
3. **計画変更の見かけ上の改善**: `訂正`表面markerに依存したrecency factorであり、通常能力を失っているため意味理解の証拠ではない。
4. **計算量だけ増加**: 24〜32候補、2 sweepで16〜24msへ悪化し、能力改善がない。
5. **局所学習未成立**: factor重みをfree/perturbed phaseの局所相関差から学習しておらず、平衡伝播の証拠はない。

## 系列E固有の進展

問題を明確に二分できた。

1. 非同型branchが既にある場合のattractor selection — Cycle 006で限定成立。
2. 生の日本語から非同型scope/role graphをproposalする能力 — 今回も未成立。

単に文区間、attachment、first/lastを組み合わせても意味的構造多様性にはならない。候補graphは異なるscopeを持つだけでなく、異なる局所予測・実行結果・反実仮想を生成しなければならない。

## 他系列へ返す知見

- A: 質問対象となる候補は、scope差だけでなく異なる未来を生成する必要がある。内部entropyだけで候補品質は測れない。
- B: role/effect latticeの候補は、可逆区間差だけでなく実行結果差を必須監査にする。
- C: condition nodeのsurface alias追加だけではscope attachmentは決まらない。複数operationへの効果signatureが必要。
- D: memory graph候補は異なる想起だけでなく、scope・更新先・実行effectが異なる必要がある。

## 次仮説

**Intervention-Discriminative Scope Attractors with Learned Local Factors**

次は全区間組合せを列挙しない。候補scopeが、複数operation・無介入・逆操作・訂正後観測に対して異なる局所予測を生成する場合だけ保持する。各factor重みはfree/perturbed phaseの局所相関差で更新し、固定recency markerを廃止する。

必須成功条件:

1. 正答候補recallを明示測定し0から改善
2. 通常精度を維持したまま計画変更・入れ子のいずれかを0から改善
3. margin 0の全面棄権を回避
4. 候補数16以下、平均sweep4以下
5. モデル32KB以下、弱いCPUで5ms/query以下を見込める
6. 未知context・未知commandで表面prototypeより改善

## 最終評価

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
