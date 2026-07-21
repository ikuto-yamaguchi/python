# 系列A Cycle 008 研究報告

## Predictive Evidence-Channel Change-Point States

## 結論

静的な返答信頼度では扱えなかった「同じ日本語表現の運用意味が会話途中・話者ごとに変化する」条件に対し、返答表現ごとの局所予測誤差をイベントとして監視し、証拠channel状態をfork/resetする最小機構を検証した。

**限定的支持:** 急激な意味反転・話者固有反転では、静的channelより誤確定を大幅に削減した。候補世界の状態だけでなく、観測channel自体へrun-length・暫定変更状態・rollback履歴を持たせる必要がある。

**中核仮説は反証:** 変化直後の即時適応、漸進drift、完全未学習表現、自由日本語からの対象・変数・操作・目的・制約・因果候補生成は未成立。候補世界は実験器から供給され、証拠channelも二値質問応答へ限定される。

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false

## 開始時に読んだ共通知見

- `research/intelligence_swarm/STATE.md`: 1GB未満・弱いCPU・自由日本語構造創発が共通mission。高校生級・ネイティブ日本語・実機検証はいずれも未達。
- `research/intelligence_swarm/EVIDENCE.jsonl`: 共通branch上の証拠台帳を確認。
- `research/intelligence_swarm/BACKLOG.md`: 境界候補、将来予測・介入整合性、内部整合性と現実妥当性の分離がP0。
- 最新研究PR #175–#179、および系列Aの過去失敗PR #150/#155/#160/#165/#170/#175を確認。

## 他系列との重複表

| 系列 | 最新仮説・中心機構 | 実装・成功 | 失敗・未解決 | 系列A候補との重複判定 |
|---|---|---|---|---|
| B | Execution-First Anti-Unification / 実行可能program生成後にMDL統合 | effect bridge、role factoring、圧縮 | executable grounding不足、candidate recall崩壊 | program候補生成・MDLは重複のため棄却 |
| C | Mechanism-Factored Intervention Tensor / 複数operation効果factor | 5種類のeffect signature形成、軽量化 | zero-shot意味転移弱い、誤bridge高確信 | 因果factor生成は重複のため棄却 |
| D | Open-Set Discourse Event Segmentation / fast weight・照応統合 | 既知cueの長gap・topic shift耐性 | 未知cue即時照応、episode候補生成 | 長期記憶・照応統合は重複のため棄却 |
| E | Outcome-Vector Factor Sufficiency / 局所energy・アトラクタ | candidate recallを通常0.978まで改善 | factor不足でmargin 0、全面棄権 | 内部energy緩和は重複のため棄却 |
| A候補1 | 世界候補のopen-set生成 | — | B/C/Eと中心機構・反証条件が重複 | 棄却 |
| A候補2 | 返答prototypeの長期統合 | — | Dと重複 | 棄却 |
| **A採用** | **証拠channelの意味変化点を予測誤差から形成** | 短期world state更新に直結 | drift検出・rollback・話者局所性 | **他系列と非重複** |

## 継承した部分知見

- **A Cycle 007 / PR #175:** 静的surface reliabilityは未知返答を棄権へ変えられるが、既知surfaceの意味反転で確定例が誤る。
- **B Cycle 008 / PR #176:** 内部圧縮や可逆性は、現実に実行可能な意味を保証しない。channel状態も予測結果で監査する。
- **C Cycle 008 / PR #177:** 潜在factorへの高marginは、誤った観測signatureでも成立する。複数時点での予測整合が必要。
- **D Cycle 008 / PR #178:** 暫定edgeと後続反例による撤回を採用。ただし長期記憶ではなく対話中の証拠channelへ適用。
- **E Cycle 008 / PR #179:** 安定収束・正候補recallだけでは不十分。正誤を分ける局所factorとして時間的prediction errorを導入。

## 先行研究整理

参照した研究系譜は次のとおり。

1. Adams & MacKay, *Bayesian Online Changepoint Detection* — run-length分布と予測尤度によるオンライン変化点検出。
2. Sellier & Dellaportas, *Bayesian online change point detection with Hilbert space approximate Student-t process*, ICML 2023 — 非定常系列での予測分散・計算量削減。
3. Bao et al., *CAP: A General Algorithm for Online Selective Conformal Prediction with FCR Control*, JMLR 2025 — online selectionとdistribution shift下の校正。
4. Angelopoulos et al., *Conformal Risk Control*, ICLR 2024 — 内部confidenceではなく運用riskを制御する考え方。

今回の方式は完全Bayes BOCPDではない。1GB未満・弱いCPUを優先し、各話者×表現についてstable stateとtentative post-change stateだけを保持する有限状態近似を用いた。

## 新仮説

> 返答表現の意味を静的prototypeとして保存せず、世界状態更新の成功・失敗を予測誤差イベントとして扱い、証拠channelごとのrun-length、暫定post-change仮説、rollback ledgerを予測状態へ含めれば、既知表現の意味driftに追従できる。

予測状態を次へ拡張する。

`state = world hypotheses + evidence-channel hypotheses + local run length + tentative change state + reversible ledger`

### 既存方式との差

- 静的校正: 全履歴を一つの意味分布へ集約する。
- exponential decay: 新しい証拠を重くするが、話者局所の変更状態と一時的逸脱を分離しない。
- 今回: 話者×表現ごとに局所状態を持ち、連続surpriseでpost-change stateをforkし、再現すれば昇格、矛盾すればrollbackする。

### 反証条件

1. drift時wrong commitが静的・decay方式を下回らない。
2. stable時のcoverage/精度を破壊する。
3. speaker-local driftを他話者へ誤伝播する。
4. temporary drift後に元の意味へ戻れない。
5. gradual driftで変更・rollbackが乱発し性能改善しない。
6. held-out表現を意味的に解釈できず全面棄権する。

## 最小実装

`predictive_evidence_change_point_cycle8.py`

- raw日本語文字2/3/4-gramのみ。
- 事前学習model、形態素解析、固定reply辞書、意味slot、RAG、外部LLMなし。
- delayed feedbackはinteraction success/failureのみで、hidden target valueを含まない。
- 各phraseの状態: `pos/neg/unknown` evidence、run length、surprise run。
- 連続2回のprediction errorでtentative change stateを開始。
- 3回の整合で昇格。矛盾が連続すればrollback。
- 比較: static / exponential decay / change point。

## 実験条件

- seed: 1 / 7 / 19
- warmup: 180 episode
- 評価: 1,200 episode / scenario
- 話者: 3
- scenarios: stable / 全話者abrupt reversal / speaker-local reversal / temporary reversal / gradual drift / completely held-out reply surfaces
- ablation: static aggregate / exponential decay (`0.94`) / change-point state

## 3 seed平均

| scenario | method | accuracy(all) | coverage | selective accuracy | wrong commit | changes | rollbacks |
|---|---|---:|---:|---:|---:|---:|---:|
| stable | static | 0.6603 | 0.6603 | 1.0000 | 0.0000 | 0 | 0 |
| stable | change-point | 0.6603 | 0.6603 | 1.0000 | 0.0000 | 0 | 0 |
| abrupt | static | 0.3056 | 0.6603 | 0.4625 | 0.3547 | 0 | 0 |
| abrupt | decay | 0.6003 | 0.6603 | 0.9091 | 0.0600 | 0 | 0 |
| abrupt | change-point | **0.6303** | 0.6603 | **0.9546** | **0.0300** | 18.0 | 0 |
| speaker drift | static | 0.5161 | 0.6603 | 0.7816 | 0.1442 | 0 | 0 |
| speaker drift | change-point | **0.6503** | 0.6603 | **0.9849** | **0.0100** | 6.0 | 0 |
| temporary | decay | 0.5617 | 0.6603 | 0.8506 | 0.0986 | 0 | 0 |
| temporary | change-point | **0.6003** | 0.6603 | **0.9091** | **0.0600** | 36.0 | 0 |
| gradual | decay | **0.5592** | 0.6631 | 0.8433 | 0.1039 | 0 | 0 |
| gradual | change-point | 0.5458 | 0.6486 | 0.8415 | 0.1028 | 18.7 | 17.3 |
| held surface | change-point | 0.2956 | 0.2956 | 1.0000 | 0.0000 | 0 | 0 |

### 変化直後20件

- abrupt: static 0.0000、decay 0.0000、change-point 0.0500
- speaker-local: static 0.5500、change-point 0.7667
- temporary: decay 0.5500、change-point 0.7500

## 資源量

- change-point model: 2,819 bytes（stable）、held surface追加後4,535 bytes
- static model: 935 bytes
- change-point推論: 0.0049 ms/episode（stable）、0.0062 ms（gradual）
- candidate reads: 5
- 全実験時間: 4.3477 sec
- Peak RSS: 309,428 KiB（Python runtime込み）
- 推定計算量: `O(PG)`、局所状態更新 `O(1)`、このprobeでは `P<=15`
- modelは1GB未満。弱いスマートフォン実機値ではない。

## 支持された部分

1. stable性能を維持したまま、abrupt wrong commitを0.3547から0.0300へ削減した。
2. speaker-local driftではwrong commitを0.1442から0.0100へ削減し、他話者へ意味変更を伝播させなかった。
3. temporary driftでもdecayよりwrong commitを削減した。
4. gradual driftではtentative stateの昇格・rollbackが実際に発生し、証拠channelを不可逆に固定しない機構を確認した。

したがって、**証拠意味の非定常性をworld stateとは別の予測状態として保持する**下流原理は残せる。

## 決定的な反証・反例

### 変化直後には弱い

abrupt reversal直後20件の精度は0.0500。変化点検出には誤りを観測する必要があり、最初の数件を事前に救えない。

### gradual driftではdecayを上回らない

change-point accuracy 0.5458はdecay 0.5592を下回った。離散的fork/resetは、意味が確率的に徐々に変化するchannelへ不向きである。

### held-out日本語は理解しない

held surfaceのcoverageは0.2956。確定時は正しいが、多くを棄権する。表面類似を超えた肯定・否定・保留の対話行為は形成されていない。

### 候補世界は実験器から供給

対象、変数、操作、目的、制約、因果候補を生の日本語から生成していない。二値partitionへの返答channelだけを扱う下流probeである。

### 「意味変化」の原因を表現しない

話者差、皮肉、局所規約、訂正、引用、否定scopeのいずれが変化原因かを構造化していない。speaker×surfaceの局所統計を分けただけである。

## 統合評価

### 系列A固有の進展

Cycle 007の静的channel信頼度から次へ進んだ。

- channel stateを時間的に非定常な潜在状態として扱う。
- stable / tentative post-changeを同時保持する。
- prediction errorをイベントとして局所更新する。
- 一時的変化・矛盾時にrollbackする。

### 他系列へ返す新知見

- **B:** effect evidenceの表面意味も非定常。primitiveへ統合する前にchannel change stateを監査する。
- **C:** intervention結果channelが装置・話者・時点で変化する場合、同じsignatureを因果factorへ固定してはいけない。
- **D:** 記憶edgeだけでなく、そのedgeを支持した証拠channelのrun-lengthと変更履歴も保存する。
- **E:** energy factorの意味が変化した場合、過去weightのまま安定収束しても誤り。factor reliabilityへ時間状態が必要。

## 次の仮説

**Multi-Timescale Predictive Evidence Semantics with Structural Drift Causes**
（構造的drift原因を持つ多時間尺度予測証拠意味）

次は単一change/resetではなく、証拠channelを次の合成状態として表す。

- global surface意味
- speaker-local意味
- episode-local規約
- 引用・否定・訂正scope
- fast drift state
- slow semantic state

各時間尺度が、次発話、行動成否、後続訂正、別channel整合をどれだけ予測するかで責任分配する。

必須成功条件:

1. stable coverage/accuracyを維持。
2. abrupt直後20件精度0.0500を改善。
3. gradual accuracy0.5458をdecay以上へ改善。
4. held coverage0.2956を改善しつつwrong commitを増やさない。
5. speaker driftとepisode-local temporary driftを異なる状態として識別。
6. rollback後に旧意味へ復帰。
7. 候補生成済みという制限を明記し、自由日本語統合ゲートを別評価する。

## 再現

```bash
python research/intelligence_swarm/tracks/A_predictive_state/predictive_evidence_change_point_cycle8.py \
  --output research/intelligence_swarm/tracks/A_predictive_state/results_cycle_008.json
```
