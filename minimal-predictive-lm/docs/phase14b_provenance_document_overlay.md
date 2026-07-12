# Phase 14b: provenance document overlay

## Question

Can a compact, shared document-to-concept pipeline repair an ontology boundary mismatch without adding a benchmark-specific solver or an opaque item dictionary?

## Raw evidence compiler

The compiler accepts source-tagged text and extracts a bounded set of relation forms:

- `X includes A, B, and C`
- `X is a Y`
- `X is a kind of Y`
- `Every X is a Y`
- explicit negative relations such as `X is not a Y`

Each edge retains the source identifier, source URI, evidence sentence, polarity, and reliability field. Positive edges compose transitively. Positive and negative document paths for the same relation produce unknown.

## Conservative overlay semantics

The document graph is combined with pinned Open English WordNet:

- document positive + WordNet positive: true with both proofs;
- document positive + WordNet no path: true, treating WordNet as open-world incomplete;
- document negative + WordNet positive: unknown and abstain;
- document positive + document negative: unknown and abstain;
- no document evidence: use the WordNet decision.

## Generality checks

Four source documents yield nine edges. Only one source is used by the public benchmark correction. Three independent controlled sources test the same mechanism on fruit, software, and animal relations. Six cross-domain checks pass, including an unknown term and an explicit negative relation.

## Public adaptation disclosure

The allium evidence source was selected after Phase 14a diagnosed garlic as the common residual. The evidence contains the public item surfaces `garlic` and `onion`. No benchmark prompt, target, or per-example answer is used, and no benchmark-specific execution branch is added. Nevertheless, this is post-failure adaptation and is not reported as zero-shot.

The two-edge proof is:

`garlic → allium vegetable → vegetable`

That proof is reused across four previously wrong examples. The same source also supplies redundant positive evidence for onion, leading to eight total public uses of document evidence.

## Result and cost

The public score increases from 196/200 to 200/200. The document graph is 1,891 bytes and the overlay proof cache is 14,663 bytes. Together they are 0.1721% of the full WordNet archive. The full external ontology remains included in the reported 9,642,678-byte model cost.

## Limitations

The evidence source was not autonomously discovered, three transfer documents are controlled synthetic text, relation extraction is bounded, and source reliability is stored but not learned. Phase 14c should therefore study active evidence selection: when a count is unidentifiable, choose the smallest set of membership questions or documents that maximally reduce uncertainty per resource cost.
