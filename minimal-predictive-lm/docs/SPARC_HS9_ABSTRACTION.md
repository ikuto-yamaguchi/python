# SPARC-HS9: sparse abstraction and comparative reading

HS9 moves beyond retrieving isolated facts. It adds a bounded abstraction layer above HS8 episodic evidence.

## Mechanism

1. Paragraphs are stored as source-grounded episode sets.
2. Repeated `(relation, value)` structures across different subjects are interned once as abstraction nodes.
3. Topic queries route through rare character anchors to a small paragraph set.
4. Summaries select a few active claims and reuse abstraction nodes when several subjects share one property.
5. Comparisons align only the local relation lists of the requested subjects.
6. Argument frames connect explicit claim, reason and evidence sentences while preserving source IDs.

## Resource contract

- no full-history scan;
- no Transformer or softmax attention;
- no growing KV cache;
- at most 16 paragraph candidates and 128 posting reads per summary query;
- abstractions are stored once and referenced by member subjects;
- one persisted model retains HS8 conversation, revision, typed mathematics and HS9 reading structures.

## Claim boundary

HS9 is not unrestricted semantic abstraction. It induces repeated relational commonalities and explicit argument frames from Japanese prose. Metaphor, implicit author intent, broad literary interpretation and full high-school reading comprehension remain future work.
