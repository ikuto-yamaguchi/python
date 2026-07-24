# Governance Cycle 008

## Decision

**S1継続・substage遷移・HF-011凍結・AF-009昇格**

- Stage: S1 Semantic Identity Birth
- New substage: intervention-residual candidate birth
- G1: 未達
- G2: 未達
- Formal memory eligibility: 未達
- Frozen: HF-011 Selector or Version-Space Collapse Creates Semantics without Candidate Support
- Active priority: AF-009 Intervention-Residual Joint Candidate Birth
- AF-008: qualification/audit scopeへ縮小

## External capability evidence only

### PR #376 — A

- hidden d3自由日本語 joint: Active 0.1181 / Random 0.0486 / Shuffle 0.0139
- hidden d3未知語順 joint: Active 0.0694 / Random 0.0764 / Shuffle 0.0417
- hidden d3複数段落 joint: Active 0.0625 / Random 0.0764 / Shuffle 0.0347
- hidden d3Rename joint: Active 0.0278 / Random 0.0486 / Shuffle 0.0069
- strict gate: 0/3 seed

局所的な自由日本語陽性はあるが、未知語順・複数段落・Rename・d1・全seedへ再現しない。world側の結果分離だけではlanguage ambiguityを解消しない。

### PR #378 — B

- Held joint: Joint 0.0625 = World-only 0.0625
- 未知語順 joint: Joint 0.0208 = World-only 0.0208
- 複数段落 joint: Joint 0.0625 = World-only 0.0625
- 自由日本語 joint: Joint 0.0417 = World-only 0.0417
- strict gate: 0/3 seed
- oracle selectorでもhidden-domain prospective/inverse/goal/repairを改善しない

language entropyを追加しても介入選択順位が変わらず、oracleでも改善しないため、主因はselector failureではなくcandidate-support failureである。

### PR #375 — D

- Active survivor: 0.3333
- Random survivor: 0.3333
- Outcome-shuffle survivor: 0
- Correct候補集合が空: 2/3 seed
- Formal memory eligibility: 0

外部介入は誤対応候補を破壊できるが、正しい候補を生むことはできない。AF-008は資格監査として有効だがbirth原理ではない。

## Frozen family HF-011

Root premise:

> 正しいsemantic candidateが候補集合に存在しなくても、active selector、joint version-space entropy、oracle action、intervention survivalを改善すればsemantic unitが成立する。

Freeze reason:

A/B/Dの3系列で、selector・joint weighting・oracle・survivalを変えてもstrict gate 0、formal eligibility 0、またはCorrect候補全滅となった。

Allowed residual use:

- candidate-support監査
- oracle upper bound
- action/test leakage監査
- residual-born候補の資格認定

## Promoted family AF-009

全候補がcalibration介入結果を説明できないepisodeをbirth triggerとし、次を共同生成する。

- raw Japanese説明不能残差からlanguage transformation candidate
- prediction-observation residualからworld intervention candidate
- 両残差を同時に減らす最小局所変換対

### Required baselines

- Existing-candidate selector
- Random birth
- Language-residual-only
- World-residual-only
- Joint residual birth
- Residual shuffle
- Pair shuffle
- Outcome shuffle
- Oracle candidate-support

### Required data separation

1. initial candidate induction
2. calibration intervention selection
3. observed outcome and residual birth
4. AF-008 survival qualification
5. final held-out evaluation

Calibration afterはresidual birthに利用できるが、final after/test outcomeはcandidate birth・selection・rankingに使用しない。

## Track reassignment

- A: raw-language residual candidate birth
- B: missing operation/goal component birth and oracle support audit
- C: causal transfer audit of residual-born candidates
- D: residual-born eligibility plus intervention survival
- E: after/oracle/domain-bridge/best-seed leakage governance

## Maximum bottleneck

全候補不適合episodeから新生した同一のlanguage/world局所変換候補を、独立episodeと完全語彙非共有hidden domainへ転送し、prospective・inverse・repairを同時に改善すること。

## Progress gate

2以上のopaque domain × 3 seedすべてで、同一born unitがprospective target×transition、inverse、counterfactual repairについて、Existing-selector / Random-birth / Residual-shuffle / Pair-shuffle / Outcome-shuffleを各+0.10以上上回り、その後AF-008の実介入一意生存監査を通過すること。

## Status

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
