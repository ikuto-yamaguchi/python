# 系列A Cycle 013 研究報告

## 仮説

**Survival-Calibrated Active Probe Programs with Coverage-Constrained Null States**
（生存率校正型active probe programとcoverage制約付きnull state）

Cycle 012では候補削減量をprobe utilityにするとseen精度が0.3167から0.0278へ悪化し、null併用ではseenの98.33%を拒否した。本Cycleではprobe utilityを、cross-episodeでの正候補生存率、誤候補除去率、候補分割の均衡で校正し、nullを絶対生存率で制約した。

## 重複表

| 系列 | 最新中心 | 成功 | 失敗 | A候補との判定 |
|---|---|---|---|---|
| B | 実行的misapplicationとrelation quotient | 候補削減 | relation未形成 | program inductionは棄却 |
| C | 時系列介入持続からobject node | object identityを上流化 | text clause surgery失敗 | 因果object形成は棄却 |
| D | cross-query write/read不変性 | 圧縮・局所write | address未形成 | 長期memoryは棄却 |
| E | residual-cause二部attractor | 多残差の必要性 | 誤一意化/平坦化 | 内部energy routingは棄却 |
| A | 外部probeのsemantic survival校正 | 今回検証 | raw候補生成・null coverage | 系列固有 |

継承知見:
- B: 候補削減は意味発見ではない。
- C: surface surgeryはobject/relation誤差へ帰属できない。
- D: target gainのみでは非対象干渉を見落とす。
- E: 相対分離と絶対現実適合性を分ける。

## 実装

raw日本語から句読点・括弧格子と局所文字区間を最大24候補生成した。probeは削除・左右交換・反転の4種類。環境はgeneric binary outcomeのみを返し、正答文字列は返さない。

比較:
1. entropy-only
2. survival-calibrated
3. survival-calibrated + null

## 最大1024学習例・3 seed平均

| 条件 | 候補recall | Entropy精度/誤確定 | Survival精度/誤確定 | Survival+Null精度/誤確定/null |
|---|---:|---:|---:|---:|
| seen | 0.1648 | 0.0093/0.2556 | 0.0093/0.4741 | 0.0093/0.4741/0.5167 |
| paraphrase | 0.1722 | 0.0000/0.2796 | 0.0000/0.1759 | 0.0000/0.1759/0.8241 |
| nested | 0.0889 | 0.0296/0.3056 | 0.0296/0.2352 | 0.0296/0.2352/0.7352 |
| subject omission | 0.0000 | 0.0000/0.2019 | 0.0000/0.3037 | 0.0000/0.3037/0.6963 |
| out-set | 0.0000 | 0.0000/0.3241 | 0.0000/0.1741 | 0.0000/0.1741/0.8259 |

## 判定

**中核仮説は強く反証。**

- survival校正はparaphrase/nested/out-setの誤確定を一部減らしたが、seenでは0.2556から0.4741へ悪化。
- 正候補生存率は全probeで1.0となり、probe間の意味差を識別しなかった。
- seen候補recallは0.1648、paraphrase 0.1722、nested 0.0889、主語省略0。
- nullはout-set null率0.8259まで上げたが、既知でも0.5167を拒否し、accuracyは0.0093のまま。
- probeは文字hash fingerprintであり、世界介入・意味的保存・future retrievalを生成していない。
- 候補生成失敗が支配的で、active inferenceは上流proposal failureを救えない。

限定的知見:
> 候補削減量だけでなく正候補生存率を監査する必要はあるが、正候補生存率が表面fingerprintで飽和するとutility校正は無意味になる。

## 資源

- model: 約335 bytes
- 推論: 0.3651 ms/example
- 候補: 24
- probe: 最大4
- Peak RSS: 389352 KiB（Python runtime込み）
- 計算量: proposal `O(L²)`, active `O(PH)`
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 系列A固有の進展

active probe評価を、
1. entropy reduction
2. correct-hypothesis survival
3. non-target preservation
4. absolute reality fit
5. coverage loss
へ分離した。

今回2を実装したが、表面probeでは全probeが同じ生存率となり、意味的utilityにならなかった。

## 他系列へ返す知見

- B: cross-episode survivalが飽和するprobeはrelation quotientを分割しない。
- C: object persistenceを直接変える介入結果でなければsurvival校正は無意味。
- D: write/read program生存率はtarget queryとunrelated queryを別々に測る必要がある。
- E: residual cause nodeがない状態ではcoverage制約が全面拒否へ退化する。

## 次仮説

**Causal-Survival Probe Programs with Counterfactual Outcome Partitions**
（反実仮想outcome分割を持つ因果生存probe program）

文字hash probeを廃止し、候補ごとに予測される次発話・action outcome・non-target preservation・future recallを局所実行して、異なるoutcome partitionを作るprobeだけを昇格させる。nullはcoverage制約だけでなく、全候補の絶対outcome residualで校正する。

## 最終状態

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: 未達
