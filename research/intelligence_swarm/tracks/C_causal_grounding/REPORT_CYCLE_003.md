# 系列C Causal Grounding Cycle 003

## 仮説

**Transformation-Equivariant Pre-Treatment Causal Units under Paired Coordinate Worlds**

PR #357 では介入前relationがtarget選択に必要だった一方、絶対座標・object indexへ依存し、別domainでCorrectとshuffleが同一になった。本Cycleでは、同一worldを平行移動・90度回転・object permutationしたpaired coordinate worldとして学習し、介入前の候補target中心の関係multisetとprospective transitionを使う変換可換表現が、絶対表現より未知worldで因果単位を再生成できるか検証した。

禁止されているspan proposal、identity labelによるscoring、固定slot、RAG、文字列retrieval、外部LLM、test outcome利用は行っていない。テスト入力はraw Japanese commandとbefore worldのみで、完成trajectory・scar・afterは使わない。

## 最新系列との分離

- A #357: raw Japaneseからtarget×moveを直接joint predictionするsemantic identity birth
- B #353: identity / operation / goalの分離可能性
- D #355: prospective取得を通過したunitだけをmemory eligibleにする監査
- E #356: post-treatment witness仮説族HF-006を凍結しAF-004を本線化
- C本Cycle: 座標変換・object permutationを跨ぐpre-treatment causal identityの必要十分性監査

## 3 seed平均

Joint chanceは1/32 = 0.03125。

| 条件 | Equivariant joint | Absolute joint | Shuffle joint |
|---|---:|---:|---:|
| Held | 0.0722 | 0.0389 | 0.0556 |
| Rotation | 0.1000 | 0.0722 | 0.0667 |
| Translation | 0.0889 | 0.0444 | 0.0778 |
| Object permutation | 0.1056 | 0.1056 | 0.0778 |
| 計画取り消し | 0.0667 | 0.0389 | 0.0556 |
| 自由日本語 | 0.0444 | 0.0778 | 0.0278 |
| 別domain | 0.0389 | 0.0167 | 0.0389 |

Target accuracyではEquivariantがHeld 0.3778、Permutation 0.3556、自由日本語0.3167となり、chance 0.125を上回った。しかしshuffleもHeld 0.3111、Permutation 0.3056で高く、joint Correct-shuffle差は小さい。

## 判定

**中核仮説は反証。能力上の進歩は認定しない。G1未達。**

変換可換な候補中心relation表現は、絶対座標表現よりHeld・Rotation・Translation・計画取り消しでjoint accuracyを改善した。したがって、座標系やobject indexを除去することは対象再同定の必要条件寄りである。

しかし、次の理由でsemantic causal unitの十分条件ではない。

1. HeldのEquivariant 0.0722に対しshuffle 0.0556で差は0.0167に留まる。
2. Translationも0.0889対0.0778で差は小さい。
3. 別domainはEquivariantとshuffleが0.0389で完全同一。
4. 自由日本語はjoint差が0.0167で、move accuracyはchance未満。
5. Object permutationではAbsoluteもEquivariantと同じ0.1056で、改善の一部はdataset symmetryとcandidate tieで説明できる。
6. non-target preservationは候補実行器の構造上常に1.0であり、学習した因果理解の証拠ではない。

結論として、**変換可換性はsurface座標依存を減らすが、raw Japaneseの語彙・操作方向と世界変化を因果的に束縛しない**。関係multisetだけでは、同じrelative geometryを持つ複数対象のうち、なぜその対象を選び、その操作を行うかを識別できない。

## A/B/D/Eへ返す知見

- A: 次のunit birthではpaired coordinate worldだけでなく、同じgeometryでtarget/operation/goalだけを独立交換する四方向対照が必要。変換可換性だけをidentity証拠にしない。
- B: operationはcoordinate transformに応じて共変しなければならないが、identityとoperationのjoint scoreではなく、same identity/different operationとdifferent identity/same operationを別lossで監査する必要がある。
- D: Equivariant target signalはshuffle差が小さく別domain差0のためmemory eligibilityなし。保存・干渉評価を開始しない。
- E: AF-004は継続可能だが、「transformation equivariance alone implies semantic identity」という下位仮説は不採用。次の最大ボトルネックは語彙・対象・操作を独立介入しても保たれるcross-modal causal factorization。

## 資源量

- Matrix: 8,192 bytes
- Peak RSS: 167,332 KiB（Python runtime込み）
- 3 seed total: 12.6745 sec
- Update: 約2,048 ops/episode
- Candidate inference: 約2,048 ops/option
- 32 options: 約65,536 ops/query
- 1GB未満: 達成
- 弱いスマートフォンCPU実機: 未検証

## 次の仮説

**Intervention-Factorized Causal Unit Birth from Four-Way Symmetry Breaking**

同じpre-treatment geometryについて、identity、operation、goal、surface wordingのうち一つだけを交換した4方向counterexampleを生成し、

- identity交換でtargetだけが変わる
- operation交換でdeltaだけが変わる
- goal交換でranking criterionだけが変わる
- wording交換でlatent causal unitが不変

というresponse factorizationを満たすunitだけを形成する。Correct alignment / independently shuffled identity / operation / goal / wordingを比較し、before+commandから別domainのtarget×transition jointでCorrect-shuffle差0.10以上を必須とする。

- Semantic Identity Gate G1: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
