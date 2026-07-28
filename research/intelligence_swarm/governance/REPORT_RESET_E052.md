# RESET-E052 Governance Report

Date: 2026-07-26
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope

A〜Dに新しいtoy仮説、別branch、新規機構族を作らせず、公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。既存stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。

## Execution action

`R01_RUN_REQUEST.json`をRESET-E052として再発行した。SILG/RTFM official `multi` recurrent、131,072 frames、seeds `1/7/19`、固定train/test split、same-instance random/language-blind/state-only/language-shuffleを要求する。

成功・失敗にかかわらず、checkpoint、model bytes、peak RSS、training runtime、CPU latency、seed、split、actual frames、raw logs、dependency lock、prediction、qualification JSON、SHA-256 manifest、leakage結果を保存する。

単発失敗でiterationを閉じない。失敗時はmetric/log/code evidenceに基づく分類、変更する単一原因、固定条件、matched rerun、採用・棄却・停止判定、停止条件未達時の次screening requestを必須とする。

## Reproduction status

- immutable R0.1 competence bundle: 0
- learned external public capability baseline: 0
- J-CRe3 numerical reproduction: 0
- J-ORA numerical reproduction: 0
- GPI official-software reproduction: 0
- Multi-View CRL official-code reproduction: 0
- qualified R0.2: 0
- R0.3 hidden intervention-target ablation: rejected and retained

Accepted SILG evidence remains the 32,768-frame run: Correct `1/60`, Random `4/60`, Language-blind/State-only/Language-shuffle `1/60`; parameters `4,916,915`, state-dict `19,694,385 bytes`, maximum RSS `505,600 KiB`, three-seed wall time `1,033.885 s`, CPU forward `6.911 ms/step`. This is policy incompetence, not public capability reproduction.

## Evaluation contract

D015〜D035をfreezeする。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runで以下を確認する。

- random/language-blind/state-only/applicable shuffle
- model/checkpoint bytes
- peak RSS
- training runtime
- CPU latency
- seed/split/actual frames
- commit/dependency/raw logs/checksums
- leakage

## Latest primary-work overlap audit

Baumgartner et al., `Disentangling Dynamical Systems: Causal Representation Learning Meets Local Sparse Attention`, CLeaR 2026を追加した。

同研究は、raw trajectoryからstate-dependent local causal structureを用いてsystem parametersをpermutationとdiffeomorphismまで識別する条件を示し、sparsity-regularised transformerで実装する。よって以下はRQ-001の新規性候補から除外する。

- trajectoryからのsystem-parameter recovery
- state-dependent local causal structureの利用
- dynamical-system parameterのdisentanglement
- local sparse attentionによるcausal structure recovery

今回の監査ではauthor-official repositoryを固定できなかったため、paper/PMLR verified・official code unresolvedとし、再現済みbaselineには数えない。

## RQ-001 decision

> **NARROWED BEYOND LANGUAGE-GUIDED TARGET SELECTION, INTERVENTION-CONDITIONED COMPOSITION, GENERATIVE-REPRESENTATION CAUSAL INFERENCE, PARTIALLY OBSERVED MULTI-VIEW CRL, AND LOCAL-STRUCTURE DYNAMICAL-SYSTEM IDENTIFICATION — NOT ADOPTED**

採用には、既存baselineを差し引いた後にも残る明示的countermodel pair、externally fixedかつjoint recoding不能なdenotation law、trajectory/local-structure recoveryを超えるlanguage固有追加情報、直接回復metric、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage and capability decision

R0.1〜R0.3、novelty matrix、中心命題の事前登録が完了していないため、次stageは提案しない。

- new mechanism family: not recognised
- new intelligence principle: not discovered
- capability progress: not recognised
- high-school-level intelligence: not achieved
- completion: false
