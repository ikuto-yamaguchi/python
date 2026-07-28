# RESET-E048 — R0 Research Reconstruction

Date: 2026-07-26
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope

A〜Dへ新しいtoy仮説、別branch、新規機構族を許可しない。公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを同じcanonical branchへ累積する。既存stacked draft PRはnegative-results archiveとして扱い、新作業のbaseにしない。

## Evidence audit

受理可能な新しいR0.1、J-CRe3、J-ORA、R0.2数値artifactは確認できなかった。監査系workflow success、文書更新、run request、queued/cancelled runは能力進歩に数えない。

維持するaccepted SILG evidenceは32,768-frame runのみである。

- Correct: `1/60`
- Random: `4/60`
- Language-blind: `1/60`
- State-only: `1/60`
- Language-shuffle: `1/60`
- parameters: `4,916,915`
- state-dict: `19,694,385 bytes`
- peak RSS: `505,600 KiB`
- three-seed wall time: `1,033.885 s`
- CPU forward: `6.911 ms/step`

これはcompetent public baselineではなく、`initial_reproduction_failure`を維持する。

## Execution decision

「検証したが駄目」でcycleを閉じることを禁止する。不合格runは以下が揃うまで未完了とする。

1. evidence-backed failure classification
2. one changed causal factor
3. fixed frames/model family/split/instances
4. matched rerun
5. adopt/reject/stop decision
6. stopping conditionを満たさない場合の次screening request

R0.1は最大6件のsingle-factor screeningを、公式差分、recurrent/optimizer、optimization、capacity allocation、fusionの順で行う。R0.2は`qualified_for_r02=true`まで開始しない。

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまでauditorを追加しない。各runでrandom、language-blind、state-only、applicable shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。

## Prior-art audit

Markham et al., *Intervening to learn and compose causally disentangled representations*, CLeaR 2026は、任意のblack-box generative modelへ介入型context moduleを加え、因果的にdisentangledな概念表現とOOD compositionを学ぶ枠組みおよび識別結果を提示する。

したがって以下はRQ-001の新規性候補から除外する。

- intervention-conditioned context module
- causal concept disentanglement
- learned representationのcompositional reuse
- OOD concept composition自体

公式repositoryとexact commitは今回固定できていないため、再現済みbaselineとは扱わない。

LeGITのlanguage-guided intervention selection境界、2025 score-based CRL、2026 finite-sample unknown-target CRL境界も維持する。

## RQ-001 decision

> **NARROWED BEYOND LANGUAGE-GUIDED TARGET SELECTION AND INTERVENTION-CONDITIONED COMPOSITION — NOT ADOPTED**

採用には、最強の非言語CRL、LeGIT型target-selection、介入context-module型compositionの再現後にも残るcountermodel pair、外部固定でjoint recoding不能なdenotation law、language固有追加情報の直接証拠、事前登録済みclaim/counterexample/stopping ruleが必要である。

## Stage status

- R0.1 immutable competence bundle: **0**
- external learned baseline reproduction: **0**
- J-CRe3 numerical reproduction: **0**
- R0.2 qualified reproduction: **0**
- R0.3 hidden intervention-target ablation: **rejected**
- novelty matrix: **incomplete**
- central-claim preregistration: **incomplete**
- new mechanism family: **not recognised**
- new intelligence principle: **not discovered**
- capability progress: **not recognised**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**
