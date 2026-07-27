# RESET-E072 — R0 Research Reconstruction integration

Date: 2026-07-27

Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。公開benchmark再現、prior-art audit、D015〜D035 evaluation contract、hidden intervention-target ablationだけを累積する。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baseline再現前に新規機構族・知能原理・能力進歩を認定しない。高校生級知能は未達を維持する。

## Artifact inspection performed

Gradient-clipping screeningのimmutable artifactを実際に取得・展開した。

- run: `30240410850`
- job: `89896249118`
- artifact: `8644560521`
- digest: `sha256:987bc842229a8a9d03dcced3387c4c8a17a2049fdc2aadfad6c7560027e11e19`

存在を確認した主要ファイル:

- `SILG_RTFM_TRAINED_STATE_SEED_1.pt`
- `SILG_RTFM_TRAINED_STATE_SEED_7.pt`
- `SILG_RTFM_TRAINED_STATE_SEED_19.pt`
- matched controls
- policy diagnostics
- official/fresh parity
- qualification
- dependency freeze
- file sizes and SHA-256 manifest

存在しなかった必須ファイル:

- `SILG_RTFM_OFFICIAL_CHECKPOINT_SEED_1.job.tar`
- `SILG_RTFM_OFFICIAL_CHECKPOINT_SEED_7.job.tar`
- `SILG_RTFM_OFFICIAL_CHECKPOINT_SEED_19.job.tar`

## Formal diagnosis

> **checkpoint_evidence_preservation_failure**

保存済みartifactにはstandalone model-stateしかなく、official checkpointがない。このため次は判定不能である。

- optimizer stateの存在・entry数
- optimizer parameter groups
- checkpoint frame-counter provenance
- checkpoint modelとstandalone model-stateの完全一致
- save/load resume-equivalence

この証拠欠落をoptimizer/checkpoint restore failureとして扱ってはならない。optimizer/restore原因はopenのまま保持する。

Inventory evidence:

- `research/intelligence_swarm/benchmarks/grounded_causal/results_audits/SILG_RTFM_ARTIFACT_8644560521_INVENTORY.json`
- commit `fd7978701408592a3e5171e29641a7b47583eb88`

## Continuation contract

「監査できなかった」で終了しない。

1. 古いartifactのcheckpoint欠落だけを直すための重複3-seed trainingは禁止する。
2. 次の既に正当化された単一要因trainingで、学習直後に全seedのofficial `job.tar`存在、bytes、SHA-256、frame counterをfail-closed確認する。
3. artifact upload後にもcheckpoint seed集合とdigestをinventory監査する。
4. checkpointが揃った場合だけoptimizer/checkpoint integrity auditorを実行する。
5. 不合格なら欠落restore成分だけを修正し、同一checkpoint・RNG・batchのone-step resume-equivalenceを先に通す。
6. 合格ならoptimizer/restoreを主因から棄却し、learner logから次の単一原因を選ぶ。
7. provenance修復や監査合格は能力進歩に数えない。

## Controls and resources

最新の有効なnegative performance evidenceは変更しない。

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

Gradient clipping threshold remains rejected as the sole cause. Language-dependent competence is not established because Correct equals language-shuffle and remains below Random.

## Prior-art audit

CaST-Bench（CVPR 2026）は、2,066 questions / 1,015 videosについて、causal chainをtemporal segmentsとbounding-box tracksへgroundし、answer accuracyだけでなく時空間証拠の局在化を評価する。

したがって、以下だけではRQ-001の新規性を認定しない。

- causal-chain-grounded video reasoning
- temporal causal evidence localization
- bounding-box-track grounded explanation
- grounded causal-chain evaluation

これはhidden intervention-target identificationやSILG interactive policy competenceとは別能力であり、論文値を本研究の能力証拠へ流用しない。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND CAUSAL-CHAIN-GROUNDED SPATIO-TEMPORAL VIDEO REASONING — NOT ADOPTED**

## Formal status

- immutable R0.1 artifacts: **8件**
- competent external baseline reproduction: **0件**
- J-CRe3 numerical reproduction: **0件**
- qualified R0.2: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- novelty matrix: **未完了**
- central claim preregistration: **未完了**
- new mechanism family: **未認定**
- new intelligence principle: **未発見**
- capability progress: **未認定**
- 高校生級知能: **未達**
- next-stage proposal: **なし**
