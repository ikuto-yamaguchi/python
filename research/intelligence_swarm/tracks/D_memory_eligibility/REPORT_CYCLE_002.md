# 系列D Memory Eligibility Cycle 002

## 仮説

**Time-Indexed Prospective Eligibility before Retention**

PR #352 の日本語–trajectory陽性と PR #354 のpost-treatment leakage監査を受け、記憶資格を次の4段階へ分離した。

1. 完成trajectoryを用いる事後取得
2. 介入前に利用可能なprefix witnessによる取得
3. 未知表現・別domain・inverse queryでのprospective closed-loop利用
4. 上記を通過した単位だけに対する干渉後保持

semantic identity未成立のままaddress、replay、assembly、fast/slow memoryを作らない。保持測定は取得資格通過後のみ意味を持つ、という仮説を検証した。

## 最新証拠との統合

- PR #352: held日本語と完成trajectoryでは Correct 0.2431 / Shuffle 0.1233。ただし別domainでは差が消失。
- PR #353: operation、goal、failure repairはchance近傍でG2未達。
- PR #354: 完成trajectoryの陽性はpost-treatment情報に依存し、prefix witnessでは差が縮小。
- PR #351: Stage S1、G1未達、保存最適化は凍結継続。

## 方法

raw Japanese全体を128次元hashed feature、観測witnessを64次元featureへ写像し、局所Hebbian外積だけを学習した。

候補側witnessを以下に分離した。

- `full`: 完成trajectory + scar（事後情報）
- `prefix1`: 最初の1 stepのみ
- `prefix2`: 最初の2 stepのみ
- `scar`: episode固有scarのみ

各方式をCorrect / episode対応shuffle / disjoint-domain日本語 / 24 distractor interferenceで比較した。3つの未知言い換えに対する一貫性とinverse queryも同時に測定した。

記憶資格は、pre-treatment witnessであり、acquisition accuracy 0.25以上、Correct-Shuffle差0.10以上、別domainでchance+0.10以上、inverse accuracy 0.25以上を全3 seedで満たす場合だけ認定した。

## 3 seed平均

8択chanceは0.125。

| Witness | Correct | Shuffle | 差 | 別domain | Inverse | 3-form一貫 |
|---|---:|---:|---:|---:|---:|---:|
| full | 0.1944 | 0.1319 | +0.0625 | 0.1528 | 0.1250 | 0.1146 |
| prefix1 | 0.1319 | 0.1042 | +0.0278 | 0.1632 | 0.1875 | 0.1007 |
| prefix2 | 0.1528 | 0.1042 | +0.0486 | 0.1285 | 0.1736 | 0.1007 |
| scar | 0.1215 | 0.1250 | -0.0035 | 0.1215 | 0.1111 | 0.1146 |

干渉監査accuracyは full 0.2153、prefix1 0.1285、prefix2 0.1736、scar 0.1389だった。ただし資格通過方式は0件であり、これらをsemantic retentionとは解釈しない。

## 判定

**監査仮説は支持。能力上の進歩は未認定。G1未達。保存最適化は凍結継続。**

完成trajectoryはCorrect-shuffle差を示したが、事後情報でありprospective資格外である。prefix1/2は小さな差を示したものの、accuracy、別domain、inverse、一貫性の全てが資格閾値を満たさなかった。

現在の失敗分類は次の通り。

- full: retrospective matching only
- prefix1 / prefix2: initial semantics failure
- scar: post-treatmentまたはepisode-specific witness
- catastrophic forgetting: 観測されず
- semantic memory eligible unit: 0
- consolidation mainline: 再開不可

干渉後に数値が上下しても、取得時にsemantic closed-loopが成立していないため破滅的忘却ではない。

## 系列固有の進展

内部memory構造を追加せず、**記憶資格を観測時刻と利用方向で分離するgate**を明示した。これにより、事後照合の陽性を取得成功、干渉後の偶然変動を保持・忘却と誤分類することを防いだ。

## 他系列へ返す知見

- A: identity proposalにはwitnessの観測時刻を付与し、介入前だけで3-form一貫性とinverse利用を成立させる必要がある。
- B: operation unitは作用前target選択と作用後結果照合を分離する必要がある。
- C: episode identityにはpre-treatment witness、prospective rollout、retrospective witnessを別channelとして提供する必要がある。
- E: G1aに「取得資格通過前のretention報告禁止」を追加すべき。

## 資源量

- Matrix: **32,768 bytes**
- Peak RSS: **113,608 KiB**（Python runtime込み）
- 3 seed総時間: **31.919 sec**
- Update: **8,192 ops/episode**
- Inference: **8,192 ops/candidate**
- 8候補・3表現一貫性: 約 **196,608 ops/query**
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 次の一点

**Pre-Treatment Cross-Episode Identity from Relational Change Prediction**

絶対trajectory prefixを直接照合せず、介入前の対象間関係とcommandから、どの対象のどの将来変化が生じるかを複数episodeで予測する。同じunitが未知表現・別domain・inverse query・3-form一貫性を全て満たした場合だけDへ渡し、その後に初めて干渉保持を測定する。

- Semantic Identity Gate G1: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
