# RESET-E012 — R0 Integration

## Decision

Continue **R0 Research Reconstruction**. Do not transition to a mechanism-development stage.

No toy hypothesis, architecture, memory mechanism or branch was created. This cycle integrates only public reproduction, trajectory qualification, prior-art boundaries and evaluation-contract evidence on the canonical reconstruction branch.

## Evidence integrated

### R0.1 staged public recurrent reproduction

The official SILG `multi` recurrent path is pinned to SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`, RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`, seeds `1,7,19` and RTFM S1.

The completed 2,048-frame matched smoke remains undertrained:

| Method | Win rate | Mean return |
|---|---:|---:|
| Correct | 0.0000–0.0167 across completed smoke artifacts | below Random |
| Random | 0.0667 | approximately -1.15 |
| Language-blind | 0.0000–0.0167 | approximately Correct |
| State-only | 0.0000–0.0167 | low |

It establishes source installation, official learner/checkpoint execution and matched initial-instance evaluation, not the published capability baseline.

Cycle R01-010 increases the staged budget to `32,768` frames per seed, adds Language-shuffle and episode-level paired export. At integration time, a completed artifact was not yet recorded in the canonical evidence. Therefore its outcome is **pending**, not positive or negative evidence.

### R0.2 trajectory qualification

The previous 2,048-frame policy trajectories are comparison-ineligible:

- seed 1: `0/40` successful training episodes;
- seed 7: `0/40`, with one action representing `97.42%` of transitions;
- seed 19: `1/40`;
- every test seed: `0/20` successful episodes.

The earlier offline accuracy ordering — State-only above End-to-end above Environment-first, with zero Language-blind and Language-shuffle gap — is retained only as a failed-policy negative diagnostic.

A trajectory-eligibility guard is now mandatory before interpreting R0.2:

- majority-action share `<=0.90`;
- at least five successful training episodes per seed;
- at least two actions with `>=5%` support.

If the 32,768-frame source policy fails this guard, only behavior-policy training/reproduction may be repaired. Representation-model tuning remains prohibited.

### Causal-identifiability boundary

C005 narrows the remaining candidate to RQ-001-N4. Unknown intervention targets, multi-node interventions, general-environment nonparametric CRL, temporal partition learning, multimodal shared-latent identification, language-dynamics pretraining and environment-first learning are established adjacent areas and cannot serve as the central novelty claim.

SILG remains valid for Gate L language-necessity testing but invalid for Gate I because it defines no ground-truth intervention partition or causal abstraction. Gate I remains blocked until a qualifying public benchmark is found.

### Reproducibility and statistics

D009 makes prediction-side `instance_fingerprint` mandatory and adds instance-paired statistics:

- Correct-only and control-only outcomes;
- exact two-sided McNemar test;
- hierarchical cluster-bootstrap confidence interval;
- cell-level paired randomization and minimum-cell gap.

Seven contract regression tests pass. Public ability reproduction still fails because complete fixed-snapshot predictions and verified method × seed × domain × split artifacts do not yet exist.

## Integrated classification

- Stage: `R0_public_capability_reproduction_and_benchmark_qualification`
- Stage transition: **false**
- Public environment control reproduction: `1`
- Public training-path reproduction: `1`
- Learned public capability baseline reproduction: `0`
- R0.2 formal reproduction: `0`
- R0.3: not authorized
- Evaluation classification: `initial_reproduction_failure`
- RQ-001-N4: `narrowed_not_adopted`
- Active mechanism family: none
- Novelty: not established
- Capability progress: not recognized
- High-school-level intelligence: not achieved

## Single P0

1. Retrieve and verify the completed 32,768-frame artifact.
2. Test policy competence and trajectory eligibility.
3. If eligible, freeze one immutable RTFM test JSONL and run every required control on exactly that snapshot.
4. Export complete predictions, checksums and resource measurements and pass the evaluation contract.
5. If ineligible, repair only the official recurrent training budget or reproduction conditions.

No R0.2 tuning, Gate-I model, new architecture or new mechanism family is authorized before this P0 resolves.
