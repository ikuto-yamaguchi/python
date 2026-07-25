# R0.2 Environment-first baseline — cycle 008

## Decision

**Classification:** `official_method_transfer_audited_current_dataset_blocked`

This cycle adds no operation/goal toy hypothesis and no architecture claim. It audits the current SILG/RTFM transfer against the primary paper and the authors' public implementation, and adds a fail-closed eligibility program before any result can be called an R0.2 reproduction.

## Fixed R0.1 substrate

- SILG source: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM source: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- train split: `silg:rtfm_train_s1-v0`
- test split: `silg:rtfm_test_s1-v0`
- canonical seeds: `1, 7, 19`
- pretrained language model: false
- source-policy gate: the official recurrent run must complete and pass success/action-diversity checks before R0.2 results can be accepted

## Primary sources fixed

- David Gaddy and Dan Klein, *Pre-Learning Environment Representations for Data-Efficient Neural Instruction Following*, ACL 2019, DOI `10.18653/v1/P19-1188`.
- Authors' public repository: `dgaddy/environment-learning`, commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`.

The public README calls the default block-stacking run the **full model**, including discrete representations and encoder matching. Its explicit ablation uses `--continuous_message --model_message_loss_weight 0.0`. In `model.py`, the language module is an LSTM; the pretrained encoder supplies target messages; the default message-loss weight is `0.01`; and the decoder remains frozen unless `--model_train_decoder` is set.

## Official method contract

1. Environment phase: learn an encoder `E(s,s') -> m` and decoder `D(s,m) -> s'` from language-free state transitions.
2. Language phase: learn `L(c) -> m`, reuse the environment-pretrained decoder, and predict the correct result state.
3. Full published implementation: structured discrete message plus direct matching between the language message and the environment encoder's target message.
4. End-to-end control: the same final language-module/decoder architecture without environment pretraining.

## Current implementation mapping

Current file: `environment_first_baseline.py`

| Required component | Current implementation | Verdict |
|---|---|---|
| language-free `E(s,s')` environment stage | `TransitionEncoder` | present |
| decoder `D(s,m)` reused in language stage | shared `Decoder` | present |
| decoder frozen by default | `freeze_decoder=True` | present |
| otherwise identical end-to-end baseline | same `LanguageEncoder` and `Decoder` classes | structurally present |
| state-only control | `StateOnlyModel` | present |
| three canonical seeds | workflow uses `1,7,19` | present |
| resource/model-byte reporting | JSON records bytes, RSS, time, latency | present |
| online task success | offline script returns `None` | absent |
| typed result-state likelihood | one flat float-vector MSE | invalid for mixed RTFM fields |
| official default discrete message | continuous width-48 vector | absent |
| encoder/language message matching | no direct matching loss | absent |
| authors' LSTM language module | GRU | not faithful |
| real entity/dynamics holdouts | exporter hard-codes both flags false | absent |
| verified unseen language-form split | public test split is marked as language holdout without form-overlap proof | unqualified |
| matched data and compute | epochs match, but environment-first gets a separate pretraining stage | must be reported separately |

## Invalid metric identified

The exported state vector concatenates heterogeneous SILG fields after converting everything to floats. It includes categorical token/entity identifiers, binary masks, positions and other structured fields. One unweighted MSE therefore does not implement the paper's conditional output likelihood and can be dominated by arbitrary numeric encodings.

The existing `next_state_mse` and global-threshold `transition_joint_success` remain diagnostic only. They are not reproduction or capability evidence.

## Completed code change

Added:

`audit_r02_gaddy_klein_fidelity.py`

The audit exits nonzero and classifies the run as `initial_reproduction_failure` unless all of the following are present:

- exact canonical seed coverage `1,7,19`;
- disjoint train/test episode IDs;
- a typed `state_schema` that exactly covers the state vector;
- nonempty real entity, dynamics and language-form holdout examples;
- evidence that test language forms are not merely copied train token sequences;
- a non-collapsed source-policy action distribution;
- at least one successful terminal episode;
- an explicit method contract requiring discrete message, message alignment, pretrained decoder, default decoder freezing, typed next-state loss, matched parameter/data/split budgets, online task success and no pretrained LM.

The current trajectory exporter intentionally fails this gate because it does not preserve typed field boundaries and sets entity/dynamics holdouts to false. This prevents the existing continuous diagnostic from being mislabeled as a faithful result.

## Required faithful transfer

### Typed decoder likelihood

Replace flat MSE with field-specific heads and losses derived from the measured SILG schema:

- categorical grid/entity/token IDs: masked cross entropy;
- binary validity or occupancy fields: binary cross entropy;
- bounded categorical positions/actions: cross entropy;
- genuinely continuous fields, if any: normalized MSE or an explicit likelihood;
- variable-length sequences: token cross entropy with length/padding masks.

Save per-field metrics and a preregistered aggregate. Test data must not determine weights.

### Parameter, data and compute matching

At inference, Environment-first and End-to-end must have identical language/decoder topology and parameter count. The transition encoder is training-only and reported separately. For every seed report:

- inference bytes and total training bytes;
- language-labelled rows and language-free transition rows;
- optimizer steps in both stages;
- CPU training wall time and peak RSS;
- CPU inference latency;
- source/model/data/log full hashes.

Equal parameter count must not be described as equal data or equal compute.

### Required evaluation

For seeds `1,7,19`, on immutable matched instances, save:

- online environment task success;
- action accuracy;
- typed next-state likelihood and per-field accuracy/error;
- held-out entity, dynamics and language-form transfer;
- correct, language-blind, language-shuffle and state-only controls.

No result is accepted if source trajectories fail the success/action-diversity gate.

## Current execution status

At audit time, the canonical workflow is still in the official 131,072-frame recurrent training step. No unfinished checkpoint, task-success, model-size, RSS, timing, latency or trajectory value is incorporated here.

## Next minimal change

After the source-policy gate passes:

1. export field-preserving observations plus typed schema;
2. derive public-generator entity/dynamics/language-form holdouts or formally mark them unavailable—do not invent target labels;
3. implement the official discrete message and direct message-matching objective;
4. retain an identical no-pretraining end-to-end inference topology;
5. run three-seed offline typed metrics and online task success.

## Claims

- formal R0.2 reproduction: not completed
- task-success improvement: not established
- representation improvement: not established
- novelty: not claimed
- intelligence principle: not claimed
- high-school-level intelligence: not achieved
