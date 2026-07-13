# Phase 18b-2: Induced integer operations

## Question

Phase 18b-1 answers recursive state questions with independently replayable
traces, but every primitive transition only copies one value to another.
Phase 18b-2 asks whether unknown operation words can be grounded as integer
addition, subtraction, and multiplication from observed state changes, then
recombined inside previously unseen recursive calculations.

This is a controlled arithmetic gate. It is not a claim of high-school
mathematics or natural Japanese word-problem understanding.

## Unknown arithmetic lexemes

The atomic surface form is:

```text
ENTITYをINTEGERだけLABEL
```

Three labels recur in the observations. Their meanings are not assigned by
the parser or learner. The learner evaluates all six bijections between the
three surface labels and:

```text
ADD
SUB
MUL
```

The correct mapping is accepted only when it uniquely minimizes complete
state-transition error across simple and composed observations.

## Inherited control structure

Sequence, reverse sequence, conditions, and subtree suppression are inherited
from Phase 18a-7. Arithmetic operation meanings are newly induced in this
phase.

The same operation atoms can appear inside:

- left-to-right and right-to-left compositions;
- equality and inequality branches;
- suppressed subtrees;
- recursive programs containing four to five arithmetic atoms.

Order matters. For example, adding and then multiplying is generally not the
same as multiplying and then adding.

## Frozen induction campaign

Training contains six program families and 54 observations:

- one direct family for each unknown operation label;
- three composed or conditional families;
- nine observations per family;
- one adversarially corrupted final state per family;
- negative and positive starting values;
- equality and inequality condition cases.

The learner searches all six operation mappings. No exception table is
allowed.

## Frozen held-out evaluation

The held-out suite contains six previously unseen recursive programs, each
under two initial states, for 12 questions total. It includes:

- unseen operation amounts;
- unseen operation orders;
- nested conditions;
- reverse execution order;
- whole-subtree suppression;
- negative intermediate and final integers;
- four to five arithmetic atoms.

Each problem embeds its initial integer state, recursive calculation, and
query entity in one text string. The machine must return both the final
integer and a complete trace.

## Independent trace verification

Arithmetic trace steps contain:

- target entity;
- surface operation label;
- induced arithmetic operation;
- operand;
- value before the operation;
- value after the operation;
- recursive path.

The verifier independently parses the problem and replays every arithmetic,
sequence, condition, and suppression step. Empty traces, altered intermediate
values, and wrong answers attached to otherwise valid traces are rejected.

## Falsification gates

The campaign fails unless all of the following hold:

1. the unique recovered mapping equals the generating ADD/SUB/MUL mapping;
2. bounded corrupted observations are absorbed without exception rules;
3. the second-best operation mapping has strictly larger error;
4. held-out answer accuracy and coverage are both 100%;
5. every held-out trace is independently verified;
6. whole-problem memorization has zero held-out coverage;
7. returning the queried initial value scores below 50%;
8. an orderless operation-set baseline is bounded at 50%;
9. empty, tampered, and wrong-answer traces are rejected;
10. intervening on an induced operation meaning changes predictions.

## Non-identifiability controls

Some numerical observations cannot distinguish operations:

- adding zero and subtracting zero have the same effect;
- multiplying by one is the identity;
- from value two with operand two, addition and multiplication both produce
  four.

These controls are retained explicitly. A larger search budget cannot infer
an operation distinction that the chosen observations do not reveal.

## Resource accounting

The learned payload includes:

- inherited compact control semantics;
- the three induced operation mappings;
- entity names and the arithmetic atom schema.

The report separately records source bytes and excludes the Python runtime and
fixed parser. No claim such as a few-hundred-byte complete mathematics model
is permitted.

## Claim boundary

Passing Phase 18b-2 demonstrates controlled recursive integer calculations
using induced ADD, SUB, and MUL lexemes with machine-checkable derivations.
It does not establish:

- unbracketed natural Japanese word problems;
- division, fractions, powers, or roots;
- equations or symbolic algebra;
- geometry, probability, or statistics;
- mathematical proof;
- Japanese high-school-level mathematics or intelligence.

The next gate should add division and rational numbers, then require equation
construction and solution rather than direct execution of an exposed
calculation tree.
