# Intelligence Swarm Backlog

## P0 — Preserve one clean SILG recurrent reproduction bundle

Accepted evidence remains the official SILG `multi` recurrent at 32,768 requested frames、seeds `1,7,19`:

- parameters `4,916,915`
- state-dict audit `19,694,385 bytes`
- maximum RSS `505,600 KiB`
- total training time `1,033.885 s`
- CPU forward `6.911 ms/step`
- Correct `1/60`
- Random `4/60`
- Language-blind / State-only / Language-shuffle `1/60` each

Classification: `matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`。

Run `30158106220` completed install、schema/random probe、131,072 requested frames × seeds `1,7,19` training、and matched Correct/Random/Language-blind/State-only/Language-shuffle evaluation. It then failed during the R0.2 typed trajectory/baseline step before dependency freeze and artifact upload. Workflow artifacts are empty. None of the new checkpoint、performance、resource、or log values are accepted.

Required next actions:

1. Use only the canonical split-job workflow on `research/intelligence-swarm-reconstruction-001`.
2. Run `r01-public-reproduction` and verify immutable artifact upload immediately after matched R0.1 evaluation.
3. Retrieve and verify seed `1,7,19` checkpoints and actual frame counters before R0.2 consumes them.
4. Verify Correct、Random、Language-blind、State-only、Language-shuffle use identical initial instances.
5. Verify model bytes、peak RSS、training wall time、CPU latency、seed、split、raw logs、source/model/data/prediction/statistics checksums.
6. Feed the preserved R0.1 bundle through the unified evaluation contract and preserve the first failure.
7. Audit policy competence and action collapse before interpreting any ablation.
8. Do not place R0.2 inside the R0.1 preservation boundary.

Queue control:

- R0.1 workflow runs only on benchmark-code/run-request pushes or manual dispatch.
- Governance/prior-art commits must not enqueue another long reproduction.
- Existing pending/duplicate runs are not results.
- R0.2 may start only by downloading an uploaded immutable R0.1 artifact.

Forbidden:

- new toy mechanism or architecture family
- favorable seed/instance selection
- failed-policy trajectory tuning
- interpreting incompetent-policy ablations as language irrelevance
- counting workflow edits、queued/cancelled runs、documents、or unaudited step success as capability progress

## P0 — Evaluation, statistics, leakage and provenance

Implemented through D031:

- SILG real-schema adaptation
- train/test utterance overlap
- entity/dynamics split leakage
- gold action/after-state/completed-trajectory/post-treatment leakage
- semantic alias/value leakage
- exact global and per-cell seeds `1,7,19`
- domain/split/condition non-missing checks
- train and evaluation presence per seed
- immutable prediction/data/log/checkpoint/commit/resource joins
- random/language-blind/state-only/target-label shuffle/outcome shuffle same-instance coverage
- shuffle donor provenance、same-cell bijection、derangement、semantic no-op rejection
- observed sparse `domain × split × condition` topology shared by all methods/seeds
- mean gap、minimum cell gap、paired randomization、McNemar、episode-cluster bootstrap CI
- model bytes、RSS、training wall time、CPU latency、raw logs、checksums
- exact six-method artifact and prediction topology
- single full code commit and one data path/hash per cell
- strict prediction schema and prediction-payload leakage rejection
- D031 checksummed prediction JSONL and derived statistics artifacts, method/seed agreement, finite JSON values, coverage、cell statistics、summaries、paired gaps, and failure-report rejection

D031 focused regression fixes:

1. complete checksummed prediction/statistics evidence passes;
2. prediction mutation after hashing fails;
3. missing statistics checksum fails;
4. prediction method mismatch fails;
5. checksummed statistics classified as failure still fails.

Dedicated CI run `30171670131` passed. This validates audit code only; no real R0 bundle has passed.

Remaining:

1. Do not add another auditor unless a preserved real bundle exposes a concrete false pass/failure.
2. Apply the unified D015–D031 contract to the next preserved R0.1 artifact.
3. Preserve the first failing condition and raw evidence.
4. If target-label is undefined in SILG, record formal inapplicability instead of inventing labels.
5. Require core contract and companion auditors to agree on method registry、code commit、per-cell dataset identity、prediction payload、prediction checksums、and statistics checksums.

Formal classification remains **`initial_reproduction_failure`** until a real bundle passes.

## P1 — R0.2 Environment-first faithful transfer

Primary reference:

- Gaddy & Klein 2019
- public repository `kristyelee/environment-learning`
- historical reference `dgaddy/environment-learning`
- pinned commit `98c0dc68926ee9535f15019922d2ca871b0ac0b5`
- inspected Git blob SHAs fixed in `GADDY_KLEIN_PUBLIC_REFERENCE_MANIFEST.json`

Implemented:

- language-free transition pretraining followed by instruction following
- Environment-first / parameter-matched End-to-end / State-only
- typed before/after trajectory export without reward/outcome leakage
- generator-side entity/dynamics/language-form signatures
- immutable `(domain, split, seed, episode_seed)` join
- offline next-state/action comparison
- same-initial-instance online task evaluation
- checkpoint/model bytes、RSS、wall time、CPU latency、logs、hashes

RTFM S1 boundary:

- dynamics holdout: measurable
- entity holdout: formally inapplicable in S1
- language-form holdout: formally inapplicable in S1

The immutable author-code revision/reference-file pin gap is closed. Remaining blockers:

1. Add a fail-closed author-component → SILG-component mapping validator.
2. Keep the claim as task adaptation; do not compare RTFM numbers to ACL 2019 SHRDLURN/regex numbers.
3. Reproduce the paper's language-data-efficiency curve before discussing that result.
4. Execute the authors' code on a native public task.
5. Start R0.2 only after an immutable R0.1 artifact exists and passes checkpoint/resource integrity.
6. Download that artifact in the separate R0.2 job.
7. Produce and audit the 3-seed signature-to-trajectory join artifact.
8. Pass the real dynamics holdout audit.
9. Measure task success、next-state prediction、action accuracy and transfer for all three methods and seeds.
10. Confirm source-policy competence before attributing differences to representation learning.

Run `30158106220` produced no preserved R0.2 artifact and is classified as failed. No task success、next-state prediction、action accuracy、or transfer result is accepted.

Representation appearance、compression、clusteringは進歩に数えない。モデル調整は認可しない。

## Closed — R0.3 hidden intervention-target track

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず、R0.3 empirical trackを棄却維持する。

## P1 — Prior-art and novelty matrix

Integrated boundaries:

- C023: state-dependent local-dynamics identifiability
- C024: isolated causal effects of natural language
- C025: mechanistic independence
- C029: general-environment nonparametric CRL
- C030: lossy projected causal abstraction

C030 adds that many low-level interventions may collapse into one high-level intervention while valid high-level observational、interventional、and counterfactual queries remain identifiable. Therefore lossy abstraction itself, high-level query recovery, or a human-readable abstract label does not establish fine-grained target-partition or raw-language-equivalence recovery.

The novelty matrix must separate:

1. general-environment CRL;
2. projected high-level causal-query identification;
3. fine partition recovery inside a lossy abstraction fibre;
4. language-supplied residual information beyond observations、actions、outcomes、interaction history、environment signatures、and the maximal projected abstraction;
5. joint raw-utterance / residual-target identification under an external anti-recoding law.

Official paper-specific code for C030 was not verified. Public baseline reproduction remains required where code exists.

## P2 — Only admissible RQ reformulation, not adopted

Candidate only:

> 最強のnon-language estimatorとprojected causal abstractionを適用し、利用可能なhigh-level causal queryを識別した後にも同一abstraction fibre内に残るexplicit countermodel pairに対して、externally fixed・non-recodableなpopulation language contrastが不足するseparationを供給し、raw utterance equivalenceとfine intervention-target partitionを有限標本またはconsistentに共同同定できるか。

Necessary but insufficient condition:

`I(P_fiber ; L | A_proj, X, A, Y, H) > 0`

Before adoption:

1. explicit projected abstraction and identified query class;
2. concrete fibre with at least two non-language-indistinguishable fine partitions;
3. language contrast unrecoverable from observations、actions、outcomes、environment identity、or completed trajectories;
4. externally fixed denotation anchor established before fitting;
5. proof that all fibre-preserving joint automorphisms are removed;
6. strict joint-identification theorem;
7. impossibility theorem when language only names the high-level intervention;
8. finite-sampleまたはconsistency保証;
9. dependency-pinned public baseline reproduction;
10. true-group、projected-group、predicted-group、language-blind、state-only、target-label-shuffle、outcome-shuffle controls on identical instances;
11. direct recovery metrics for utterance classes and fine target blocks;
12. exactly one preregistered claim、counterexample、stopping rule;
13. model bytes、RSS、wall time、CPU latency、raw logs、checksums、seeds `1/7/19` once experiments begin.

No implementation、synthetic benchmark、new architecture is authorised.

## Stage transition

次stageは以下すべての完了後だけ提案する。

1. competent learned external public capability baseline
2. immutable matched controls
3. complete canonical three-seed prediction/artifact/leakage qualification
4. qualified R0.2 online comparison with real dynamics holdout and entity/language-form boundary
5. retained R0.3 rejection
6. novelty matrix closed through relevant 2026 primary work and official code
7. exactly one preregistered successor claim with theorem、counterexample、stopping rule

## Status

- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
