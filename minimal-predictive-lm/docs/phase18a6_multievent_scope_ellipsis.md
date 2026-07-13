# Phase 18a-6: Multi-event order, scope, and ellipsis

## Research question

Phase 18a-5 still evaluated one event per sentence. Phase 18a-6 asks whether a
learner can recover reusable discourse operators from continuous Japanese
strings and anonymous state transitions:

- execute the left event and then the right event;
- execute the right event and then the left event;
- suppress the left event and execute only the right event;
- resolve one omitted participant in the second clause from the first clause.

Entity, action, and elementary case atoms are inherited from earlier phases.
Connector and ellipsis-marker spans are extracted as residual substrings; their
semantic labels are not supplied.

## Finite hypothesis class

Three observed connector lexemes are assigned injectively to:

```text
LR         left then right
RL         right then left
R          suppress left, execute right
```

Each one-role ellipsis marker is assigned one of four strategies:

```text
explicit side ∈ {left, right}
inherited antecedent side ∈ {left, right}
```

The complete declared search contains 72 joint connector/ellipsis models. The
learner minimizes prediction error under bounded corrupted observations and
requires a unique optimum with a positive margin.

## Frozen split

Training contains nine connector × clause-form × action-pair cells and 81 raw
continuous strings. Every cell has nine repetitions and one corrupted final
state.

Held-out evaluation contains six previously unseen joint tuples and two role
variants per tuple, for twelve rows. The connector, ellipsis rule, and atomic
action semantics must therefore be recombined rather than retrieved as one
seen template.

## Identifiability result

Execution order is observable only when the two events do not commute. A
negative control containing only disjoint copy events must leave LR and RL
indistinguishable and cause induction to reject the data as non-identifying.

A matched LR/RL pair has the same unordered event multiset and initial state but
different final states. Any model that discards order is therefore bounded at
50% on that pair.

## Falsification controls

The campaign requires:

- exact recovery of all three connector programs;
- exact recovery of both ellipsis rules;
- recovery from one bounded corruption per training cell;
- positive error margin over the second-best model;
- 100% held-out accuracy and coverage;
- zero whole-sentence and joint-tuple memorizer coverage;
- 50% orderless-event upper bound;
- rejection of commuting-only training data;
- abstention on unknown connectors and ellipsis markers;
- a connector intervention that changes execution order;
- a suppress-left intervention whose result is invariant to the left event;
- an antecedent intervention that changes the resolved elliptical event.

## Resource accounting

The learned payload stores three connector programs, two ellipsis rules, and
the inherited finite entity/action inventory. It is compared with literal
enumeration of the supported connector × form × action-pair capability grid.
Python and the standard library remain excluded and declared substrate.

## Claim boundary

Passing this phase demonstrates controlled two-event execution order,
suppress-left negation scope, and two one-role ellipsis patterns. It is not
evidence for unrestricted Japanese discourse, general coreference, reading
comprehension, or Japanese high-school-level intelligence.

The next gate should add three-or-more-event recursive composition, explicit
scope nesting, and discourse reference across sentence boundaries.
