# 系列A Cycle 042

## 仮説

**Prediction-Residual State Rebirth from Post-Event Counterexample Synthesis**  
（event後反例合成による予測残差駆動state再生）

Cycle 041ではevent境界後に既存ruleを再rankingしてもOne-step方式から一件も選択が変わらなかった。今回は境界後2turnの失敗予測残差から、state区間とcommand value区間をexpand・contract・shiftして新ruleを生成した。

比較:
- One-step
- Boundary-only
- Residual rebirth
- Shuffled post-event targets

Final testのafter/futureは通常rankingには使わず、rebirth学習時のpost-event counterexampleとしてのみ使用した。したがって本実験はonline adaptation能力の検証であり、純粋zero-shotではない。

## 重複表

| 系列 | 最新中心 | Aで分離した領域 |
|---|---|---|
| B Cycle 041 | 削除因果role grammar | MDL・記号圧縮 |
| C Cycle 041 | Leave-one-world-out relation axis | 因果world補完 |
| D Cycle 041 | Interference-graph memory assembly | 長期memory・slow統合 |
| E Cycle 041 | Leave-one-counterexample-out constraint mode | Energy固定点 |
| **A Cycle 042** | **event後残差から時間状態ruleを新生し次turnへ再入** | 今回の固有対象 |

## 3 seed平均

| 条件 | One-step 精度/wrong | Boundary-only 精度/wrong | Rebirth 精度/wrong | Shuffle 精度/wrong |
|---|---:|---:|---:|---:|
| 対象切替 | 0/0 | 0/0 | 0/0 | 0/0 |
| 主語省略 | 0/0.6667 | 0/0.0139 | 0/0.0139 | 0/0.4722 |
| 未知語順 | 0/0 | 0/0 | 0/0 | 0/0.1389 |
| 複数段落 | 0/0.4583 | 0/0.1389 | 0/0.1389 | 0/0.3611 |
| 計画変更 | 0/0 | 0/0 | 0/0 | 0/0.3333 |
| 反実仮想 | 0/0 | 0/0 | 0/0 | 0/0.1389 |

追加診断:
- Rebirth rule: 21.67
- Correct rebirth births: 対象切替0、主要条件も0
- Shuffled births: 主語省略18、未知語順20、計画変更10.33、反実仮想20
- Post-boundary correct execution: 0
- Model: 約773 bytes
- Training: 約0.0125 sec
- Inference: 約0.18〜0.33 ms/example
- Peak RSS: 167,244 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

Correct-order residual rebirthはpost-boundary executionを一件も改善しなかった。一方、shuffled post-event targetでは多数のrule birthが発生した。生成操作は意味的event contrastではなく、surface mismatch量へ反応している。

Boundary-onlyは主語省略wrongを0.6667→0.0139、複数段落wrongを0.4583→0.1389へ減らしたが、accuracyは増えない。これは旧state停止による棄権増加であり、新state再生ではない。

今回の生成設定では多くのturnでobjectが変わるためboundary F1が飽和しており、意味的event segmentationの証拠として使えない。重要評価であるpost-boundary executionは0だった。

> **Post-event residual synthesisはcandidate birthを起こせても、意味的state identityを生成しない。時間順序に固有な予測責任を持たないbirthは、単なるsurface repairである。**

## 資源量

- Model: 約773 bytes
- Training: 約0.0125 sec
- Inference: 約0.3 ms/example
- Candidate上限: 32
- 計算量: induction `O(NL²)`、online評価 `O(TR)`、residual birth `O(kRM)`、`k=2`

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列A固有の進展

Boundary-only停止gateの安全効果は再確認できた。しかしevent後残差からの局所rule新生はCorrect order固有ではなく、shuffleでむしろ増えた。State rebirthにはsurface差分ではなく、複数turnへ予測責任を持つ時間creditが必要である。

## 他系列へ返す知見

- B: Counterexampleからproductionをbirthする場合、shuffleよりCorrectで生成率と実行率が高いことを必須化すべき。
- C: 欠測world補完信号とprospective inputからのevent birthを分離する必要がある。
- D: Replay residualによるaddress birthもrandom replay mismatchで増える候補を棄却すべき。
- E: Missing-world constraint modeは候補数ではなくcorrect-order fixed-point変化で評価すべき。

## 次の仮説

**Prospective Responsibility Traces for Order-Specific State Rebirth**  
（順序固有の将来予測責任traceによるstate再生）

1. Rebirth候補へ未来3turnの予測責任を割り当てる
2. 現在afterの修復だけではcreditを与えない
3. Future継続・主語省略・object切替・goal撤回を独立channel化
4. Correct順序でのみ累積lossを減らす候補を保持
5. Temporal shuffle、future shuffle、one-step residual、boundary-onlyを比較
6. 対象切替でpost-boundary executionとwrong carryを同時改善
7. 計画変更で撤回stateを終了し最終stateを再生
8. 反実仮想では実行・非実行traceを並行保持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
