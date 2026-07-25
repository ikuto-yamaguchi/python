# R0-D Cycle 032 — Unified fail-closed acceptance gate

## Scope

This cycle adds no memory, replay, fast weights, sleep, forgetting, architecture, or capability claim. It integrates the existing R0 reproducibility and leakage checks into one acceptance command on the canonical reconstruction branch.

## Gap closed

Before this cycle, the core evaluation contract, prediction-payload leakage audit, and prediction/statistics checksum audit could be invoked independently. A caller could therefore run only `evaluation_contract.py score`, obtain paired statistics, and omit a companion audit that would reject gold/outcome payload leakage or mutable prediction/statistics evidence.

That partial success is not a qualified public-baseline reproduction.

## Change

`audit_r0_acceptance_bundle.py` now requires all of the following to return `valid=true` in the same invocation:

1. dataset/schema and train/eval leakage contract;
2. prediction-payload leakage and valid-action contract;
3. same-instance paired statistics contract;
4. model/data/raw-log resource artifact contract;
5. prediction/statistics checksum and validity contract.

Any failed component classifies the whole bundle as:

`initial_reproduction_failure`

The result records each failed contract and preserves its errors. A valid score cannot hide payload leakage, and valid resource files cannot hide a modified statistics report.

## Regression coverage

The dedicated tests verify that:

- all contracts passing is required for acceptance;
- prediction gold/outcome leakage rejects a bundle even when paired statistics pass;
- prediction/statistics checksum failure rejects an otherwise valid bundle;
- multiple simultaneous failures remain visible.

The dedicated workflow is short and does not trigger SILG training.

## Current status

No real R0 bundle has passed this unified gate. No public baseline reproduction, novelty, intelligence principle, capability progress, or high-school-level intelligence is recognized.
