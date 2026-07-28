# RESET-001 — Research Program Reconstruction

## Decision

The previous A–E loop is stopped as a mainline research program.

It produced useful diagnostics, but it did not establish:

- a novel intelligence principle
- a publishable scientific claim
- a reproduced external baseline
- a cumulative model that improved on a fixed benchmark
- a mathematically grounded research question

Continuing to generate another opaque-token mechanism would have low expected value.

## What changes immediately

1. No new A/B/C/D toy-mechanism cycles.
2. No claim of novelty or foundational discovery from prior PRs.
3. One canonical reconstruction branch replaces the stacked-PR chain as the base for new work.
4. Public benchmark reproduction precedes new model invention.
5. Prior art is compared by assumptions, observables, supervision, identifiability result, and downstream metric.
6. A new hypothesis is allowed only after a baseline gap and a theorem-level or preregistered claim exist.

## Productive target

The immediate target is not “build intelligence.” It is:

> Establish whether joint recovery of causal variables and raw-language meaning under unknown intervention targets is a genuinely open, identifiable, and experimentally measurable problem.

This target can terminate in three legitimate outcomes.

- **Adopt**: direct prior art is absent, baselines are reproduced, and a falsifiable gap remains.
- **Narrow**: only a restricted theorem or benchmark contribution is defensible.
- **Reject**: existing work already solves it or available observations make it unidentifiable.

All three are more useful than another unconstrained mechanism cycle.

## Deliverables

### D1 Prior-art matrix

Required columns:

- paper
- observation modality
- language input
- action/intervention input
- intervention target known?
- object/state structure given?
- pretrained model required?
- identifiability guarantee
- external task
- code/data availability
- unresolved mismatch with RQ-001

### D2 Reproduction package

A single benchmark package containing:

- pinned environment and dependency versions
- deterministic seeds
- official or faithful baseline
- language-blind and state-only controls
- evaluation contract
- model/RSS/runtime measurements
- raw logs and reproduction command

### D3 Research claim preregistration

Before new architecture code:

- exact claim
- strongest existing baseline
- primary metric
- expected effect size
- controls
- failure criterion
- compute ceiling
- novelty evidence
- theorem or identifiable empirical mechanism

## Stop conditions

The candidate research question is rejected when any of the following holds.

- A directly equivalent published method exists.
- Public baseline reproduction fails and cannot be diagnosed.
- Language adds no external ability beyond state/action baselines.
- Unknown intervention targets make the problem unidentifiable without assumptions that violate the project constraints.
- The proposed contribution reduces to another surface grouping, response equality, candidate filtering, or oracle-axis benchmark.

## Repository policy

Past PRs remain readable as a negative-results archive. They are not used as the base of future work. New work starts from the reconstruction branch and is merged into one canonical research line.
