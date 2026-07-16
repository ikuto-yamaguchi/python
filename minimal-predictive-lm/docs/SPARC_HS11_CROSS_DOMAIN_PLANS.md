# SPARC-HS11: sparse cross-domain evidence-to-calculation plans

HS11 connects the previously separate episodic-reading and typed-mathematics systems.

## Learning mechanism

1. Source-grounded documents contribute typed quantity facts such as speed, duration, length, mass, area or price.
2. A subject-to-relation index is updated at ingestion; query-time reasoning never scans all episodes.
3. For several question-answer demonstrations, HS11 identifies the mentioned subject and the relations available for that subject.
4. It searches small ordered subsets of relations and synthesizes the minimum-cost dimensionally valid expression tree that reproduces all answers.
5. The resulting plan stores relation slots, one shared expression tree and one or more learned question surfaces.
6. An unseen subject activates one plan, retrieves only the required relation slots, executes the tree and renders the result with source IDs.

## Safety and revision

- conflicting active quantities for a required relation cause an explicit refusal rather than arbitrary selection;
- an HS8 revision deactivates the old episode and the same plan then uses the revised value;
- dimensional typing from HS7 is retained throughout plan induction and execution.

## Resource contract

- no global subject, episode or plan scan at inference;
- at most 32 candidate plan surfaces;
- a learned plan reads only its required relation slots;
- expression trees are interned once and shared across question surfaces;
- no Transformer, softmax attention or growing KV cache.

## Claim boundary

HS11 learns bounded evidence-to-arithmetic plans. It does not yet induce arbitrary algorithms, proof strategies or open-ended research plans, and it is not Japanese high-school-level general intelligence.
