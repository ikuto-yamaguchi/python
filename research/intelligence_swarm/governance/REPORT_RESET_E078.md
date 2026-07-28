# RESET-E078 — R0 Research Reconstruction

Date: 2026-07-28
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

- A〜Dの新規toy仮説、別branch、新規機構族は禁止を維持。
- 既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。
- 外部baseline再現前の新規知能原理・能力進歩認定は禁止。
- R0.1〜R0.3、novelty matrix、中心命題の事前登録が完了するまで次stageを提案しない。

## Execution audit

PR #409のhead `4376e9ab931fb663214404b2b4ef0c4ec84432a1`に紐づく確認可能な11件のPR workflow runを監査した。すべて`completed/action_required`であり、jobは生成されていない。

該当runには次が含まれる。

- R0 SILG push-run locator
- artifact path containment
- unified acceptance gate
- prediction method topology
- raw-log measurement binding
- normalized cell/holdout identity
- score dataset-contract binding
- artifact evaluation split scope
- R0D core metric coverage

この状態ではone-step resume-equivalence workflowのrun ID、job ID、artifact ID、qualification JSONは存在しない。したがって正式分類を次へ更新した。

> **`workflow_execution_approval_blocker`**

これはモデル、optimizer、checkpoint restore、resume instrumentation、SILG baselineの失敗ではない。Actions承認またはrepository policy解除前に同条件を重複dispatchしない。解除後は同一canonical workflowを変更せず実行し、最初の実jobとartifactだけをprimary evidenceとする。

## Frozen resume-equivalence contract

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- model `multi`
- stateful `false`
- actors `30`
- batch `24`
- unroll `80`
- threads `4`
- learning rate `0.0005`
- RMSprop
- gradient clip `40`
- seed `1`
- fixed train/validation split

RNG、exact learner batch、initial agent state、model、actor model、optimizer、schedulerをlearner update直前に保存し、uninterrupted one-stepとreload-resumed one-stepを比較する。受理にはmodel/optimizer/schedulerのbitwise equality、loss・gradient normのexact equality、batch payloadのbytes・SHA-256保存が必要である。

このrunはinfrastructure-onlyである。random/language-blind/state-only/language-shuffleはN/Aであり、能力進歩へ数えない。

## Existing numerical evidence

最新のshort-horizon negative artifactはrun `30240410850`、artifact `8644560521`。

- Correct `3/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `0/60`
- Language-shuffle `3/60`
- Correct return `-1.7679994`
- Random return `-1.1513333`
- parameters `6,200,115`
- actual frames `131,200` per seed
- peak RSS `1,299,228 / 1,180,104 / 1,856,556 KiB`
- wall `1528.08 / 1559.30 / 1591.64 s`
- CPU forward `8.565 ms/step`
- leakage `false`
- qualification rejected

これは公式100M-frame baseline failureではなく、縮小契約で言語依存能力が成立しなかったnegative evidenceである。

## Prior-art audit

AAAI 2026のCOGSをnovelty boundaryへ追加した。COGSはtime-series OOD generalizationについて、構造事前分布によるlatent causal graph学習、causal/non-causal variable disentanglement、domain-invariant representation、domain label不在時のprototype-based unsupervised domain discoveryを扱う。

したがって、次だけではRQ-001の新規性を認定しない。

- time-series latent causal/non-causal disentanglement
- unsupervised environment/domain discovery
- causal representationによるOOD generalization
- two-phase causal representation optimization

一次論文は確認済みだが、author-official repository、exact commit、dependency、dataset、official commandを固定できていないため、再現済みbaselineには数えない。SILG interactive policy competence、J-CRe3 multimodal reference resolution、hidden intervention-target groundingの代替baselineでもない。

## RQ-001

> **RQ-001: FURTHER NARROWED BEYOND UNSUPERVISED-DOMAIN CAUSAL REPRESENTATION LEARNING FOR TIME-SERIES OOD GENERALIZATION — NOT ADOPTED**

広義RQ-001は棄却、狭義RQ-001は未採用を維持する。

## Formal status

- immutable R0.1 short-horizon artifacts: **8件**
- official-contract infrastructure artifacts: **1件・不合格**
- one-step resume-equivalence artifacts: **0件**
- resume-equivalence execution: **Actions approval/policy blocker**
- official SILG 100M-frame reproduction: **0件**
- competent external baseline reproduction: **0件**
- J-CRe3 numerical reproduction: **0件**
- COGS numerical reproduction: **0件**
- R0.2: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- novelty matrix: **未完了**
- 中心命題の事前登録: **未完了**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 次stage: **提案なし**
