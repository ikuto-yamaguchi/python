# SPARC-HS12: outcome-directed sparse relational plan induction

HS12 generalises HS11 beyond arithmetic. It learns which relation sequence to execute from source-grounded question-answer demonstrations.

## Learning mechanism

1. Every active episodic claim is indexed as a directed typed relation edge.
2. For each demonstration, HS12 identifies the subject mentioned in the question and the answer endpoint.
3. A bounded local search enumerates relation paths from that subject to the demonstrated endpoint.
4. The shortest relation sequence shared by all demonstrations becomes one reusable plan.
5. The question surface is stored separately from the relation sequence, so one plan can serve several phrasings.
6. At inference, only the captured subject and the plan's required outgoing relation slots activate.

The same mechanism can learn paths such as:

- `classification -> body-temperature property`;
- `belongs-to-region -> main-industry`;
- repeated `cause -> cause -> cause` chains.

## Revision and ambiguity

- inactive superseded episodes are ignored;
- conflicting active values at a required relation cause an explicit refusal;
- each successful answer lists the source IDs for every traversed edge.

## Resource contract

- no global node, episode, relation or plan scan at inference;
- bounded path length and bounded active frontier;
- one shared relation sequence per induced plan;
- query-local subject dictionary lookup depends on question length, not stored subject count;
- no Transformer, softmax attention or growing KV cache.

## Claim boundary

HS12 learns bounded relation-path programs. It does not yet invent new predicates, quantify over arbitrary sets, prove theorems or plan open-ended investigations, and it is not Japanese high-school-level general intelligence.
