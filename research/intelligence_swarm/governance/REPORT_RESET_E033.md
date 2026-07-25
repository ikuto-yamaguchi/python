# RESET-E033 — R0 Reconstruction Integration

## Scope

This integration adds no toy mechanism、operation/goal hypothesis、memory、replay、fast weights、sleep、forgetting、architecture family、branch、or PR chain. Existing stacked drafts remain negative-results archives.

## Verified R0.1 execution state

GitHub Actions run `30158106220` reached the following verified step results:

- pinned SILG/RTFM installation: success
- generator-signature tests: success
- canonical random/schema probe: success
- official recurrent training at 131,072 requested frames for seeds `1,7,19`: success
- matched Correct/Random/Language-blind/State-only/Language-shuffle evaluation: success

The job then terminated with conclusion `failure` during the R0.2 typed trajectory and baseline step.

The following steps did not complete:

- R0.2 holdout audit
- dependency freeze
- artifact upload

The workflow run exposes zero artifacts. Therefore no 131,072-frame checkpoint、performance value、model bytes、RSS、training wall time、CPU latency、raw log、or checksum is accepted as reproducible evidence.

Classification:

`initial_reproduction_failure_due_to_unpreserved_bundle_after_downstream_failure`

Training-step success is retained as execution-path evidence only. It is not public capability reproduction or capability progress.

## Preservation boundary

The canonical workflow currently on `research/intelligence-swarm-reconstruction-001` separates:

1. `r01-public-reproduction`
2. `r02-environment-first`

The R0.1 job now freezes and uploads its bundle immediately after matched control evaluation. The R0.2 job depends on that job and downloads the immutable R0.1 artifact. This is the required execution boundary for the next run: R0.2 failure must not erase R0.1 evidence.

No new long run is triggered by this governance integration.

## R0.2

No formal R0.2 result was preserved from run `30158106220`.

Accepted counts remain zero for:

- Environment-first task success
- parameter-matched End-to-end task success
- State-only task success
- next-state prediction
- action accuracy
- dynamics-holdout transfer
- three-seed resource measurements

RTFM S1 supports a real dynamics holdout only. Entity and language-form holdouts remain formally inapplicable rather than synthetically invented.

## Evaluation contract

D027 is integrated with the prior fail-closed checks. It requires:

- exactly Correct、Random、Language-blind、State-only、Target-label shuffle、Outcome shuffle
- canonical seeds `1,7,19`
- complete method coverage per observed cell
- one data path and SHA-256 per `(seed, domain, split, condition)` cell
- one immutable code commit across the bundle
- all prior leakage、coverage、shuffle、statistics、resource、raw-log、and checksum requirements

No real bundle has passed. In this run there is no artifact to audit.

## Prior-art and RQ-001

C023–C025 remain the active novelty boundary:

- state-dependent local dynamics can identify parameters without language
- isolated causal effects of predefined linguistic attributes do not identify raw utterance equivalence or latent target partitions
- mechanistic independence can identify components under nonlinear and non-invertible mixing without language

The narrowed RQ remains not adopted. Adoption still requires an explicit residual countermodel pair、external non-recodable anchor、strict joint-identification theorem、matching impossibility result、finite-sample or consistency guarantee、public baseline reproduction、and exactly one preregistered claim.

## Stage decision

No next stage is proposed.

- R0.1 public capability baseline: not reproduced
- R0.2 formal reproduction: incomplete
- R0.3: rejected
- novelty matrix: incomplete
- central preregistration: incomplete
- new intelligence principle: none
- capability progress: not recognized
- high-school-level intelligence: not achieved
- completion: false
