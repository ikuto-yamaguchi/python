# Intelligence Swarm Backlog

## P0 — Complete one clean SILG recurrent reproduction

Accepted evidence remains the official SILG `multi` recurrent at 32,768 requested frames for seeds `1,7,19`, with matched fixed-instance controls:

- parameters: `4,916,915`
- state-dict audit bytes: `19,694,385`
- maximum RSS: `505,600 KiB`
- total three-seed training time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct win rate: `0.0167`
- Random win rate: `0.0667`
- Language-blind, State-only, Language-shuffle: each `0.0167`

Classification: `matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`。

Current canonical headに131,072-frameの検証済み完了artifactはない。pre-integration head `8325ff9f63e8d782209cccce232170adc95689bb`にはcombined CI statusがなく、未完了・cancelled・duplicate runを証拠にしない。

Authorized actions:

1. stable workflow headからexactly one 131,072-frame runを起動・完了する。
2. seed `1,7,19`の3 checkpointとraw logsを検証する。
3. Correct、Random、Language-blind、State-only、Language-shuffleを同一immutable instanceで評価する。
4. source/model/data/raw-log/prediction SHA-256、code commit、model bytes、RSS、training wall time、CPU latency、seed、splitを保存する。
5. policy competenceとaction-collapseを監査する。
6. competence不成立なら、公式再現条件の検証済み不一致だけを最小修正するか、事前登録した上限でbudget/resource insufficiencyと分類する。

Forbidden:

- failed-policy trajectoryでR0.2を調整する。
- architecture/mechanism familyを追加する。
- favorable seed/instanceを選ぶ。
- incompetent policyからlanguage irrelevanceを結論する。
- unfinished/cancelled/duplicate runを成果扱いする。

## P0 — Immutable R0.1 evaluation

R0.1完了条件は、competent learned public baselineとcontrolsが一つのfrozen serialized `rtfm_test_s1-v0` snapshotをseed `1,7,19`で消費すること。

Required controls:

- official recurrent Correct
- random valid action
- language-blind
- state-only
- environment-ID-only
- within-environment language shuffle
- transition/outcome shuffle
- target-label shuffleはnon-oracle labelが存在する場合のみ。存在しなければformal inapplicability record。

Required outputs:

- per-instance prediction/fingerprint
- complete `method × seed × domain × split × condition` coverage
- win/return/episode length
- source/model/data/raw-log/prediction hashes
- model bytes/RSS/training time/CPU latency
- paired cell and episode statistics
- preregistered public-reference tolerance

## P0 — Evaluation, statistics, leakage and provenance

- D015: 実SILG exporter schemaへ適合。18件の実行済み回帰テスト。
- D016: prediction path/hash、可読JSONL、method一致、unique instance、dataset/prediction instance-set一致、fingerprint一致、shared dataset hash、stable model SHA/code commit。
- D017: every `domain × split × condition` cell must contain exactly seeds `1,7,19`。
- D018: target-label/outcome shuffleのdonor payload hashと実適用payload hash一致、same-cell、bijection、derangement、self-shuffle/no-op禁止。
- D019: entity/dynamics holdoutを`domain × split × condition × kind`単位で監査。同一domain train signatureとの重複、signature欠落、seed欠落/余分、train reference欠落をfail-closedで拒否。in-distribution cellの期待されるtrain overlapはholdout leakageへ誤分類しない。
- D020: 全評価行に`episode_id`を要求し、Correct対Random/Language-blind/State-only/Target-label shuffle/Outcome shuffleを同一instanceで比較する。cell→episodeのhierarchical bootstrap、episode-level sign-flip、step-weighted gap、episode-equal gap、minimum cell gap、paired episode/step countを保存する。
- D021: 各`method × seed × domain × split × condition` cellをprediction/data/raw-log/checkpoint/full commit/model bytes/RSS/training time/CPU latencyへ一対一結合する。exact six-method and seed coverage、shared dataset hash、stable checkpoint/commit、full checksumを要求し、post-manifest mutation、condition間checkpoint差替え、method間resource/artifact tupleコピーを拒否する。

D018の4テストはローカル成功。D019/D020/D021のCI完了結果は未確認。実semantic shuffle bundle、immutable test serialization、complete prediction/artifact joins、condition-scoped holdout pass、episode-cluster statistics pass、runtime/artifact-cell pass、competent public capabilityがないため、正式分類は **`initial_reproduction_failure`**。

## P1 — R0.2 Environment-first faithful transfer

Primary reference:

- Gaddy & Klein 2019
- `dgaddy/environment-learning`
- commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`

Implemented paths:

1. `gaddy_klein_typed_baseline.py`
   - language-free transition pretraining
   - 20 categorical message variables × 30 symbols
   - straight-through Gumbel-Softmax
   - shared typed next-state/action decoder
   - LSTM language encoder
   - direct message matching weight `0.01`
   - decoder freezing
   - categorical CE / binary BCE / continuous MSE
   - canonical seeds、hash/resource reporting
2. `export_silg_typed_policy_trajectories.py`
   - typed before/after fields and schema
   - metadata-derived cardinalities
   - episode/seed/split/fingerprint provenance
   - dataset/schema SHA-256
   - unknown field fail-closed
   - text/reward/done/outcome exclusion
3. `r02_typed_comparison.py`
   - Environment-first / End-to-end / State-only on identical typed data, seed and split
   - Environment-firstとEnd-to-endのinference parameter bytes完全一致
   - action accuracy、typed next-state loss、real holdouts、独立online fieldがある場合だけtask success、CPU latency、training time、RSS、checkpoint/data hashes
   - offline accuracyをonline task successへ代用しない
4. `audit_r02_matched_budget.py`
   - canonical seed、non-empty train/test、dataset SHA-256
   - complete test prediction coverage
   - inference parameter equalityとtransition-pretraining-only bytesの分離
   - checkpoint bytes/hash、training wall time、peak RSS、CPU latency
   - action accuracy、typed next-state loss
   - equal total row exposure
5. `audit_r02_holdout_assignments.py`
   - entity/dynamics/language-form holdoutの実在
   - exact seed coverage `1,7,19`
   - `entity_signature`、`dynamics_signature`、`language_form_signature`
   - train/test signature overlap zero
   - all-false placeholder禁止
   - test split全体のlanguage-form holdout扱い禁止
6. `attach_r02_holdout_manifest.py`
   - preregistered episode manifestを`domain/split/seed/episode_seed`で結合
   - non-empty entity/dynamics/language-form signatures
   - explicit Boolean holdout assignments
   - manifest/input/output SHA-256
   - duplicate/missing/extra/noncanonical/train-held-out entryをfail-closedで拒否
   - prediction/reward/task-success/action-accuracy/next-state-errorからholdoutを推測しない

Matched exposure contract for `N` train rows, environment epochs `E`, language epochs `L`:

- Environment-first: `N*E + N*L`
- End-to-end: `N*(E+L)`
- State-only: `N*(E+L)`

Offline checksが通っても独立online SILG task successがなければ、`matched_offline_budget_audit_passed_online_task_success_pending`とする。

Current blocking result:

- current exporter sets `entity_holdout=false` for all rows;
- current exporter sets `dynamics_holdout=false` for all rows;
- entire public test split is labeled `language_holdout=true`;
- immutable manifest join is implemented, but a valid preregistered manifest does not exist;
- qualified competent three-seed source trajectories do not exist;
- therefore no requested transfer metric is currently valid.

Current classification:

`immutable_holdout_join_implemented_manifest_generation_and_qualified_silg_execution_blocked`

Before formal reproduction:

- competent non-collapsed 3-seed source trajectories
- complete typed state schema
- parameter/topology-matched controls
- equal examples/steps/splits/row exposure
- externally specified immutable holdout manifest generated before prediction/outcome inspection
- real entity/dynamics/language-form signatures and disjoint cells
- online task success
- action accuracy and typed next-state metrics
- full resource/dependency/hash artifacts
- fidelity audit pass
- no pretrained LM

Minimal next correction:

1. pinned RTFM generator/configurationから、prediction/outcomeを見ずにimmutable holdout manifestを作成する。
2. episodeをentity/dynamics/language-formの非重複cellへ割り当て、3 signatureを保存する。
3. seed `1,7,19`を再exportし、manifestをjoinする。
4. `audit_r02_holdout_assignments.py`を通過してからmatched comparisonを実行する。

Representation appearance、compression、clusteringは進歩に数えない。モデル調整は認可しない。

## Closed — Empirical Gate I / R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず、R0.3 hidden intervention-target ablationとRQ-001-N5は棄却維持。

## Closed — Broad RQ-001 formulation

Rejected:

- finite benchmark上でraw languageが全unrestricted finite auxiliary representationを超える
- grammar/mechanism restrictionなしでlanguage factorsとlatent target blocksを共同識別する
- unknown target recovery、environment label recovery、parameter namingをlanguage-specific causal identificationとする
- target不明、environment不完全、nonlinear/nonparametricであることだけをlanguage necessityとする
- shuffle degradation、semantic naming、prediction improvement、non-zero isolated language effectだけでidentifiabilityを主張する
- partial shared-latent discoveryを新規性とする
- languageを追加modalityにすればtarget partitionが識別できるとする
- schema/sensor/object/time/field groupingをlanguageが再記述するだけでjoint identificationとする

## P2 — Only admissible RQ reformulation, not adopted

Preregistration candidate only:

> intervention-based、general-environment、trajectory-local、multimodal partial-sharing、known-observational-grouping identifiabilityを適用した後に、externally anchored population language channelが、otherwise unknownなobservational groupingと残存latent intervention-target partitionを共同同定できるか。

Before adoption:

1. G-CaRL-compatible known grouping適用後のformal residual equivalence class
2. language informationがschema、sensor identity、object slot、time index、environment label、action historyから復元不能である証明
3. grouping/latent partitionと共同再符号化不能なexternal language anchor
4. groupingとpartitionをjointly identifyするtheorem
5. anchor/grouping-separation除去時のmatched impossibility theorem
6. direct grouping metadataとG-CaRLとの比較
7. discrete/stochastic/non-injective population language generator
8. paraphrase/polysemyとunseen-form/composition/system evaluation
9. arbitrary merge/split and joint recoding禁止
10. dependency-pinned public baseline reproduction
11. exactly one preregistered claim、counterexample、stopping rule

No implementation、synthetic benchmark、architectureは認可しない。

## P1 — Prior-art and novelty matrix

2026年一次文献まで、unknown/uncoupled interventions、general-environment CRL、subset-intervention abstractions、finite-sample CRL、trajectory-local parameter identifiability、auxiliary/temporal/multi-view/hidden-regime ICA、grouping/weak supervision、mechanism sparsity、mechanistic independence、interactive grounding、environment-first、language-dynamics pretraining、causal world models、WM3C、isolated causal effects of natural language、multimodal partial-sharing CRL、known observational grouping CRLを比較する。

C018でMorioka and Hyvärinen, ICML 2024とofficial `hmorioka/GCaRL` commit `0020bfce34736d61d70ab8175f061d02951a7ed4`を追加。known observational groupingを新規language contributionから除外し、`G=q(L)=r(X)`なら`I(P;G|X)=0`であるcounterexampleを固定した。official codeは存在するがexact dependency lockがなく、reproductionは主張しない。

Novelty matrixは拡張されたがstage-transition用にclosedとは認定しない。

## P2 — Japanese realism audit

Pinned candidate: official `riken-grp/J-CRe3`。commit、license、downloads、checksums、split/schemaを固定し、supported text/vision/combined baselinesを再現する。SILGへ平均せずGate Iにも使わない。

## Stage transition

次stageは以下すべての完了後だけ提案する。

1. learned external public capability baseline
2. immutable-instance controls
3. canonical 3-seed prediction/artifact/leakage contract
4. qualified R0.2 online comparison with typed metrics and real holdouts
5. formal R0.3 rejection
6. novelty matrix through 2026 closed for the successor claim
7. exactly one preregistered successor claim/theorem、counterexamples、stopping rule

## Frozen work

- new toy benchmarks/mechanisms
- memory/replay/fast weights/sleep/forgetting
- best-seed/average-only positives
- prospective leakage
- new stacked PR chains
- smoke/offline imitation as intelligence progress
- manual Gate-I ontology
- R0.2 tuning on failed demonstrations
- RQ implementation before formalization/preregistration
