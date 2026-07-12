# Phase 14a: pinned general ontology and proof-cache compilation

## Question

Can the remaining semantic abstentions from Phase 13d be resolved by a general public ontology without inserting benchmark-specific item memberships?

## Protocol

Open English WordNet 2025 is downloaded from its public release URL and verified against SHA-256:

`38b16326159f51853626b7d24a44c453fa88ab33f06fce5ec8fc5996d1c2be93`

The worker parses noun synsets, lemma forms, noun exceptions, and hypernym edges. For each membership query it performs a shortest-path search and retains the proof path in a query cache. Unknown lemmas remain unknown. A missing hypernym path is provisionally treated as non-membership in Phase 14a, which is later shown to be too strong for open-world knowledge.

The reported model size includes the entire 9.6MB ontology archive, not only the much smaller proof cache.

## Result

The public five-axis score rises from 172/200 to 196/200. All four residual errors are object-counting undercounts caused by the same missing relation: WordNet has no `garlic → vegetable` hypernym path.

This is a useful negative result. The retrieval algorithm is consistent and the ontology source is pinned, but a single curated ontology does not define every evaluation category boundary identically.

## Consequence

A missing path must be represented as open-world absence rather than logical negation. Additional evidence sources should be composable with provenance, while explicit contradictions must produce uncertainty instead of silent overriding.

## Claim boundary

Phase 14a is zero-benchmark-training with respect to the public examples, but it relies on a large human-curated knowledge source. It does not demonstrate autonomous knowledge acquisition or general intelligence.
