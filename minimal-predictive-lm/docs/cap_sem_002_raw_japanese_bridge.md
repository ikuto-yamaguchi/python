# CAP-SEM-002: raw controlled-Japanese clause and argument grounding

## Ability definition

Learn a surface-to-event bridge from continuous controlled Japanese strings while keeping the complete `CAP-SEM-001` latent relation map and graph runtime frozen. The bridge must recover clause punctuation, entity spans, recurring surface templates, and argument direction from raw strings paired only with final Boolean truth labels.

A new relation solver is forbidden. Every parsed fact and query is passed to the unchanged `CAP-SEM-001.predict` runtime.

## Training signal

The learner receives 288 records with two fields only:

- a continuous string containing one fact sentence and one query sentence;
- a final Boolean answer.

The raw records do not expose clause arrays, entity spans, argument roles, template IDs, relation IDs, parse trees, or proof traces. Relation marker meanings are inherited from the already frozen `CAP-SEM-001` payload.

The training procedure:

1. searches recurring delimiter roles rather than fixing `。` and `？`;
2. discovers two low-frequency entity spans shared by the fact and query;
3. abstracts three statement and three query surface skeletons;
4. evaluates all 64 argument-orientation assignments through the frozen semantic runtime;
5. accepts the remaining assignments only when they form one prediction-equivalent behavior class.

## Held-out gate

The 128 held-out examples contain two through five fact edges, unseen entity strings, irrelevant facts from the other relation family, unseen template combinations, and both true and false queries.

Metamorphic gates change template placement, reverse fact order, and replace the punctuation pair with `；` and `！`. The latter requires relearning delimiter roles from the transformed training data.

## Baselines and budgets

- Exact raw-text memorization is frozen as a baseline.
- Held-out accuracy and parse coverage must each reach at least 95%.
- Every template/order and punctuation variant must retain at least 95%.
- The learned bridge payload must remain at most 4,096 bytes.
- Average semantic inference must remain below 128 counted operations.
- The `CAP-SEM-001` payload fingerprint must be byte-identical before and after bridge learning.

## Claim boundary

Passing removes supplied clause arrays and argument slots for this controlled grammar. It does not learn arbitrary relation vocabulary, unrestricted Japanese syntax, ellipsis, morphology, coreference, world knowledge, dialogue, or Japanese high-school intelligence. Entity strings are deliberately distribution-shifted symbols so that the gate measures template and role transfer rather than name memorization.

## Next capability

`CAP-SEM-003` must remove the inherited closed relation vocabulary. It should ground genuinely unseen relation expressions from definitions and usage inside a mixed continuous stream while reusing the same semantic graph runtime. Adding another hand-written relation-specific solver does not count.
