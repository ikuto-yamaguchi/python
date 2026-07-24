# R0 Integration Report E013

Date: 2026-07-25

## Decision

Continue **R0 Research Reconstruction**. Do not transition to a new mechanism-development stage.

No new toy mechanism, architecture family, memory mechanism, or stacked branch is authorized. Existing stacked draft PRs remain a negative-results archive. All work continues on `research/intelligence-swarm-reconstruction-001`.

## 1. Primary-literature and official-code boundary

The novelty boundary remains restrictive:

- Unknown-intervention nonparametric CRL already establishes latent-variable and graph identifiability under explicit intervention-environment assumptions.
- Unknown multi-node intervention recovery is already covered, including partial recovery under soft interventions and perfect recovery under sufficiently diverse hard interventions.
- Score-based CRL already treats linear and general observation transformations and uncoupled intervention environments.
- 2026 finite-sample work reports recovery from a logarithmic number of unknown multi-node intervention environments, including unknown target recovery.
- Environment-first instruction following, language-dynamics pretraining, multimodal shared-latent recovery, perturbation-to-intervention prediction, and causal sufficiency/necessity are not novel by themselves.

Therefore RQ-001 cannot be adopted as a broad claim that language plus trajectories discovers unknown causal variables. The only remaining empirical candidate is whether episode-aligned language contributes mechanism information after conditioning on the complete non-language trajectory and strictly refines an intervention-supported equivalence class. This remains unadopted.

## 2. R0.1 public benchmark reproduction

Pinned environment:

- SILG commit `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit `58f17955595b5a127c96d045d896fcbcc7d4b570`
- train `silg:rtfm_train_s1-v0`
- test `silg:rtfm_test_s1-v0`
- seeds `1,7,19`
- pretrained language model: none

Reproduced:

- public environment installation and random control;
- official recurrent training/checkpoint path;
- 2,048-frame engineering smoke;
- checkpoint reload and matched initial-instance evaluation path;
- model/RSS/training/CPU timing collection.

Not reproduced:

- a learned public capability baseline close to the paper/reference regime;
- a strict immutable-instance comparison containing every required control;
- a complete artifact manifest joined to every episode prediction.

The 32,768-frame official recurrent run completed checkpoint creation for all three seeds. Its first matched evaluation stopped because the ablation harness supplied zero sequence lengths to the official packed RNN. The branch now masks lexical content while retaining a one-token padding sequence. The corrected workflow is still running at this integration point, so no corrected capability result is claimed.

## 3. R0.2 Environment-first reproduction

The existing public-trajectory comparison remains ineligible:

- almost no successful train or test episodes;
- seed 7 collapsed to one action for 97.42% of transitions;
- Environment-first did not exceed matched End-to-end or State-only;
- language removal and language shuffle changed nothing.

These values are retained only as a failed-policy negative diagnostic. Representation-model tuning remains prohibited until source trajectories pass, for every seed:

- majority action share <= 0.90;
- at least five successful train episodes;
- at least two actions with >=5% support.

A faithful R0.2 comparison must also use typed observation-field transition losses, online task success, real entity/dynamics/language-form holdouts, matched budgets, and identical-instance controls.

## 4. Evaluation, statistics, leakage, and provenance

The contract now checks:

- train/test normalized utterance overlap;
- entity/dynamics split overlap;
- gold action, after-state, reward, done, post-treatment and completed-trajectory leakage;
- prediction-supplied immutable instance fingerprints;
- complete method x seed x domain x split coverage;
- duplicate and missing predictions;
- domain x seed x condition cells;
- episode-paired gaps, Correct-only/control-only counts and exact McNemar tests;
- hierarchical seed/domain/condition cluster-bootstrap confidence intervals;
- source/model/data/log checksums, code commit, model bytes, RSS, training time and CPU latency.

The transition contract and SILG episode adapter are implemented, but strict evaluation still lacks target-label/outcome-shuffle coverage and a complete prediction-to-artifact manifest. Current classification remains `initial_reproduction_failure`.

## 5. RQ-001 and Gate-I status

Gate L remains a public language-necessity test on SILG and is not passed.

Gate I is rejected on SILG because the benchmark does not independently define latent intervention families, intervention targets, mechanism pre/post operators, or a causal abstraction. Audited candidates including J-CRe3, CausalTriplet, ACCESS and MIB do not jointly provide raw episode-aligned language, interactive trajectory, independently defined mechanism change, justified target/abstraction labels and held-out mechanism splits.

Candidate **RQ-001-N5** remains narrowed and not adopted:

> On a public benchmark with independently defined mechanism-changing variation, does episode-aligned raw language retain mechanism information conditional on the complete non-language trajectory, strictly refine a trajectory-only equivalence class, and improve held-out mechanism capability?

Necessary condition: `I(M; L | X) > 0`, where `X` contains state, action, history, reward, time, policy phase and environment identity.

If no qualified benchmark is found by completion of the novelty audit, the empirical Gate-I track is closed. The only permitted successor is a preregistered theory-only impossibility or sufficient-condition claim with explicit assumptions.

## 6. Stage-transition audit

R0.1 through R0.3, the novelty matrix and the central-claim preregistration are not complete.

Failed requirements:

1. learned external public capability baseline: 0;
2. all strict controls on one immutable public instance set: incomplete;
3. complete three-seed prediction/artifact/leakage contract: incomplete;
4. qualified R0.2 online matched comparison: incomplete;
5. R0.3: SILG rejected and no qualified replacement benchmark;
6. novelty matrix: active, not closed;
7. central claim preregistration: absent.

Therefore no stage transition is allowed.

## Single P0

1. Finish and inspect the corrected 32,768-frame matched-evaluation artifact.
2. Verify all three checkpoints, source/model/data/log hashes and resources.
3. Evaluate policy competence and source-trajectory eligibility.
4. If competent, freeze one immutable `rtfm_test_s1-v0` episode set and run every non-oracle control on it.
5. If incompetent, change only the official recurrent training/reproduction condition; do not tune R0.2.

## Status

- new intelligence principle: none
- academic novelty: not established
- capability progress: not recognized
- learned public capability baseline: 0
- high-school-level intelligence: not achieved
- completion: false
