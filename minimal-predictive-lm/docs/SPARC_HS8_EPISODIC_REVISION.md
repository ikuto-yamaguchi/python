# SPARC-HS8: Sparse Episodic Revision Memory

HS8 adds a bounded long-passage and revision layer to the shared HS7 conversational model.

## Compute contract

- no full-history attention;
- no KV cache that grows with conversation length;
- no scan over all stored episodes at query time;
- global episode capacity is separated from active query candidates;
- at most 32 retrieved episode candidates and 192 posting reads in the CI profile;
- evidence sources are retained with every episode;
- the working set is a fixed 32-entry deque.

## Memory mechanism

A document is split into short episodic records. Character n-gram anchors build an inverted index. Query routing starts from the rarest matching anchors and stops when the bounded candidate or read budget is reached. The complete episode list is never scored.

Repeated subject-relation claims are versioned. A normal conflicting document keeps both active and produces an explicit unresolved-conflict answer. A revision document marked as a correction, update, current information or explicit revision suppresses the older conflicting value while retaining it for audit.

Causal claims are stored as local directed edges. A why-question starts from a retrieved consequence and walks backward through at most four local cause edges. Each returned answer includes the source IDs used by the path.

## Claim boundary

HS8 is a sparse evidence-memory and revision operator. Its Japanese claim parser is still a bootstrap surface parser, and retrieval is not unrestricted semantic reading comprehension. Passing HS8 does not establish Japanese high-school-level intelligence. Later stages must learn richer discourse roles, argument structure, counterfactual reasoning, proof plans and broad real-curriculum free response.
