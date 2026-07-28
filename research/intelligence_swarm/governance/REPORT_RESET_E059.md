# RESET-E059 — Active Entropy Screening and C037 Boundary

Date: 2026-07-26
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope

R0 Research Reconstructionのみを累積する。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして扱い、新作業のbaseにしない。

## 1. Latest primary literature and official-code overlap audit

CVPR 2026の **Multi-Modal Image Fusion via Intervention-Stable Feature Learning** をC037として監査した。

同研究は以下の介入を用いる。

- complementary masking
- identical-region random masking
- modality dropout

これらの介入下で安定な特徴を選択するCausal Feature Integratorにより、spurious correlationではなく頑健なcross-modal dependencyを学習する。したがって、intervention-stable feature selection、masking intervention、modality dropout、robust multimodal dependency extractionだけではRQ-001の新規性を認定しない。

CVPR一次論文は確認済み。author-official repository、exact commit、dependency、dataset command、raw output、checksumは未解決であり、公式code再現済みとは扱わない。

## 2. SILG / J-CRe3 reproduction status

### SILG / RTFM

有効な`entropy_cost=0.005` screeningはGitHub Actions run `30215555334`、job `89830932884`で開始された。

- execution commit: `cbd4af3d89718df76cc481f7c730ed80334ef223`
- install: success
- SILG / RTFM source pins: success
- generator schema: success
- random/schema probe: success
- locator取得時のcurrent step: official `multi` recurrent 3-seed training
- artifacts at locator time: `0`

run完了前に同一screeningを重複発行しない。完了後にartifact、qualification、commands、controls、resources、leakage、diagnosticsを取得する。

### J-CRe3

- exact numerical reproduction: `0`
- official repository境界は維持
- SILG interactive policy competenceの代替baselineにはしない

## 3. Matched controls

次runで必須:

- Random
- Language-blind
- State-only
- Language-shuffle
- identical initial-instance stream

完了前のため、新しいcontrol数値は認定しない。

## 4. Resource and provenance contract

必須保存:

- model parameters / state bytes
- checkpoint bytes / SHA-256 / actual frames
- peak RSS
- training wall time
- CPU latency
- seeds `1/7/19`
- train/test split
- dependency lock
- raw logs
- artifact digest
- full command per seed
- actual entropy value per seed

## 5. Leakage

- answer leakage
- schema leakage
- prediction provenance
- same-instance verification

D015〜D035は凍結する。実bundleが具体的なfalse pass/failureを示さない限り新規auditorを追加しない。

## 6. RQ-001 decision

> **FURTHER NARROWED BEYOND INTERVENTION-STABLE MULTIMODAL FEATURE LEARNING — NOT ADOPTED**

採用条件:

1. competent external baseline再現
2. 既存非言語baselineを差し引いた後にも残るcountermodel pair
3. externally fixedでjoint recoding不能なdenotation law
4. language固有追加情報の直接証拠
5. claim / counterexample / stopping ruleの事前登録

## Failure-continuation contract

有効な`0.005`が全seedのsummary、record、commandへ到達したrunでCorrectがRandomを上回らない、またはCorrect successが0なら、entropy cost単独原因を棄却する。

その場合、同一budgetで次の単一原因 **official evaluation/default parity** を検証する。そこで終了せず、最大6 screening runまたは事前停止条件まで継続する。

## Formal status

- immutable R0.1 bundle: **2件・不合格**
- valid entropy=0.005 screening: **run 30215555334 training中**
- learned external baseline reproduction: **0**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3: **rejected and retained**
- novelty matrix: **incomplete**
- central claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next-stage proposal: **none**
