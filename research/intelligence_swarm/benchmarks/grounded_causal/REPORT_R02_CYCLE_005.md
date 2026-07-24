# R0.2 Environment-first baseline — Cycle 005

## Scope

This cycle does not introduce a new operation/goal mechanism or a new model family. It audits the completed 32,768-frame official SILG recurrent run, repairs the matched-control harness, and tightens alignment with the public implementation of Gaddy & Klein (ACL 2019).

## Public-source alignment

Primary sources:

- Gaddy & Klein, *Pre-Learning Environment Representations for Data-Efficient Neural Instruction Following*, ACL 2019, DOI `10.18653/v1/P19-1188`.
- Official software: `dgaddy/environment-learning`, `README.md`, `pretrain.py`, and `model.py`.

The official method is explicitly two-stage:

1. Learn an encoder `E(state, target_state) -> message` and a decoder `D(state, message) -> target_state` from language-free state transitions.
2. Freeze the environment encoder, normally freeze the decoder, and train an LSTM language module to emit the environment message. The public code optionally fine-tunes the decoder through `--model_train_decoder`.
3. The language-stage objective contains both output reconstruction and a message-matching term. The official default uses a discrete message; the continuous-message path is an ablation.

The current SILG port therefore remains a baseline reproduction only if it preserves all of the following:

- transition encoder observes `(state_before, state_after)` only during environment pretraining;
- transition decoder is conditioned on `state_before` and the learned message;
- the language encoder maps raw instruction fields to that same message space;
- no future state, reward, completed trajectory, target label, parser, or pretrained LM enters inference;
- matched end-to-end uses the same inference parameter budget and the same transitions;
- decoder-freeze and decoder-fine-tune variants are reported separately rather than silently mixed.

The public code was written for SHRDLURN/string-manipulation outputs, whereas SILG/RTFM exposes typed recurrent observations and low-level actions. Consequently, an exact paper-number reproduction on RTFM is impossible; the work is a faithful transfer baseline whose deviations must remain explicit.

## Completed 32,768-frame behavior-policy training

GitHub Actions run `30113833685` completed the official SILG `multi` recurrent training path for seeds `1`, `7`, and `19` before the evaluation harness failed.

| Seed | Frames in checkpoint | Wall time | Peak RSS | Model-state bytes |
|---:|---:|---:|---:|---:|
| 1 | 32,800 | 367.087 s | 491,876 KiB | 19,693,911 |
| 7 | 32,800 | 366.987 s | 505,556 KiB | 19,693,911 |
| 19 | 32,800 | 362.024 s | 480,664 KiB | 19,693,990 |

Shared model audit:

- parameters: `4,916,915`
- untrained state-dict bytes: `19,694,385`
- CPU forward latency: `7.779 ms/step`
- maximum measured RSS: `505,556 KiB`
- pretrained language model: no
- artifact ID: `8605097568`
- artifact digest: `sha256:e68d4156a50ca24346cc7ea133ae4a1435fb36fa4726c840a9cf0750b86a7a66`

This is still far below the public SILG paper-scale budget and is not a reproduced capability baseline.

## Failure and repair

The staged training completed, but matched evaluation stopped in the official `pack_padded_sequence` call because the text ablations zeroed `wiki_len`/`task_len`. The official recurrent encoder requires every declared sequence length to be positive.

Classification:

`evaluation_harness_input_contract_failure`, not model failure.

Repair applied on the canonical branch:

- masked token tensors are zeroed;
- corresponding `*_len` tensors are set to one, preserving one padding/unknown position and no lexical content;
- shuffled donor lengths are clamped to at least one;
- missing R0.2 trajectory exports are emitted as structured `initial_reproduction_failure` records rather than a secondary traceback.

The corrected workflow is re-running on the same canonical branch. No result from the failed matched-evaluation step is treated as capability evidence.

## Progress decision

- official 32,768-frame training/checkpoint path: reproduced as a staged engineering run;
- matched language-blind/state-only/language-shuffle evaluation: pending corrected rerun;
- trajectory eligibility: pending corrected export;
- Environment-first vs matched end-to-end: not yet eligible;
- task success, valid typed next-state prediction, held-out entity/dynamics/language-form transfer: not yet measured;
- novelty or intelligence-principle claim: prohibited;
- capability progress: not recognized.

## Next admissible decision

1. Complete the corrected matched-control run on the 32,768-frame checkpoints.
2. Export trajectories only after matched evaluation succeeds.
3. Apply the per-seed anti-collapse/success eligibility gate.
4. Run the Environment-first transfer only if all behavior-policy datasets qualify.
5. If they do not qualify, change only the public behavior-policy training/reproduction budget; do not tune the representation baseline against failed-policy data.
