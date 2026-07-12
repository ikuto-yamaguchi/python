# Phase 17c: Factorial resource identification and the road to gpt-oss-class comparison

## Purpose

Phase 17b established a non-degenerate tiny-model curve, but all four resource
budgets increased together. It therefore could not tell whether accuracy was limited
by persistent model bits, training evidence, induction search, or inference work.

Phase 17c varies one resource at a time around one common high-resource anchor and
adds a strict campaign-wide candidate-evaluation limit. The parser, hypothesis
language, task mixture, validation set, and blind suite remain unchanged.

This is a diagnostic campaign. It identifies the present learner's bottleneck; it
does not extrapolate the Phase 12 generated mixture to gpt-oss-class intelligence.

## Frozen variables

Within campaign C1, freeze:

- generic prompt parser and lexical feature extractor;
- hypothesis and primitive language;
- fitting and validation criteria;
- calibration, consolidation, and blind suites;
- random seeds;
- abstention and correctness policy.

The only architecture-level change from Phase 17b is replacing a per-fit-only cap
with a strict global induction budget. That change starts a new named campaign and
does not overwrite Phase 17b.

## Independent resource sweeps

Use one shared high-resource anchor and three geometric levels per axis:

```text
B_acquired:  128 B, 512 B, 8 KiB
D_train:       4 KiB, 32 KiB, 512 KiB of evidence
C_induce:    500, 5,000, 100,000 candidate evaluations
C_test:        8, 32, 256 operations per item
```

Each point is trained from scratch at seeds 17, 29, and 43. Other resources stay at
the anchor while one resource changes.

The strict induction accounting rule is:

```text
sum of every attempted candidate fit <= C_induce
```

Rejected candidates, failed fits, feature partitions, and fallback attempts all
consume the same global budget. Running out of search causes selective abstention,
not silent overspend or global model deletion.

## Interpretation

A large low-to-high gain on one sweep means that resource is an active bottleneck
for the current learner. A flat sweep can mean either:

1. that resource is already sufficient;
2. another resource is binding first;
3. the fixed representation cannot express the missing capability.

The one-factor-at-a-time design does not identify interactions. A later dense grid
is justified only after this pilot shows which axes matter.

## Route toward gpt-oss-class comparison

The project will not jump from a 729-byte acquired model to a speculative GiB run.
It advances through falsifiable gates.

### Gate 1: resource identification

Required:

- strict limits on acquired bits, evidence bits, total induction work, and
  inference work;
- multiple seeds;
- independent sweeps;
- correct abstention under exhausted budgets.

Phase 17c implements this gate.

### Gate 2: representation growth without manual solver accumulation

A representation change is accepted only when it:

- is induced from training evidence rather than keyed to a benchmark;
- improves at least two previously held-out task families;
- survives renaming, paraphrase, ordering, and distractor shifts;
- has an ablation showing that the new mechanism is necessary;
- permits obsolete rules or primitives to be pruned;
- starts a new scaling campaign rather than being inserted between size points.

The first target is autonomous acquisition of string and surface transformations,
because Phase 17b saturated despite unused persistent capacity.

### Gate 3: broad frozen workload

Before any gpt-oss comparison, the workload must include independent families for:

- raw-language grounding and paraphrase;
- arithmetic, formal, causal, temporal, and reference reasoning;
- factual learning, provenance, contradiction, and retrieval;
- long-context state and sparse memory;
- real repository localization, patching, test repair, and rollback;
- constrained and open-ended writing;
- tool-use planning and calibrated abstention.

Training, validation, blind evaluation, and public comparison sets must be
separated before results are inspected.

### Gate 4: forecast before allocation

Fit scaling surfaces only on smaller points. Reserve at least two larger points and
one shifted workload as unseen forecast targets. Compare constant, log-linear,
power-law, sigmoid, and monotone non-parametric baselines.

GiB-scale allocation is allowed only when:

- held-out budget forecasts are calibrated;
- performance has not saturated under the current representation;
- resource exponents are stable across seeds and shifted mixtures;
- the projected lifetime cost is competitive with the chosen gpt-oss reference.

## Size target policy

The 1--5 GiB target for a gpt-oss-20b-class comparison and the 8--30 GiB target for
a gpt-oss-120b-class comparison are research objectives, not current predictions.

Success requires parity under matched information, tools, reasoning budgets, and
evaluation breadth while reporting:

- all persistent core, acquired, and knowledge bits;
- active working state and memory traffic;
- induction and inference operations;
- latency, energy, and deployment horizon.

External indexes and tools remain part of total system cost. Moving knowledge out
of the learned model does not make it free.

## Claim boundary

Phase 17c may support statements about which resource limits the present tiny
learner. It cannot support a byte-to-gpt-oss conversion, a universal scaling law,
or a claim that the current architecture will reach broad LLM parity at any finite
size.
