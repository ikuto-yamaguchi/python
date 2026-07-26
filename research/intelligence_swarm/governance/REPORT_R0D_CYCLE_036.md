# R0-D Cycle 036 — Unicode-normalized utterance overlap audit

## Scope

This cycle only strengthens R0 benchmark reproducibility and leakage auditing on the canonical reconstruction branch. It does not add memory, replay, fast weights, sleep, forgetting, a toy mechanism, or a new architecture.

## Defect found

`evaluation_contract.py` currently canonicalizes string utterances by removing whitespace and applying `casefold()`. That catches ordinary case/spacing duplicates, but not Unicode-equivalent or presentation-equivalent forms such as:

- full-width versus ASCII text (`ＴＡＫＥ　ＲＥＤ` / `take red`)
- precomposed versus combining characters (`café` / `cafe\u0301`)
- zero-width format characters (`open door` / `open\u200bdoor`)

Consequently, a train utterance could reappear in an evaluation split with only Unicode encoding differences while the existing exact-overlap check reports no collision.

## Change

Added `audit_unicode_utterance_overlap.py`, which performs a fail-closed overlap audit using:

1. Unicode NFKC normalization;
2. case folding;
3. removal of whitespace and Unicode control/format characters;
4. exact token-sequence canonicalization for tokenized SILG rows.

For every evaluation split, the report stores the normalized overlap count and example train/evaluation instance IDs. Any train-to-test/eval/validation overlap is classified as `initial_reproduction_failure`.

## Regression coverage

The focused test suite fixes the following behavior:

- genuinely distinct utterances pass;
- full-width aliases fail;
- combining-character aliases fail;
- zero-width aliases fail;
- equal token sequences fail;
- missing utterance/text tokens fail.

The suite was executed locally before publication and all six cases passed. A short GitHub Actions workflow was added; it does not trigger the long SILG training workflow.

## Status

- Accepted real R0 bundle: 0
- Accepted public baseline reproduction: 0
- Accepted model/RSS/runtime/latency bundle: 0
- Capability progress: not recognized
- New intelligence principle: not recognized
- Failure classification remains: `initial_reproduction_failure`

Direct integration of this Unicode normalization into `evaluation_contract.py` and the single acceptance gate remains required before it becomes an unavoidable acceptance condition.
