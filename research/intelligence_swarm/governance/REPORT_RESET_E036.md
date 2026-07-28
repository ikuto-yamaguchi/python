# RESET-E036 — R0 Research Reconstruction integration

Date: 2026-07-26  
Branch: `research/intelligence-swarm-reconstruction-001`  
PR: #409

## Scope

This integration keeps one canonical reconstruction branch. It adds no toy mechanism, operation/goal hypothesis, memory/replay/fast-weights/sleep/forgetting mechanism, architecture family, branch, or stacked PR chain. Existing stacked drafts remain negative-results archives.

## Newly integrated evidence

### R0-D Cycle 030

A concrete false-pass path was closed in prediction payloads. Dataset inputs were already screened for gold action/state, reward, terminal output, and completed-trajectory leakage, but prediction JSONL could still carry equivalent fields while the scorer ignored unknown keys.

The new fail-closed auditor requires exactly six preregistered methods, complete evaluation-instance coverage, one row per `instance_id × method`, a strict prediction schema, finite values, valid actions under the instance action schema, and no training-instance predictions. It rejects leaked gold/outcome/trajectory fields and unknown debug payloads.

This is qualification-code progress only. Real passing bundle: 0.

### R0.2 Gaddy–Klein fidelity audit 001

The current SILG/RTFM code matches the high-level two-stage separation of Gaddy and Klein 2019: language-free transition pretraining, frozen environment representation during language matching, a no-pretraining comparison, matched inference parameter budget, and separated offline/online metrics.

It is not yet entitled to a public reproduction claim because:

- the exact author-code revision and reference-file hashes are not fixed in the artifact contract;
- the RTFM port is a task adaptation, not a numerical reproduction of SHRDLURN/regex results;
- no fail-closed author-component → SILG-component manifest exists;
- the paper's language-data-efficiency curve is not reproduced;
- the authors' code has not been run on its native public task.

Formal R0.2 reproduction remains 0 and classification remains `initial_reproduction_failure`.

### C029 general-environment CRL boundary

Ng et al. 2025 shows that, under sufficiently rich environment-conditioned mechanism variation and structural assumptions, latent variables and the latent DAG can be identified under nonlinear nonparametric mixing without known intervention types or target labels.

Therefore the following are not admissible novelty claims:

- unknown intervention labels make language necessary;
- generic environment variation plus language labels is a new identification principle;
- naming an already identified environment/mechanism/latent variable is joint grounding;
- task success, environment classification, or language-shuffle gaps alone establish joint raw-language/target-partition identifiability.

The surviving candidate is further narrowed to language that separates an explicit residual countermodel pair after the strongest valid general-environment CRL analysis. C029 adds the necessary but insufficient condition:

`I(P_residual ; L | S_GE) > 0`

Adoption additionally requires an externally fixed anti-recoding law and a proof that the residual joint automorphism group is trivial. RQ-001 remains not adopted.

### R0.1/R0.2 split-job execution request

`R01_RUN_REQUEST.json` was refreshed to request the split-job workflow from the canonical head. R0.1 must preserve its immutable three-seed checkpoint/control/resource/log/checksum bundle before R0.2 starts.

The request itself is not a result. No corresponding immutable R0.1 artifact or accepted R0.2 result was verified in this integration.

## CI and evidence qualification

The current head's PR-triggered `R0 prediction method topology tests` run `30169591964` completed successfully. This validates a short audit-code path only. It does not establish:

- public capability reproduction;
- immutable checkpoint preservation;
- model/RSS/runtime/latency evidence;
- real leakage-contract passage;
- R0.2 task success or dynamics transfer;
- novelty, intelligence principle, or capability progress.

## Integrated decision

- R0.1 public learned baseline: **0 accepted reproductions**
- immutable 131,072-frame three-seed bundle: **0**
- R0.2 formal reproduction: **0**
- real R0 bundle passing unified contract: **0**
- R0.3 hidden intervention-target empirical track: **rejected**
- broad RQ-001: **rejected**
- narrowed RQ-001: **further narrowed; not adopted**
- novelty matrix: **incomplete**
- central preregistration: **incomplete**
- evaluation classification: **`initial_reproduction_failure`**
- next-stage proposal: **none**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**

## Next admissible actions

1. Preserve and audit the next split-job R0.1 artifact before any R0.2 consumption.
2. Apply D015–D030 to that real bundle and preserve the first failing condition.
3. Pin/hash the Gaddy–Klein author implementation and add a fail-closed component mapping before a faithful-transfer claim.
4. Reproduce the general-environment CRL official baseline with immutable dependencies before using it in the novelty matrix.
5. Do not authorize a successor architecture or experiment until R0.1–R0.3, the novelty matrix, and exactly one central preregistration are complete.
