# R0-D Cycle 008 — Aggregate Summary Reproducibility Preflight

## Scope

This cycle did not add memory, replay, fast weights, sleep, forgetting, a new architecture, or a new branch. It audited the public R0.2 trajectory summary against the strict benchmark contract.

Audited source:

- `R02_PUBLIC_TRAJECTORY_SUMMARY_003.json`
- Workflow run: `30108096366`
- Canonical seeds: `1, 7, 19`

## Added preflight

`audit_r02_public_summary.py` checks whether an aggregate summary contains enough information to proceed to strict instance-level scoring.

It verifies:

- canonical seed set
- required matched controls
- instance-level prediction availability
- evaluation dataset path and checksum
- immutable instance fingerprint digest
- per-run raw logs and full SHA-256 values
- per-seed model and data SHA-256 values
- online task success
- entity, dynamics, and language-form holdouts
- validity of the next-state metric

This is a preflight only. Passing it does not replace `evaluation_contract.py`; it permits the result to be submitted to the strict instance-level contract.

## Result

Formal classification: **`initial_reproduction_failure`**.

Missing matched controls:

- random
- target-label shuffle
- outcome/transition shuffle

Missing strict-evaluation artifacts:

- instance-level predictions
- evaluation dataset path and checksum
- instance fingerprint digest
- complete per-run raw logs
- per-seed model checksums
- per-seed data checksums

Missing external evaluations:

- online task success
- held-out entity transfer
- held-out dynamics transfer
- held-out language-form transfer
- valid typed next-state metric

## Diagnostic values retained

The aggregate summary is still useful as a negative diagnostic:

- Environment-first minus language-blind: `0.0`
- Environment-first minus language-shuffle: `0.0`
- Environment-first minus state-only: `-0.04008`
- Language-necessity signal: `false`

These values cannot establish progress because domain × seed × condition paired cells cannot be reconstructed and the required controls are incomplete.

## Decision

- R0.2 remains **not reproduced**.
- The public trajectory result remains a negative offline diagnostic only.
- No capability progress, novelty, or intelligence principle is recognized.
- The next valid run must emit canonical dataset JSONL, per-instance predictions for all required methods, fingerprints, and a complete artifact manifest.

## Reproduce

```bash
python3 research/intelligence_swarm/benchmarks/grounded_causal/audit_r02_public_summary.py \
  research/intelligence_swarm/benchmarks/grounded_causal/R02_PUBLIC_TRAJECTORY_SUMMARY_003.json \
  --output research/intelligence_swarm/benchmarks/grounded_causal/REPRO_AUDIT_R0D_008.json
```

A non-zero exit code is expected until the strict prerequisites are present.
