# R0-D Cycle 037 — Unicode utterance overlap in the core contract

## Scope

This cycle changes only benchmark qualification. It adds no memory, replay, fast weights, sleep, forgetting, toy mechanism, architecture family, branch, or PR chain.

## Defect

`audit_unicode_utterance_overlap.py` already rejected train/evaluation utterance aliases after Unicode normalization, but `evaluation_contract.py validate` still used only whitespace removal and `casefold()`. A caller could therefore bypass the standalone auditor and obtain a nominally valid core-contract result for visually equivalent strings such as:

- `ＴＡＫＥ　ＲＥＤ` versus `take red`
- precomposed `café` versus `cafe` plus a combining accent
- `open door` versus `open` + zero-width-space + `door`

The official single-bundle acceptance path calls the core dataset contract, so the normalization rule must live in that contract rather than remain optional.

## Change

`evaluation_contract.py` now canonicalizes textual utterances using:

1. Unicode NFKC normalization;
2. `casefold()`;
3. removal of whitespace;
4. removal of Unicode control and format characters (`Cc`, `Cf`).

Integer token sequences remain exact ordered token IDs and are not semantically rewritten.

The overlap report now records, for each shared normalized utterance:

- the normalized value;
- up to five train instance IDs;
- up to five evaluation instance IDs.

Only train-to-test/eval/validation/valid overlap is fail-closed. Failure remains classified as `initial_reproduction_failure` by the enclosing acceptance gate.

## Regression coverage

`test_evaluation_contract_unicode_overlap.py` fixes the following cases:

- genuinely different train/test utterances pass;
- full-width aliases fail;
- composed/decomposed Unicode aliases fail;
- zero-width-format aliases fail;
- overlap evidence retains train and evaluation instance provenance.

## Research status

- accepted real R0 bundle: 0
- accepted public baseline reproduction: 0
- accepted model/RSS/runtime/latency evidence bundle: 0
- capability progress: not recognized
- new intelligence principle: not recognized
- classification until a real bundle passes: `initial_reproduction_failure`
