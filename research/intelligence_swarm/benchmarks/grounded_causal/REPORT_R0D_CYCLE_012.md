# R0-D Cycle 012 — independent artifact provenance contract

Date: 2026-07-25  
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

This cycle advances reproducibility, statistics, and leakage auditing only. It does not add memory, replay, fast weights, sleep, forgetting, a new architecture, or a new toy mechanism.

## Completed change

`evaluation_contract.py` previously allowed `raw_log_path`, `model_path`, or `data_path` to be absent and emitted only a warning. It also accepted shortened hashes and shortened code revisions, and did not compare `model_bytes` against the actual model artifact size. A manifest could therefore pass without independent access to the bytes whose provenance it claimed.

The artifact audit now requires:

1. readable raw-log, model, and immutable-data files for every run;
2. full 64-hex SHA-256 values for each file;
3. a full 40-hex Git commit SHA;
4. exact agreement between reported `model_bytes` and the model file size;
5. finite, non-negative RSS, wall-time, and CPU-latency values;
6. exactly the canonical seeds `1`, `7`, and `19`;
7. complete `method × seed × domain × split` coverage for `correct`, `random`, `language_blind`, `state_only`, `target_label_shuffle`, and `outcome_shuffle`.

A missing artifact is now an error, not a warning. Any failure is classified as `initial_reproduction_failure`.

## Regression tests

Executed locally against the exact committed files:

```text
Ran 10 tests in 2.272s
OK
```

New negative tests cover:

- absent raw-log path;
- truncated SHA-256 and Git revision;
- mismatch between reported model bytes and actual file size;
- non-canonical seed substitution.

Existing tests continue to cover utterance overlap, completed-trajectory leakage, fingerprint mismatch, prediction coverage, matched paired statistics, and Cartesian run coverage.

## Current public reproduction status

The existing SILG/RTFM staged run remains useful as an engineering result, but it does not satisfy this strict contract because:

- `target_label_shuffle` is absent;
- `outcome_shuffle` is absent;
- a complete per-cell manifest joining independently readable raw logs, model artifacts, immutable evaluation data, and their full checksums has not yet been produced;
- paper-scale public capability remains unreproduced.

Formal classification remains:

> `initial_reproduction_failure`

## Claims

- Public capability baseline: not reproduced
- Capability progress: not recognized
- Novelty: not established
- New intelligence principle: not claimed
- High-school-level intelligence: not achieved
