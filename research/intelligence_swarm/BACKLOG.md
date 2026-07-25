# Intelligence Swarm Backlog

## P0 — Complete one clean SILG recurrent reproduction

Completed evidence remains the official SILG `multi` recurrent at 32,768 requested frames for seeds `1,7,19`, with matched fixed-instance controls:

- parameters: `4,916,915`
- state-dict audit bytes: `19,694,385`
- maximum RSS: `505,600 KiB`
- total three-seed training time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct win rate: `0.0167`
- Random win rate: `0.0667`
- Language-blind, State-only, Language-shuffle: each `0.0167`

Classification: `matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`。

RESET-E022時点で、canonical headに131,072-frameの関連workflow run、combined status、検証済み完了artifactはない。未完了・cancelled・duplicate runを証拠にしない。

Authorized actions:

1. stable workflow headからexactly one 131,072-frame runを起動する。
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

D015は実SILG exporter schemaへ適合し、18件の実行済み回帰テストを持つ。

D016:

- prediction path/hash
- readable prediction JSONL
- method identity agreement
- unique instance IDs
- exact dataset/prediction instance-set equality
- fingerprint agreement
- shared immutable dataset hash
- stable model SHA/code commit

D017:

- every `domain × split × condition` cell must contain exactly seeds `1,7,19`
- missing/extra/noncanonical seeds fail closed

D018:

- `target_label_shuffle`は`replace_gold_action_from_donor`
- `outcome_shuffle`は`replace_gold_state_after_from_donor`
- donor payload SHA-256と実際に適用したpayload SHA-256の一致
- same-cell assignment、bijection、derangement、no self-shuffle
- 各cellで最低1件のsemantic value change
- no-op shuffleや申告donorと異なるpayloadは`initial_reproduction_failure`

D018の4テストはローカル成功。GitHub Actions完了結果はcurrent headで未確認なのでCI成功数には加えない。

Formal classification remains **`initial_reproduction_failure`** because real semantic shuffle bundles、immutable test serialization、complete prediction/artifact joins、competent public capabilityがない。

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
   - Environment-firstとEnd-to-endのinference parameter bytesを完全一致させる
   - action accuracy、typed next-state loss、real holdouts、online fieldがある場合だけtask success、CPU latency、training time、RSS、checkpoint/data hashesを保存
   - offline accuracyをonline task successへ代用しない

Current classification:

`matched_typed_offline_comparison_harness_implemented_execution_on_qualified_silg_data_blocked`

Before formal reproduction:

- competent non-collapsed 3-seed source trajectories
- complete typed state schema
- parameter/topology-matched controls
- equal examples/steps/splits
- real entity/dynamics/language-form holdouts
- online task success
- action accuracy and typed next-state metrics
- full resource/dependency/hash artifacts
- fidelity audit pass
- no pretrained LM

Representation appearance、compression、clusteringは進歩に数えない。

## Closed — Empirical Gate I / R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず、R0.3 hidden intervention-target ablationとRQ-001-N5は棄却維持。

## Closed — Broad RQ-001 formulation

Rejected:

- finite benchmark上でraw languageが全unrestricted finite auxiliary representationを超える
- grammar/mechanism restrictionなしでlanguage factorsとlatent target blocksを共同識別する
- unknown target recovery、environment label recovery、parameter namingをlanguage-specific causal identificationとする
- target不明、environment不完全、nonlinear/nonparametricであることだけをlanguage necessityとする
- shuffle degradation、semantic naming、prediction improvementだけでidentifiabilityを主張する

## P2 — Only admissible RQ reformulation, not adopted

Preregistration candidate only:

> general-environment、intervention-abstraction、trajectory-local parameter-identifiability criteriaを適用した後にも残る明示的なcausal symmetryを、latent representationと共同再符号化できないexternally anchored raw-language channelが、unseen utterance forms、compositions、systemsでstrictly refineできるか。

Before adoption:

1. formal non-language observation model and residual equivalence class
2. applicable general-environment/intervention/trajectory graphical criteriaの評価
3. non-language separation/variation条件が失敗する証明
4. jointly transformできないexternal language anchor
5. strict refinement theorem
6. anchor除去時のmatched impossibility construction
7. utterance-ID/environment-ID/target-label/component/parameter-name/paraphrase shortcut排除
8. unseen-form/composition/system evaluation
9. consistent estimatorまたはpopulation-only claimの明示
10. public baseline reproductionとpreregistration

No implementation、synthetic benchmark、architectureは認可しない。

## P1 — Prior-art and novelty matrix

2026年一次文献まで、unknown/uncoupled interventions、general-environment CRL、subset-intervention abstractions、finite-sample CRL、trajectory-local parameter identifiability、auxiliary/temporal/multi-view/hidden-regime ICA、grouping/weak supervision、mechanism sparsity、mechanistic independence、interactive grounding、environment-first、language-dynamics pretraining、causal world models、WM3Cを比較する。

C015でBaumgartner et al. 2026を追加。explicit target label不在だけではlanguage necessityにならず、parameter namingは残存reparameterization symmetryを除去しない。

## P2 — Japanese realism audit

Pinned candidate: official `riken-grp/J-CRe3`。commit、license、downloads、checksums、split/schemaを固定し、supported text/vision/combined baselinesを再現する。SILGへ平均せずGate Iにも使わない。

## Stage transition

次stageは以下すべての完了後だけ提案する。

1. learned external public capability baseline
2. immutable-instance controls
3. canonical 3-seed prediction/artifact/leakage contract
4. qualified R0.2 online comparison with typed metrics and real holdouts
5. formal R0.3 rejection
6. novelty matrix through 2026
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
