# Phase 18a-7: Recursive conditional discourse

## Question

Phase 18a-6 induced two-event order, suppress-left scope, and one-role
ellipsis, but its program depth was fixed. Phase 18a-7 asks whether the same
kind of compact semantic factors can execute previously unseen recursive
trees containing four to five events.

This remains a controlled-language falsification gate. It is not a claim of
general Japanese reading comprehension.

## Surface language

The input has no whitespace. Recursive constituent boundaries are exposed by
Japanese corner brackets:

```text
続いて【アキがボブに渡す】【その人がチカに写す】
同じなら(アキとボブ)【...】【...】
せず【...】
```

Punctuation varies and may create clause or sentence boundaries inside the
brackets. References therefore cross a punctuation boundary, but not an
unmarked unrestricted Japanese sentence boundary.

The parser does not receive a list of operator or reference strings. It
extracts residual labels from unary, binary, conditional, and event argument
positions. The hypothesis-class arities are fixed:

- two binary labels must be a permutation of left-to-right and right-to-left;
- two condition labels must be a permutation of equality and inequality;
- one unary label is tested as execute versus suppress-subtree;
- two unknown argument lexemes must be a permutation of previous semantic
  source and destination.

The resulting finite hypothesis class has 16 semantic systems.

## Recursive execution

Execution carries both a world state and the semantic source/destination of
the most recently executed event. This allows a reference inside a later
clause or nested branch to depend causally on the event that actually ran,
rather than the event that happens to appear first on the surface.

The induced operators are:

```text
続いて   = execute left subtree, then right subtree
先立ち   = execute right subtree, then left subtree
同じなら = select the first branch when two current values are equal
違うなら = select the first branch when two current values differ
せず     = suppress the complete child subtree
その人   = previous semantic destination
相手     = previous semantic source
```

Negation applies to the entire bracketed subtree. A shallow implementation
that suppresses only the first event is therefore falsified by nested
held-out cases.

## Frozen campaign

Training contains eight recursive programs and 72 observations. Every
program is observed nine times under renamed entities and varied states, with
one adversarially corrupted final state per program.

Held-out evaluation contains six new tree structures, each under two entity
renamings:

- 12 rows;
- recursive depth 3 to 4;
- 4 to 5 event leaves;
- unseen complete surfaces;
- unseen exact tree signatures;
- conditions nested under sequence;
- sequence nested under conditions;
- subtree negation;
- references crossing punctuation-delimited clauses.

## Falsification controls

The campaign fails unless all of the following hold:

1. all four semantic factor families are recovered uniquely;
2. the second-best hypothesis has strictly larger error;
3. held-out accuracy and coverage are both 100%;
4. whole-sentence memorization has zero coverage;
5. exact tree-signature memorization has zero coverage;
6. a parser limited to depth two has zero coverage;
7. unknown operators, references, and malformed brackets cause abstention;
8. internal interventions on sequence, condition, negation, and reference
   factors change predictions as prescribed.

Four negative controls also preserve cases where semantics are not
identifiable:

- commuting events do not identify execution order;
- equivalent condition branches do not identify equality versus inequality;
- a no-effect child does not identify suppress versus execute;
- equal antecedent values do not identify source versus destination
  reference.

These controls matter because more search or a larger model cannot recover a
factor that the observations do not distinguish.

## Resource accounting

The report separately records:

- serialized learned semantics plus inherited entity/action atoms;
- a literal table for the 12 frozen held-out state transitions;
- Phase 18a-7 source bytes;
- excluded Python runtime and fixed parser substrate.

The literal held-out table is only a finite comparison. Recursive capability
is not literally enumerable at arbitrary depth, so the report does not claim
a complete compression ratio for unrestricted recursion.

## Claim boundary

Passing Phase 18a-7 demonstrates recursive execution in a bracketed,
controlled Japanese-like language with equality conditions, subtree
negation, and cross-clause role references.

It does **not** establish:

- unbracketed Japanese parsing;
- open-domain coreference;
- factual reading comprehension;
- answer explanation;
- mathematical proof;
- Japanese high-school-level intelligence.

The next gate should turn a short discourse into an explicit question-answer
task and require a derivation trace that can be checked independently of the
final answer.
