# Intelligence Swarm Backlog

## Operating rule

R0はcanonical branch `research/intelligence-swarm-reconstruction-001`だけで進める。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineを再現するまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。単発失敗で終了せず、失敗分類、根拠、原因だけを変える最小修正、同一budget再run、採用・棄却・停止判定までを1サイクルとする。

## A–D allocation

- **A**: SILG/RTFM、J-CRe3等の公式code・dataset・command・dependency固定と無改変再現。
- **B**: 実装不一致、最適化不足、表現ボトルネック、探索・学習信号不足の診断と制約内最適化。
- **C**: 最新一次文献・公式codeとの重複監査、novelty matrix更新。
- **D**: D015〜D035、matched controls、resource provenance、leakage、RQ-001判定。

## P0 — SILG/RTFM R0.1 screening cycle

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- seeds `1,7,19`
- `131,072 requested frames`
- train `silg:rtfm_train_s1-v0`
- test `silg:rtfm_test_s1-v0`
- random / language-blind / state-only / language-shuffle
- same-instance matched evaluation

### Closed causes

1. `entropy_cost=0.005`単独原因: **rejected**
2. evaluation protocol mismatch主因: **rejected**
3. official stateful core不足単独原因: **rejected**
4. `unroll_length=20`不足単独原因: **rejected**
5. `learning_rate=0.0001`単独原因: **rejected**
6. gradient clip norm `40.0`不足単独原因: **rejected**

### Latest immutable negative evidence

- run `30240410850`, job `89896249118`
- artifact `8644560521`
- digest `sha256:987bc842229a8a9d03dcced3387c4c8a17a2049fdc2aadfad6c7560027e11e19`
- Correct `3/60`, Random `4/60`
- Language-blind `0/60`, State-only `0/60`, Language-shuffle `3/60`
- Correct return `-1.7679994`, Random return `-1.1513333`
- parameters `6,200,115`
- actual frames `131,200` per seed
- peak RSS `1,299,228 / 1,180,104 / 1,856,556 KiB`
- wall `1528.08 / 1559.30 / 1591.64 s`
- CPU forward `8.565 ms/step`
- leakage `false`
- qualification **rejected**

Decision: clip 10.0 reached all seeds, but Correct remained below Random and exactly matched language-shuffle. Gradient clipping threshold is rejected as the sole cause.

### Active blocker: checkpoint evidence preservation

artifact `8644560521`を展開した結果:

- standalone trained model-state: seeds `1/7/19`すべて存在
- `SILG_RTFM_OFFICIAL_CHECKPOINT_SEED_<seed>.job.tar`: **0件**
- optimizer/checkpoint restore integrity: **判定不能**
- classification: **`checkpoint_evidence_preservation_failure`**
- immutable inventory: `results_audits/SILG_RTFM_ARTIFACT_8644560521_INVENTORY.json`

Immediate tasks:

1. optimizer/restore失敗を推測で採用・棄却しない。
2. 古いartifactの欠落だけを修復するための同条件3-seed再学習を発行しない。
3. gradient-clipping workflowのtriggerからartifact-only auditor変更を外し、診断コード編集だけで高コストtrainingが再起動しないようにする。
4. 次の既に正当化されたtraining runで、学習直後に全seedのofficial `job.tar`存在、bytes、SHA-256、checkpoint frame counterをfail-closed確認する。
5. artifact upload対象へ全checkpointを含め、upload後inventoryでseed集合とdigestを再確認する。
6. checkpointが保存された場合だけ`audit_silg_optimizer_checkpoint_integrity.py`を適用する。
7. optimizer state/param groups/model equalityが不合格なら、その欠落成分だけを修正し、同一checkpoint・RNG・batchのone-step resume-equivalenceを先に通す。
8. integrityが合格ならoptimizer/restoreを主因から棄却し、learner logsから次の単一原因を選ぶ。
9. provenance修復や監査合格を能力進歩に数えない。

### Next single-cause selection rule

checkpoint provenanceが確保されるまでoptimizer/restore原因はopenのまま保持する。ただし証拠保存だけを目的とする重複学習は禁止する。次の性能runは、既存learner logとofficial defaultsとの差分から事前登録した単一要因だけを変更し、そのrunをcheckpoint integrity判定にも利用する。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで受入auditorを増やさない。checkpoint inventoryは能力受入条件の追加ではなく、既存原因を検証可能にするresource/provenance要件である。毎runでcontrols、resource、seed/split、checksums、leakageを保存する。

## P1 — External official reproductions

### J-CRe3

Ueda et al., LREC-COLING 2024、公式repository `riken-grp/J-CRe3`。exact commit、dataset、license、checksum、official commandを固定し、random、text-only、vision-only、mention-shuffle、frame/object-shuffleをmatched評価する。数値再現は0件。

### Latest prior-art boundary

CaST-Bench（CVPR 2026）は、2,066 questions / 1,015 videosについて、因果chainをtemporal segmentとbounding-box trackへgroundし、回答だけでなく時空間証拠の局在化を評価する。したがって、causal-chain-grounded video reasoning、visual evidence localization、grounded explanationだけではRQ-001の新規性を認定しない。hidden intervention-target identificationやSILG interactive policy competenceとは別能力である。

NoisyCausal、CodeBind、MagicBench、CausalDisenSeg、TRACE、DCAN、PCMCI、CausalLens、CTLD、score-based CRL、finite-sample CRL、LeGIT、GPI、Multi-View CRL、ReCITE、C3、MCDRL、CmIR、CAIR、Bayesian Ablation等もnovelty matrixの別列で維持し、論文値を本研究の能力証拠へ流用しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが`qualified_for_r02=true`を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## RQ-001

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

正式境界:

> **FURTHER NARROWED BEYOND CAUSAL-CHAIN-GROUNDED SPATIO-TEMPORAL VIDEO REASONING — NOT ADOPTED**

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 artifacts: **8件**
- competent external baseline: **0件**
- J-CRe3 numerical reproduction: **0件**
- active work: **checkpoint evidence-preservation repair and next single-cause contract**
- new mechanism family: **未認定**
- new intelligence principle: **未発見**
- capability progress: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
