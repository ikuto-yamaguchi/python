# R0-D Cycle 009 — Explicit Snapshot Proof and Instance-Paired Statistics

## Scope

This cycle strengthens reproducibility, leakage and statistics auditing only. It introduces no memory mechanism, replay, fast weights, consolidation, forgetting, architecture or toy hypothesis.

## Problem found

The previous contract checked a supplied `instance_fingerprint` when present, but did not require predictions to provide one. A method could therefore omit the fingerprint and still be treated as using the canonical dataset snapshot. This did not prove that all methods consumed the same serialized observation.

The previous statistical output also paired Correct and controls mainly at the `seed × domain × condition` cell-mean level. Cell means are useful for cross-seed robustness, but they discard episode-level disagreement direction and can hide whether Correct wins on the same instances.

## Changes

### Mandatory snapshot declaration

Every prediction row must now include:

- `instance_id`
- `method`
- `instance_fingerprint`
- `pred_action`
- `pred_state_after`

The supplied fingerprint must equal the SHA-256 of immutable evaluation inputs:

- domain, seed, split and condition
- utterance
- state before
- history
- valid-action mask
- entity/dynamics identifiers or signatures

Missing fingerprints and mismatches are fatal contract errors.

### Instance-paired statistics

For every Correct-versus-control metric, the scorer now saves:

- number of paired instances
- instance-level mean gap
- Correct-only wins
- control-only wins
- ties
- exact two-sided McNemar/binomial p-value
- hierarchical cluster-bootstrap 95% interval

The bootstrap resamples `seed × domain × condition` cells and then instances within each sampled cell. This preserves the experiment hierarchy better than treating every transition as independent.

The existing cell-level outputs remain:

- domain × seed × condition cells
- mean, minimum and maximum cell gap
- positive-cell fraction
- normal-approximation cell CI
- paired cell randomization test

A positive result must now pass both the cell-level and clustered instance-level interval conditions.

## Regression test

Executed locally with Python standard library only:

```text
python3 -m unittest -v test_evaluation_contract.py
Ran 7 tests in 2.307s
OK
```

The additional tests verify:

1. an omitted fingerprint is rejected;
2. a mismatched snapshot is rejected;
3. paired instance counts are correct;
4. exact McNemar direction counts are correct;
5. the clustered bootstrap interval is positive for a deterministic positive fixture.

## Current public-baseline classification

The contract is stronger, but the public matched baseline remains:

`initial_reproduction_failure`

The canonical branch still lacks a complete instance-level comparison containing all required methods:

- Correct
- random
- language-blind
- state-only
- target-label shuffle
- outcome shuffle

It also still requires a complete verified `method × seed × domain × split` artifact manifest with model, data and raw-log checksums.

No ability progress or novelty is claimed.

## Next minimum action

Export one immutable RTFM test JSONL with fingerprints, run all required methods on that exact file, and feed their complete prediction JSONL plus artifact manifest through this contract. Aggregate-only summaries are no longer sufficient.

## Status

- Public matched baseline: not reproduced
- Classification: initial reproduction failure
- New memory mechanism: none
- New architecture: none
- Novelty: not established
- Capability progress: not recognized
- High-school-level intelligence: not achieved
