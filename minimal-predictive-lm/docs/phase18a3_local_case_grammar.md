# Phase 18a-3: Local Japanese case grammar

## Question

Phase 18a-2 discovered entity and action spans in continuous Japanese strings, but
the final model still stored complete residual frames such as `E0がE1にA`.
Phase 18a-3 asks whether those whole forms can be replaced by reusable local
atoms.

## Representation

After Phase 18a-2 discovers entity and action lexemes, every complete event is
reduced to:

```text
action
first entity's following marker
second entity's following marker
action position among E0, E1, A
observed source/destination direction
```

No list of Japanese particles, suffix test, script test, or full frame template is
provided to the local grammar learner. The residual strings immediately attached
to the two grounded entities become candidate case markers.

The semantic equation is:

```text
effective direction = action bit XOR first-case-marker bit
```

The second marker must have the opposite latent polarity. The action-marker
bipartite graph must be connected and cycle-consistent. Order patterns are stored
as independent atoms, not as part of an action/case tuple.

## Frozen campaign

The controlled language contains:

- four induced actions;
- six case markers in two latent role classes;
- three action positions;
- nine observed action/case/order combinations;
- nineteen repetitions per identifying edge;
- one adversarial direction flip per edge;
- two incomplete grounding rows that must be skipped.

The held-out suite contains twelve whole forms. Every held-out form simultaneously
uses:

- an unseen action × first-marker pair;
- an unseen first-marker × second-marker pair;
- an unseen first-marker × order pair;
- an unseen complete action/marker/order tuple.

Each form is evaluated with an entity-role reversal pair, giving twenty-four rows.
The two rows in a pair have the same character multiset and initial state but
require different transitions.

## Falsification controls

The campaign fails unless all of the following hold:

1. tied noisy majorities are rejected;
2. disconnected action-marker graphs are rejected;
3. contradictory XOR cycles are rejected;
4. two markers with the same learned role cause abstention;
5. an unknown marker causes abstention;
6. the Phase 18a-2 literal-frame model has zero held-out coverage;
7. complete-tuple, action-marker, marker-pair, and marker-order memorisers all have
   zero held-out coverage;
8. the local grammar reaches 100% accuracy and coverage;
9. the positionless character baseline remains bounded at 50%.

## Resource accounting

The report separates:

- serialized learned local grammar;
- literal storage for the nine observed templates;
- literal enumeration of every form supported by the learned atomic cross product;
- Phase 18a-3 source bytes;
- excluded Python runtime and standard-library substrate.

A small observed lookup table can be shorter than the local grammar while having
zero transfer. The relevant scaling comparison is therefore the local grammar
versus literal enumeration of all forms it supports.

## Claim boundary

Passing this campaign demonstrates local recombination inside a small controlled
Japanese case grammar. It does not establish unrestricted tokenization, general
Japanese grammar, reading comprehension, passive or causative understanding, or
Japanese high-school-level intelligence.

The next gate must induce inflection and voice transformations, then test whether
active, passive, causative, and negative forms share one event representation
instead of becoming separate surface lexemes.
