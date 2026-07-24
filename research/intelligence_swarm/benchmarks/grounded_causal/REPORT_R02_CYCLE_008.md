# R0.2 Environment-first baseline — cycle 008

## Decision

**Classification:** `official_method_transfer_audited_implementation_not_yet_faithful`

This cycle adds no operation/goal toy hypothesis and no architecture claim. It audits the current SILG/RTFM transfer against the primary paper and public implementation boundary before modifying the model.

## Fixed R0.1 substrate

- SILG source: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM source: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- train split: `silg:rtfm_train_s1-v0`
- test split: `silg:rtfm_test_s1-v0`
- canonical seeds: `1, 7, 19`
- pretrained language model: false
- source-policy gate: 131,072-frame official recurrent run must complete and pass success / anti-collapse checks before R0.2 results can be accepted

## Primary method contract

Gaddy & Klein (ACL 2019) define two stages:

1. Environment stage: learn `E(s,s') -> a` and `D(s,a) -> s'` from language-free transitions by maximizing the conditional likelihood of the next state.
2. Language stage: learn `L(c) -> a`, reuse the environment-pretrained decoder `D`, and maximize the likelihood of the correct resulting state `s'`.

The paper evaluates an otherwise identical no-pretraining baseline. For block stacking the decoder is frozen after environment learning; for string manipulation it is initialized from environment learning and subsequently trainable. The paper's stronger reported variant adds a discrete action representation and encoder matching.

Primary references:

- David Gaddy and Dan Klein, *Pre-Learning Environment Representations for Data-Efficient Neural Instruction Following*, ACL 2019, DOI `10.18653/v1/P19-1188`.
- Public code identified by the paper: `dgaddy/environment-learning`.

## Current implementation mapping

Current file: `environment_first_baseline.py`

| Required component | Current implementation | Verdict |
|---|---|---|
| language-free `E(s,s')` environment stage | `TransitionEncoder` | present |
| decoder `D(s,a)` reused in language stage | shared `Decoder` | present |
| decoder frozen option | `freeze_decoder=True` | present; block-stacking-like choice |
| otherwise identical end-to-end baseline | `InstructionModel` uses the same `LanguageEncoder` and `Decoder` classes | structurally present |
| state-only control | `StateOnlyModel` | present |
| three canonical seeds | workflow uses `1,7,19` | present |
| resource and model-byte reporting | JSON records bytes, RSS, train time, CPU latency | present |
| online task success | offline script returns `None` | absent |
| exact result-state likelihood | flat float-vector MSE | not faithful for mixed RTFM fields |
| discrete action representation | continuous vector of width 48 | absent |
| encoder matching objective | no transition/language latent matching term | absent |
| real held-out entity/dynamics/language-form split | booleans are consumed if present, but no audited construction is enforced here | unqualified |
| matched language-data budget and update budget | epochs are matched, but environment-first receives extra transition-stage optimization | must be reported separately, not called equal compute |

## Invalid metric identified

RTFM state serialization contains heterogeneous fields: continuous/relative coordinates, binary masks, categorical token or entity identifiers, and variable-length text-derived fields. Applying one unweighted MSE to the flattened vector does not correspond to the paper's conditional output likelihood and can be dominated by arbitrary numeric encodings.

Therefore these existing values are diagnostic only:

- `next_state_mse`
- `transition_joint_success` using a global absolute-error threshold

They must not be used as reproduction evidence or capability progress.

## Faithful SILG transfer specification

The minimum acceptable transfer is preregistered as follows.

### Shared data

For each seed, export identical immutable transition rows from the qualified R0.1 policy and preserve episode/step fingerprints. Use exactly the same language-labelled rows for Environment-first and End-to-end. Environment-only pretraining may use additional language-free rows, but their count and interaction cost must be reported independently.

### Typed decoder likelihood

Replace flat next-state MSE with field-specific heads and losses derived from the measured SILG schema:

- categorical grid/entity IDs: cross entropy with padding mask;
- binary validity or occupancy fields: binary cross entropy;
- bounded categorical positions/actions: cross entropy;
- genuinely continuous fields, if any: normalized MSE or an explicit likelihood;
- variable-length sequences: token cross entropy with length/padding masks.

Save both per-field metrics and a preregistered aggregate. Do not tune weights on the test split.

### Representation variants

Run in this order without claiming novelty:

1. continuous environment-first transfer, matching the paper's base method;
2. identical continuous end-to-end baseline;
3. only after 1–2 execute correctly, the paper's discrete-action and encoder-matching variant.

The discrete/matching variant is a reproduction of published methodology, not a new mechanism family.

### Parameter and data matching

At inference, Environment-first and End-to-end must have identical decoder/language topology and parameter count. The transition encoder is training-only and must be reported separately. Report:

- inference bytes;
- total training bytes;
- language-labelled rows;
- language-free transition rows;
- optimizer steps in each stage;
- total CPU training wall time;
- peak RSS;
- CPU inference latency.

Equal parameter budget does not imply equal compute or equal data; all three must be presented independently.

### Required evaluation

For each of seeds `1,7,19` and each audited split/condition, save:

- environment-level task success from online rollout;
- action accuracy on immutable matched transition instances;
- typed next-state negative log-likelihood and per-field accuracy/error;
- held-out entity transfer;
- held-out dynamics transfer;
- held-out language-form transfer;
- correct, language-blind, language-shuffle, and state-only controls;
- model/data/log/source SHA-256 and full commit IDs.

No result is accepted if source trajectories fail the success and action-diversity gate.

## Current execution status at audit time

The most advanced observed workflow was still inside official recurrent 131,072-frame training. A newer canonical-head run had also started. No completed 131,072-frame checkpoints, matched controls, eligible trajectories, or R0.2 online results were available for incorporation in this cycle.

## Next minimal code change

After the source-policy gate passes, the next implementation change is **only** to introduce an explicit typed RTFM state schema and typed decoder loss while retaining the current two-stage structure and identical end-to-end topology. Discrete representations and encoder matching remain deferred until the continuous published base transfer executes end to end.

## Claims

- formal R0.2 reproduction: not completed
- task-success improvement: not established
- representation improvement: not established
- novelty: not claimed
- intelligence principle: not claimed
- high-school-level intelligence: not achieved
