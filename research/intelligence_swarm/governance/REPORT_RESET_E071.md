# RESET-E071 — Gradient-clipping result and optimizer integrity audit

## Scope

Canonical branch `research/intelligence-swarm-reconstruction-001` only. No toy hypothesis, mechanism family, side branch, or stacked-PR base was created. Existing stacked drafts remain negative-results archive material.

## R0.1 result integrated

Gradient-clipping screening run `30240410850` completed on pinned SILG/RTFM with one source change only: gradient clip norm `40.0 → 10.0`.

Immutable evidence:

- job `89896249118`
- artifact `8644560521`
- digest `sha256:987bc842229a8a9d03dcced3387c4c8a17a2049fdc2aadfad6c7560027e11e19`
- execution commit `3f0c62430a27116722c22f69525b54631d93032b`
- Correct `3/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `0/60`
- Language-shuffle `3/60`
- Correct return `-1.7679994`
- Random return `-1.1513333`
- qualification rejected
- leakage false

The source patch, stateful path, unroll=80, LSTM checkpoints, frame budget, same-instance controls, official/fresh evaluation parity, resource capture, checksums, and artifact upload all passed.

## Decision

Gradient clip norm `40.0` is rejected as the sole cause. Clip `10.0` produced non-zero Correct success but did not beat Random in win rate or return, and Correct exactly matched language-shuffle. No language-dependent competence is established.

## Next single cause

The next cause is optimizer/checkpoint restore integrity. A fail-closed artifact-only auditor was added:

- `research/intelligence_swarm/benchmarks/grounded_causal/audit_silg_optimizer_checkpoint_integrity.py`
- commit `9afd2bae16aa317c63979ebc9406b86d9b4d8e70`

Before any new high-cost training, the saved artifact must prove for seeds `1/7/19`:

1. non-empty optimizer state and parameter groups;
2. finite frame counter at or above `131072`;
3. exact tensor equality between checkpoint model state and exported trained model state;
4. immutable byte sizes and SHA-256 provenance.

If the audit fails, only the missing restore component may be repaired, followed by local save/load resume-equivalence on identical state, RNG, batch and one learner update. If it passes, optimizer/checkpoint restore is rejected as principal cause and the next single cause must be selected from preserved learner logs.

## Prior-art boundary

NoisyCausal (ACL 2026) covers causal reasoning under structured noise and language-to-variable/causal-graph extraction followed by structured symbolic prompting. Therefore these elements alone are excluded from RQ-001 novelty. This benchmark does not reproduce hidden intervention-target grounding or SILG interactive policy competence.

RQ-001 remains not adopted:

> **FURTHER NARROWED BEYOND LANGUAGE-TO-CAUSAL-GRAPH STRUCTURING UNDER NOISE — NOT ADOPTED**

## Formal status

- immutable R0.1 artifacts: **8**
- competent external baseline reproduction: **0**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3: **rejected and retained**
- novelty matrix: **incomplete**
- central claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next-stage proposal: **none**
