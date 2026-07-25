# R0 Research Reconstruction — RESET-E019

Date: 2026-07-25
Branch: `research/intelligence-swarm-reconstruction-001`

## Integration decision

R0 remains the only active stage. No A–D toy mechanism, memory/replay/fast-weights/sleep/forgetting mechanism, new architecture family, researcher-authored intervention ontology, branch chain, novelty claim, intelligence-principle claim, or capability-progress claim is authorized.

Existing stacked draft PRs remain negative-results archives and are not experiment bases.

## 1. Primary-literature and official-code overlap audit

C012 adds WM3C (ICLR 2025) to the novelty boundary. WM3C already covers language-conditioned, composable, block-wise identifiable latent dynamics when language components and their corresponding disjoint latent blocks are supplied and sufficient variation, conditional independence, and smooth invertible mixing assumptions hold.

Therefore language-controlled latent-block decomposition, block-wise identifiability, and unseen recombination of supplied language components are not novel RQ-001 claims.

WM3C does not jointly identify raw utterance equivalence classes and unknown target blocks. However, C012 records a stronger re-encoding counterexample: without an explicit population grammar and restrictions on language-to-dynamics mechanisms, a pair of hidden language factors can be bijectively merged into one factor controlling a combined block, or one utterance identifier can be reversibly split into pseudo-components, without changing the observable distribution. The ambiguity changes the number and size of blocks and is stronger than permutation.

Decision: RQ-001 remains narrowed and not adopted. It must be rejected unless a preregistration rules out utterance-ID lookup and arbitrary factor splitting/merging, defines the residual causal abstraction, supplies a joint-identification theorem and matching impossibility result, and uses unseen-form/tuple/target splits.

## 2. R0.1 SILG/RTFM reproduction

Latest completed evidence remains the official SILG `multi` recurrent at 32,768 requested frames for seeds `1,7,19`:

- parameters: `4,916,915`
- state-dict audit bytes: `19,694,385`
- maximum RSS: `505,600 KiB`
- total three-seed training wall time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct win rate: `0.0167`
- Random win rate: `0.0667`
- Language-blind, State-only, Language-shuffle win rate: each `0.0167`

Correct remains below Random, so learned public capability is not reproduced.

At this integration, workflow run `30136732061` is still in the official 131,072-frame recurrent training step after successful source installation and random/schema probing. No unfinished checkpoint, resource, control, trajectory, or R0.2 value is incorporated.

## 3. R0.2 Environment-first fidelity audit

The primary paper and authors' public code are pinned to Gaddy & Klein 2019 and `dgaddy/environment-learning` commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`.

The official full method uses:

1. language-free `E(s,s') -> m` environment pretraining;
2. `D(s,m) -> s'` reconstruction;
3. a structured discrete message;
4. direct matching between language and environment messages;
5. an LSTM language module;
6. a pretrained decoder frozen by default.

The current SILG adaptation remains non-faithful because it uses a continuous width-48 message, no direct message-matching loss, a GRU, flat MSE over mixed typed state, no online task-success metric, and no verified entity/dynamics/language-form holdouts.

`audit_r02_gaddy_klein_fidelity.py` now fails closed unless canonical seeds, disjoint episodes, typed schema/losses, real holdouts, non-collapsed successful source trajectories, the official method contract, matched inference topology, resource reporting, and no pretrained LM are all present.

Classification: `official_method_transfer_audited_current_dataset_blocked`; formal R0.2 reproduction remains zero.

## 4. Evaluation contract and leakage

D015 adapts the contract directly to the concrete SILG exporter schema:

- `text_tokens -> utterance`
- `action -> gold_action`
- `state_after -> gold_state_after`
- prospective-only default `model_input`
- exclusion of reward, done, episode outcome, gold action, and after-state from model input
- train/test rejection for shared `episode_id`, `episode_seed`, or `observation_fingerprint`
- missing-method coverage is reported even when a method is wholly absent

The existing audits remain: utterance/entity/dynamics overlap, gold/post-treatment/completed-trajectory leakage, immutable fingerprints, complete `method × seed × domain × split × condition` coverage, paired cell/episode statistics, exact McNemar, hierarchical bootstrap CI, full artifact joins, complete hashes, model bytes, RSS, wall time, CPU latency, canonical seeds, and shuffle donor bijection/derangement.

Eighteen regression tests pass. Formal classification remains `initial_reproduction_failure` because real outcome-shuffle predictions, target-label-shuffle predictions or a formal inapplicability record, immutable serialized test data, complete artifact joins, and a competent public baseline are absent.

## 5. Stage decision

No next stage is proposed. Transition remains blocked until all of the following exist:

1. one competent learned external public capability baseline;
2. immutable-instance Correct/Random/Language-blind/State-only/shuffle controls;
3. complete three-seed artifact, statistics, and leakage contract;
4. qualified R0.2 online task-success comparison with typed transition metrics and real holdouts;
5. formal R0.3 rejection retained;
6. novelty matrix through relevant 2026 primary work;
7. exactly one preregistered successor claim with theorem assumptions, counterexamples, falsification, and stopping conditions.

## Status

- public learned capability baseline: `0`
- formal R0.2 reproduction: `0`
- R0.3 empirical track: rejected
- RQ-001: narrowed, not adopted
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
- completion: false
