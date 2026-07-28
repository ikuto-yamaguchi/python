# RESET-E075 — Official SILG infrastructure qualification

## Scope

Canonical branch `research/intelligence-swarm-reconstruction-001` only. A〜D remain prohibited from creating toy hypotheses, mechanism families, alternate branches, or stacked work bases. Existing stacked draft PRs remain a negative-results archive.

## Correction retained

The eight existing 131k-frame SILG artifacts remain short-horizon screening evidence. They are not official public-baseline reproductions because the pinned RTFM launch contract is 100M frames with `model=multi`, `stateful=false`, actors 30, batch 24, unroll 80, threads 4, learning rate 0.0005, RMSprop, and gradient clip 40.

Formal classification remains `public_reproduction_contract_mismatch`.

## Implemented execution

Added:

- `patch_silg_official_infrastructure_qualification.py`
- `audit_silg_infrastructure_qualification.py`
- `.github/workflows/r01_silg_official_infrastructure_qualification.yml`

The workflow runs one short 32,768-frame seed-1 segment with the official sampling/default command, without `--stateful` or a learning-rate override. It preserves the exact official `job.tar`, exported model state, host provenance, dependency lock, resource measurements, raw logs and SHA-256 manifest.

The qualification is explicitly not capability evidence. It records a canonical random probe, while language-blind/state-only/language-shuffle policy comparisons are marked not applicable to this infrastructure-only segment and remain mandatory for the later 100M capability reproduction.

## Fail-closed checks

The auditor verifies:

- official command parity for model/stateful/actors/batch/unroll/threads/learning-rate override
- checkpoint model state and standalone model-state exact equality
- non-empty optimizer state and parameter groups
- checkpoint frame counter at or above the segment budget
- checkpoint/model bytes and SHA-256
- peak RSS, wall time, throughput and projected 100M-frame runtime
- scheduler, RNG and learner-batch state presence required for one-step resume equivalence

One-step resume equivalence is not claimed merely from save/load equality. If RNG or learner-batch state is absent, the qualification rejects with explicit missing-prerequisite failures. The next change may add instrumentation for only those missing resume components; no new model mechanism is allowed.

## Prior-art boundary

MTG-Causal-RL (2026 preprint) introduces a complex partially observed, masked-action causal-RL benchmark with an explicit hand-specified SCM, intervention effects, per-factor credit traces, paired seeds and corrected statistical comparisons. Therefore, masked sequential decision making plus explicit SCM-grounded causal credit assignment and intervention-calibration is not a novelty basis by itself. Author-official code, exact commit and immutable reproduction are unresolved in this branch, so it is not counted as a reproduced baseline or as capability evidence.

Formal RQ status:

> **RQ-001: FURTHER NARROWED BEYOND EXPLICIT-SCM CAUSAL CREDIT ASSIGNMENT IN MASKED PARTIALLY OBSERVED RL — NOT ADOPTED**

## Formal status

- immutable R0.1 short-horizon screening artifacts: **8**
- official SILG 100M-frame reproduction: **0**
- official-contract infrastructure qualification: **workflow dispatched by canonical push; result not yet recognized**
- competent external baseline reproduction: **0**
- J-CRe3 numerical reproduction: **0**
- R0.2 formal reproduction: **0**
- R0.3 hidden intervention-target ablation: **rejected/closed**
- novelty matrix: **incomplete**
- central-claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**
