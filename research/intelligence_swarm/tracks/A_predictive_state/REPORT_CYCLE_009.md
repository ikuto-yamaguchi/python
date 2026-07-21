# 系列A Cycle 009 研究報告

## 仮説

**Multi-Timescale Predictive Evidence Semantics with Structural Drift Causes**  
（構造的drift原因を持つ多時間尺度予測証拠意味）

Cycle 008では、話者×返答表面ごとのchange-point stateにより急激・話者局所driftの誤確定を削減できた。一方、変化直後、漸進drift、未知表面、引用・否定・訂正scopeは未解決だった。

本Cycleでは、同じ証拠文字列の運用意味を以下の時間尺度へ分離した。

- global surface state
- speaker-local state
- episode-local state
- fast recent state
- reversible contradiction ledger

学習器が受け取るのは、生の日本語返答、話者ID、episode境界、後続の汎用成功/失敗だけである。正答world value、肯定/否定ラベル、意味slot、形態素解析、固定ontology、RAG、外部LLMは与えていない。

## 先行研究

- Active Predictive Codingは、予測誤差を通じて知覚・行動・構成表現・階層計画を統合する方向を示す。ただし本Cycleが扱う証拠意味の非定常性とopen-set日本語構造生成は直接解かない。  
  https://pubmed.ncbi.nlm.nih.gov/38052084/
- Bayesian online learningで不規則なdistribution shiftを複数change-point仮説として追跡し、変化時に過去情報を部分的に弱める方式が報告されている。  
  https://proceedings.neurips.cc/paper/2021/hash/362387494f6be6613daea643a7706a42-Abstract.html
- 2026年の音声理解研究は、speaker-specific semantic priorと高次semantic prediction errorが異なる階層で共存することを示した。  
  https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3003588

## 他4系列との重複表

| 系列 | 最新中心機構 | 成功 | 失敗・未解決 | A候補との判定 |
|---|---|---|---|---|
| B Cycle 009 | cross-episode permutation-complete anti-unification | 実行監査をMDL前段へ移す問題分解 | 単一episode再現ではcandidate precision改善なし、平均約150候補 | program候補生成は重複のため棄却 |
| C Cycle 009 | mechanism-factored intervention tensor | 同一contextのmissing operation補完1.0 | 未知context 0.2875、順序反実仮想0 | 因果機構形成は重複のため棄却 |
| D Cycle 009 | open-set discourse event segmentation memory | 未知follow-up retrievalを0.2333へ部分改善 | event F1約0.015、gap/干渉0 | event境界・長期記憶は重複のため棄却 |
| E Cycle 009 | outcome-vector factor sufficiency | candidate recallとoutcome非同型性を分離 | local factor separability不足で精度0 | energy/credit routingは重複のため棄却 |
| A Cycle 009 | 証拠意味のglobal/speaker/episode/fast state | 本Cycleで検証 | open-set scope意味と候補world生成 | 系列固有 |

継承した知見:

- B: 内部整合だけでは現実意味を保証しない。
- C: 高精度な同一context補間を機構理解と混同しない。
- D: 証拠がどのevent stateへ作用するかも不確実。
- E: 候補が異なっても局所的な識別featureがなければ選べない。

## 実装

比較方式:

1. `StaticModel`
   - 全履歴を一つのsurface prototype集合へ統合。
2. `MultiTimescale`
   - global, speaker, episode, fast の各raw-text prototypeを別々に保持。
   - 各尺度の予測を重み付き投票。
   - fast stateは同じ話者・同じ表面について直近12件だけ保持。
   - 後続失敗ではrollback履歴を増やし、矛盾時に新しいfast stateをfork。

### 反証条件

- stable性能が維持されるか
- abrupt reversal
- speaker-local reversal
- episode-local convention
- 引用・否定・訂正scope
- gradual drift
- 完全未学習surface
- 誤答と過剰棄権を分離
- 候補worldは実験器供給であることを統合ゲートで明示

## 実験条件

- train sizes: 64 / 256 / 512
- seeds: 1 / 7 / 19
- 各scenario: 300 episode
- delayed evidence: generic action success/failureのみ
- 正答valueの後続漏洩なし

## 最大512例・3 seed平均

| 条件 | Static accuracy | Multi accuracy | Static wrong commit | Multi wrong commit | Multi coverage |
|---|---:|---:|---:|---:|---:|
| stable | 1.0000 | 0.7756 | 0.0000 | 0.0000 | 0.7756 |
| abrupt | 1.0000 | 0.8022 | 0.0000 | 0.0078 | 0.8100 |
| speaker-local | 0.9633 | 0.7667 | 0.0367 | 0.0489 | 0.8156 |
| episode-local | 0.8000 | 0.6433 | 0.2000 | 0.1656 | 0.8089 |
| quote/negation/correction | 0.9511 | 0.2922 | 0.0489 | 0.1333 | 0.4256 |
| gradual | 0.9711 | 0.7700 | 0.0289 | 0.1167 | 0.8867 |
| held surface | 0.7822 | 0.4944 | 0.2089 | 0.1878 | 0.6822 |

## 資源

- Static model: 8016 bytes
- Multi-timescale model: 111868 bytes
- Static prototypes: 88.3
- Multi-timescale prototypes: 1596.7
- Multi inference:
  - stable 1.0087 ms
  - scope 1.5629 ms
  - held 2.2050 ms
- local reads: 9.50–11.99
- forks: 119.0
- rollbacks: 769.0
- Peak RSS: 397632 KiB（Python runtime込み）
- 推定計算量: `O((P_global + P_speaker + P_episode) * G)`、上位12局所読出し

## 判定

**中核仮説は強く反証。**

### 1. 多時間尺度化が全体性能を悪化

Multi-timescaleはstatic方式より全scenarioでaccuracyが低い。stableで1.0000から0.7756、held surfaceで0.7822から0.4944へ後退した。

局所状態を増やすほど証拠が分散し、各尺度のsupportが薄くなった。これは構造的意味分解ではなく、同じsurface prototypeを階層別に重複保存しただけである。

### 2. scope構造を理解しない

quote/negation/correction accuracyは0.2922、coverage 0.4256。引用・否定・訂正のscopeを構造edgeとして持たず、全文n-gram prototypeの類似で投票している。

### 3. gradual driftで誤確定が増加

Multi wrong commit 0.1167に対しstaticは0.0289。fast stateとslow stateの競合を予測誤差で校正できず、局所drift候補が誤ったsurface meaningを強化した。

### 4. open-set表面理解に失敗

held surfaceはaccuracy 0.4944、wrong commit 0.1878。棄権だけでなく誤確定も多く、未知表面を対話行為・scope・証拠役割へ分解していない。

### 5. 記憶量が悪化

Multi modelは約111.9KBでstatic約8.0KBの約14倍、prototype数も約18倍。1GB未満ではあるが、弱いスマートフォン向け原理としての容量スケーリングは不成立。

### 6. 候補world生成は未着手

今回もworld hypothesesは実験器が供給している。生の日本語から対象・変数・関係・操作・目的・制約・因果候補を生成した証拠ではない。

## 系列A固有の進展

証拠意味の非定常性を以下へ分解できた。

1. 時間尺度を分けて保存すること
2. drift原因を構造化すること
3. 各構造が異なる将来観測を生成すること
4. 予測誤差を原因edgeへ帰属すること

今回実装したのは1だけであり、2〜4がないと多時間尺度化は単なるprototype複製となる。

> global / speaker / episode / fast stateを用意するだけでは意味の階層化にならない。各状態が引用・否定・訂正・話者規約について異なる予測を実行生成し、原因edgeへ誤差を帰属できる必要がある。

## 他系列へ返す新知見

- B: 同じsurface primitiveを階層別に複製しても意味構造にはならない。各階層programが異なる実行結果を生成する必要がある。
- C: speaker/episode condition nodeは、異なるoperation signatureを生成しなければ単なるcontext prototypeである。
- D: fast/slow memoryを分けるだけではevent理解にならず、境界候補ごとの未来想起差が必要。
- E: 多時間尺度state間のcredit routingには、scope/cause edgeの局所Jacobianが必要。

## 次の仮説

**Causal-Scope Predictive State Forks with Edge-Specific Error Routing**  
（因果scope予測状態forkとedge別誤差routing）

次はglobal/speaker/episodeという保存箱を先に固定しない。生の発話から次の少数候補graphを生成する。

- literal assertion
- quotation
- negation
- correction/retraction
- speaker-local convention
- episode-local convention

各候補は、次発話、承認/否定、行動成功、訂正発生、speaker transferに異なる予測を生成する。各scope edgeだけを削除・反転した有限差分により、prediction errorを原因edgeへroutingする。

必須成功条件:

- stable accuracy 0.7756を改善
- scope accuracy 0.2922を改善
- gradual wrong commit 0.1167を低減
- held accuracy 0.4944を改善
- model 32KB未満
- prototypeの階層重複保存を廃止
- 候補world生成の統合ゲートを別途実施

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
