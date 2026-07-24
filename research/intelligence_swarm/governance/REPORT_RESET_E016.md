# RESET-E016 — R0 Research Reconstruction integration

Date: 2026-07-25  
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

This integration accumulates only public benchmark reproduction status, prior-art/identifiability audit, evaluation-contract hardening, and governance decisions. It adds no toy mechanism, operation/goal hypothesis, memory/replay/fast-weights/sleep/forgetting mechanism, architecture family, hand-authored intervention ontology, stacked branch, intelligence-principle claim, or capability claim.

## Integrated evidence

### R0.1 SILG/RTFM

The last completed qualified staged result remains the corrected 32,768-frame official SILG `multi` recurrent run for seeds `1,7,19` with no pretrained language model.

- learned public capability baseline reproduced: `0`
- Correct win rate: `0.0167`
- Random valid-action win rate: `0.0667`
- Language-blind / State-only / Language-shuffle win rate: `0.0167`
- parameters: `4,916,915`
- maximum RSS: `505,600 KiB`
- total three-seed training wall time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- completed artifact SHA-256: `662139632c73082f096154d819bef20f86f672d4e8f5b36f8667d754b6b751d2`

The faithful staged budget has been increased to `131,072` frames per seed without changing the model, observation/action schema, optimizer family, splits, seeds, or pretrained-LM condition. Workflow run `30127967677` is still `in_progress` at integration time. No result, competence claim, resource value, trajectory qualification, or R0.2 conclusion from that unfinished run is incorporated.

### R0.2 Environment-first

R0.2 remains blocked. The previous public trajectories are comparison-ineligible because the source policy produced almost no successful episodes and one seed collapsed to one action. The current implementation also remains a continuous Gaddy/Klein-style adaptation rather than a faithful reproduction of the authors' structured discrete-message and direct message-alignment default. Flat scalar MSE over mixed typed RTFM fields remains invalid as a formal next-state metric.

No Environment-first tuning is authorized until a competent public source policy passes the existing success and anti-collapse gate.

### Evaluation contract — D013

The contract now requires verifiable donor provenance for `target_label_shuffle` and `outcome_shuffle` predictions:

- `control_source_instance_id`
- `control_source_fingerprint`
- donor existence in the immutable evaluation set
- no self-donor
- same seed/domain/split/condition cell
- correct donor fingerprint
- cell-wise bijection
- fixed-point-free derangement
- no illicit donor reuse

The result artifact records a `shuffle_assignment_audit` per cell. Thirteen regression tests pass, including missing provenance, self-shuffle, non-bijective donor reuse, cross-cell donation, and donor-fingerprint mismatch failures.

The current real public payload still lacks target-label-shuffle and outcome-shuffle predictions with this provenance, immutable serialized test-set checksum, and a complete raw-log/model/data artifact join. Strict classification remains `initial_reproduction_failure`.

### Prior art and RQ-001 — C009

C009 adds a non-identifiability counterexample. Two invertibly related latent representations can induce exactly the same complete pre/post trajectories while assigning different intervention partitions and different intervention-target cardinalities. If language is only a function of the environment/intervention index, then it adds no sigma-algebra beyond that index and cannot distinguish the competing partitions.

Consequences:

- language/trajectory dependence or shuffle sensitivity is not intervention-partition identification;
- environment labels, paraphrases, or long utterances do not help when language reduces to an index;
- multi-view nonlinear ICA, hidden-regime nonlinear ICA, mechanistic-independence, and heterogeneous measurement-model identifiability further narrow any surviving novelty claim.

Decision state:

- empirical Gate I / RQ-001-N5: rejected and closed;
- RQ-001-T1: narrowed again, not adopted;
- negative construction: now present;
- positive construction and sufficient-condition theorem: absent.

A surviving theory claim must show that raw-utterance relations not recoverable from an environment/intervention index strictly refine a causal-model equivalence remaining after complete non-language trajectories, and must differ nontrivially from existing auxiliary-variable, temporal, multi-view, hidden-regime, mechanistic-independence, and measurement-model identifiability results.

## Integrated decision

1. Continue R0 Research Reconstruction.
2. Do not recognize a learned public capability baseline.
3. Do not incorporate unfinished `131,072`-frame results.
4. Do not start or tune R0.2 until source-policy competence and trajectory eligibility are established.
5. Keep empirical Gate I closed and prohibit researcher-authored target/mechanism labels on SILG.
6. Keep RQ-001-T1 unadopted; C009 satisfies only the negative-construction prerequisite.
7. Require D013 shuffle provenance before any shuffle control can pass the evaluation contract.
8. Do not recognize novelty, a new intelligence principle, or capability progress.
9. Do not propose the next stage.

## Single P0

Complete and verify the `131,072`-frame faithful official recurrent run. Preserve checkpoints and the same immutable matched protocol. Audit source/model/data/raw-log hashes, model bytes, RSS, training wall time, CPU inference latency, canonical seeds, matched fingerprints, policy competence, and trajectory anti-collapse eligibility. If competence still does not emerge, correct only a verified official reproduction-condition mismatch or classify resource/budget insufficiency at the preregistered ceiling.

## Status

- public environment/control path: reproduced
- completed official recurrent training path at 32,768 frames: reproduced
- 131,072-frame staged run: in progress, not incorporated
- corrected matched-evaluation path: reproduced
- learned public capability baseline: not reproduced
- R0.2 formal reproduction: not reproduced
- empirical Gate I: rejected
- RQ-001-T1: narrowed, not adopted
- novelty: not established
- new intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
- completion: false
