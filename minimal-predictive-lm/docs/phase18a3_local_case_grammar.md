# Phase 18a-3: Local Japanese case grammar

## Question

Phase 18a-2 discovered entity and action spans in continuous Japanese strings, but
the final model still stored complete residual frames such as `E0がE1にA`.
Phase 18a-3 asks whether those whole forms can be replaced by reusable local
atoms.

## Representation

Each complete event is reduced to:

```text
action
first entity's following marker
second entity's following marker
action position among E0, E1, A
observed source/destination direction
```

No list of Japanese particles, suffix test, script test, or full frame template is
provided to the local grammar learner. The residual strings immediately attached
to grounded entities become candidate case markers.

The semantic equation is:

```text
effective direction = action bit XOR first-case-marker bit
```

The second marker must have the opposite latent polarity. The action-marker graph
must be connected and cycle-consistent. Order patterns are independent atoms,
not parts of memorized action/case tuples.

## Failed c1 campaign and identifiability repair

The original frozen c1 campaign failed twice in CI. Entity grounding was correct,
but `受ける` and `移す` each occurred in only one boundary environment. The generic
substring learner therefore had insufficient evidence to identify them as reusable
action spans. All twelve exact-cover candidates were rejected as disconnected local
grammars.

Campaign c2 does not weaken the boundary-diversity rule. It adds one independent
case/order environment for each underidentified action. This changes the campaign
from nine to eleven observed whole forms. The failure and repair are retained as an
identifiability result rather than hidden as an implementation detail.

## Repaired prospective campaign c2

The controlled language contains:

- four induced actions;
- six induced case markers in two latent role classes;
- three induced action positions;
- eleven observed action/case/order whole forms;
- nineteen repetitions per identifying edge;
- one adversarial direction flip per edge;
- two incomplete grounding rows that must be skipped.

The action search produces sixteen substring candidates and fourteen exact covers.
Only one cover survives the connected, cycle-consistent local grammar constraints:
`写す・受ける・渡す・移す`.

The held-out suite contains twelve whole forms. Every held-out form simultaneously
uses:

- an unseen action × first-marker pair;
- an unseen first-marker × second-marker pair;
- an unseen first-marker × order pair;
- an unseen complete action/marker/order tuple.

Each form is evaluated with an entity-role reversal pair, giving twenty-four rows.
The two rows in a pair have the same character multiset and initial state but
require different transitions.

## Result

- 211 total observations, 209 semantic rows, 2 skipped rows;
- 100% accuracy and 100% coverage on the 24 held-out rows;
- literal whole-frame baseline coverage 0%;
- full-tuple, action-marker, marker-pair, and marker-order memorizer coverage 0%;
- positionless character baseline upper bound 50%;
- 11 observed forms expand to 216 forms in the learned atomic cross product;
- learned atomic payload 5,120 bits;
- literal enumeration of all 216 supported forms 73,880 bits.

Storing only the eleven observed forms is smaller at 3,728 bits but has zero held-out
coverage. The valid scaling comparison is therefore not against a non-generalizing
training lookup table, but against literal enumeration of the capability set the
atomic grammar supports.

## Falsification controls

The campaign also requires:

1. tied noisy majorities are rejected;
2. disconnected action-marker graphs are rejected;
3. contradictory XOR cycles are rejected;
4. two markers with the same learned role cause abstention;
5. an unknown marker causes abstention;
6. incomplete observations are skipped rather than forced into a rule;
7. bounded direction noise is recovered without exception rules.

## Claim boundary

This demonstrates local recombination inside a small controlled Japanese case
grammar. It does not establish unrestricted tokenization, general Japanese grammar,
reading comprehension, passive or causative understanding, or Japanese
high-school-level intelligence.

The next gate must induce inflection and voice transformations, then test whether
active, passive, causative, and negative forms share one event representation
instead of becoming separate surface lexemes.
