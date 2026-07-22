# 系列C Cycle 016 研究報告

## 仮説

**Event-Regime Discovery from Intervention Commutativity Breaks**  
（介入交換可能性の破れからのevent-regime発見）

Cycle 015では既知形式の局所更新は36 node・精度1.0で再実行できた一方、未知言い換え・別状態表現・主語省略・複数段落・計画変更はすべて0だった。非対象保存ablationも増分情報0で、nodeはobject identityではなく既知surface contextだった。

本Cycleでは、系列Bの「outcome matrixのrank増加による介入basis」と中心機構が重なる候補を棄却した。代わりに、連続する局所介入が交換可能かをraw before/after編集から判定し、交換可能性が崩れる地点をevent/regime境界として分節し、境界内だけで状態遷移を再利用する仮説を検証した。

## 先行研究整理

- Li et al., AISTATS 2025: 介入集合のcoverageにより識別可能な因果抽象化の粒度が決まる。https://proceedings.mlr.press/v258/li25g.html
- Rahmani & Frossard, AISTATS 2025: 時系列の因果regimeと各DAGの共同同定。https://proceedings.mlr.press/v258/rahmani25a.html
- Kekić et al., ICML 2025: 単一介入から複合介入効果を推定するには効果分解を可能にする構造仮定が必要。https://proceedings.mlr.press/v267/kekic25a.html
- Jahn et al., CLeaR 2025: 時系列因果効果の識別に必要な履歴長を有限に抑えられる条件。https://proceedings.mlr.press/v275/jahn25a.html

これらは因果regime・介入coverage・有限履歴の重要性を支持するが、観測変数や介入対象は既に定義されている。生の日本語からobject・relation・event候補を作る上流問題は別に残る。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | C候補との判定 |
|---|---|---|---|---|
| A | prediction-error surgeryからprobe library | marked能力を維持し推論短縮 | unmarked recall 0、破壊量の大きいprobeへ偏る | 外部probe policyは棄却 |
| B | rank増加program outcome basis | executable既知0.6222 | quotient 0.1778、role basis未成立 | rank増加介入basisは重複のため棄却 |
| D | factorized object/relation address trace | write/read非対称性を明確化 | one-shot 0、read 0、surface nodeへ過剰統合 | 長期memory addressは棄却 |
| E | minimal edge surgeryによるrouting自己誘導 | 既知basis間routingをほぼ完全回復 | residual/edge basis自体は手書き | energy routingは棄却 |
| C | intervention commutativityによるevent-regime分節 | 今回検証 | raw editと意味regimeの同一性 | 系列固有 |

継承知見:
- A: 分割利得だけでは意味的probeにならない。
- B: outcome差分を並べてもrole識別basisがなければ商形成に失敗する。
- D: write成功とread/address形成は別能力。
- E: finite-difference routing回復とbasis創発は分けて評価する。

## 設計

learner入力はraw Japanese before/command/afterと順序のみ。hidden object/field/value/regime/event IDは評価専用で、proposal・boundary decision・transition executionには使わない。

各before/afterから局所editを作り、隣接edit `a,b`について `a→b` と `b→a` のraw state結果が異なる場合をcommutativity breakとした。

比較:
1. Surface boundary: command noveltyのみ
2. Regime no-comm: commutativityなし
3. Regime comm: commutativity + novelty + cross-episode support
4. Regime no-support: support条件を外すablation

## 実験

- event数: 8 / 16 / 24
- 1 event当たり4介入
- seed: 1 / 7 / 19
- 最大96 step、plan条件120 step
- seen / alternate state / subject omission / multi-paragraph / plan change
- event boundary F1 / next-state / order counterfactual / regime数 / edge数 / model / RSS / latency

## 最大24 event・3 seed平均

### Event boundary F1

| 条件 | Surface | No-comm | Commutativity | No-support |
|---|---:|---:|---:|---:|
| seen | 0.3698 | 0.0800 | 0.1994 | 0.2222 |
| alternate | 0.3698 | 0.0800 | 0.1994 | 0.2222 |
| omitted | 0.5000 | 0.0800 | 0.1766 | 0.2222 |
| paragraph | 0.3737 | 0.0800 | 0.1978 | 0.2175 |
| plan | 0.3621 | 0.0800 | 0.2002 | 0.2215 |

### Next-state accuracy

| 条件 | Surface | No-comm | Commutativity |
|---|---:|---:|---:|
| seen | 0.8438 | 1.0000 | 1.0000 |
| alternate | 0.8438 | 1.0000 | 1.0000 |
| omitted | 0.5139 | 0.9965 | 0.9965 |
| paragraph | 0.9514 | 1.0000 | 1.0000 |
| plan | 0.8556 | 1.0000 | 1.0000 |

### Order counterfactual

| 条件 | Surface | No-comm | Commutativity |
|---|---:|---:|---:|
| seen | 0.5167 | 0.7929 | 0.7095 |
| omitted | 0.2000 | 0.8024 | 0.7548 |
| paragraph | 0.5871 | 0.6609 | 0.5333 |
| plan | 0.4709 | 0.6739 | 0.6398 |

## 判定

**中核仮説は反証。**

1. commutativityはevent境界を改善しない。seen F1 0.1994はsurface 0.3698を下回り、true event 24に対してregime数は平均2.67で巨大regimeへ誤統合した。
2. supportありF1 0.1994、supportなし0.2222で、cross-episode supportは境界精度を改善しなかった。
3. next-state 1.0は観測したbefore/after局所editを同じ入力へ即時再適用する制御条件であり、未知object・未知relation・zero-shot因果転移ではない。
4. seen order counterfactualはno-comm 0.7929に対しcomm 0.7095へ悪化した。raw text editの交換可能性とworld operationの交換可能性は一致しない。
5. omitted 0.9965もbefore stateが単一objectの完全記述であり、談話から省略主語を解決した結果ではない。
6. plan 1.0も最終訂正文のbefore/after editをそのまま学習しただけで、撤回されたoperation・旧goal・新goal・constraintをgraphへ保持していない。

重要な否定結果:

> raw文字編集の交換可能性は、意味的operationの交換可能性ではない。event境界を因果的に定義するには、同じ潜在state variableへ作用するoperationと異なるvariableへ作用するoperationを先に区別する必要がある。

## 相関暗記と因果理解の反証条件

- boundary F1がsurface novelty未満 → causal event segmentationではない
- commutativity ablationが同等以上 → 交換可能性の増分情報なし
- 同一episodeの観測edit再適用だけで1.0 → intervention correlation replay
- order counterfactualがcomm方式で悪化 → raw edit algebraとworld causalityが不一致
- omitted/planでfocus・goal edgeなし → object permanence / planning未成立

## 資源量

最大24 event seen comm方式:
- model: 44,718 bytes
- edge: 96
- regime: 2.67
- training: 0.0639 sec
- inference: 0.6404 ms/step
- Peak RSS: 113,668 KiB（Python runtime込み）
- complexity: learning `O(NKG)`, inference `O(KG)`, counterfactual `O(NK)`, `K<=64`

1GB未満・5ms未満は満たすが、弱いスマートフォン実機では未検証。能力未成立のため採用不能。

## 系列C固有の進展

1. raw object/event proposal
2. local transition executability
3. temporal regime proposal
4. **operation algebra identification**
5. object/relation binding
6. counterfactual composition
7. goal/constraint planning
8. open-form Japanese integration

今回は3・4をraw edit algebraで近似したが、operation algebraの意味的basisが欠けていた。

## 他系列へ返す新知見

- A: surgery outcome昇格前にraw edit競合とworld operation競合を分離する。
- B: outcome matrixのrank増加は、潜在state variable basisがなければ文字位置rankになる。
- D: event境界を先に作ってもobject/relation addressがなければ巨大regimeへ誤統合する。
- E: commutativity residualをroutingできてもedge basisがsurface editなら因果causeにならない。

## 次の仮説

**Latent-State-Specific Operation Algebra from Cross-Context Commutator Signatures**  
（文脈横断commutator signatureによる潜在状態別operation代数）

単一raw state上の交換可能性を直接event境界へ使わない。同じcommand候補を複数object・複数state表現へ再適用し、二操作のcommutator outcomeをcross-context vector化する。表現や文字位置が変わっても同じpatternを持つ操作だけを同じlatent-state familyへまとめ、familyが変化する地点をevent/regime境界候補にする。説明不能操作はnull operationへ保持する。

最低成功条件:
- boundary F1 0.3698超
- commutativity ablationとの差を明確化
- order counterfactual 0.7929維持または改善
- alternate / omitted / paragraphで同じoperation familyを再利用
- operation family 3～12
- 32KB未満
- 5ms/step未満

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
