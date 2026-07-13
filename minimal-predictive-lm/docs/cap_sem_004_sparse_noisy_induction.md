# CAP-SEM-004: sparse noisy definition and usage induction

## Ability definition

Ground the sixteen opaque relation expressions from `CAP-SEM-003` while keeping the `CAP-SEM-001` semantic graph runtime and the canonical `CAP-SEM-002` surface bridge frozen, but remove the complete code-by-direction behavioral contrast table.

Each expression receives only:

- one short raw definition against a known expression;
- four ordinary contrast usages using two relation-family anchors in both argument directions;
- one multi-fact, multi-hop usage;
- one deliberately corrupted observation.

The learner must recover all statement and query meanings, tolerate the single corruption, and reject insufficient or excessively noisy evidence.

## Definition connector induction

The phrases expressing “same direction” and “inverse direction” are not assigned semantics in code. Known-known definition sentences calibrate each recurring raw definition skeleton. A novel definition then proposes a latent code by combining the known anchor code with the learned connector transformation.

A metamorphic run replaces every opaque relation expression and every definition connector phrase. The connector transformations and lexical meanings must be learned again from the transformed corpus.

## Usage induction

Each usage document contains exactly one unknown relation expression, at least one additional fact, and only a final Boolean answer. Candidate codes are tested through the unchanged graph predictor. Definition disagreement and answer disagreement contribute equally to a robust error score.

A code is accepted only when:

- at least four usage documents and one definition are available;
- the lowest-error code is unique;
- its error fraction is at most 25%.

## Gates

- 128 unseen two-to-five-hop documents using only opaque expressions;
- template and fact-order shift;
- complete alias and connector replacement;
- exact raw-text memorization baseline;
- one corrupted observation per expression;
- insufficient-evidence and excess-noise rejection;
- unregistered-expression abstention;
- byte-identical fingerprints for the frozen semantic runtime and surface bridge;
- payload, training-compute, and inference-compute limits.

## Claim boundary

This is substantially weaker supervision than the complete CAP-SEM-003 contrast table, but it remains a synthetic controlled corpus. Every expression is still mapped into one of four existing latent relation codes. It does not allocate a new relation concept, learn from ordinary unlabelled Japanese documents, resolve coreference or ellipsis, or demonstrate Japanese high-school intelligence.

## Next capability

`CAP-SEM-005` must expand the ontology itself: data should force the frozen four-code inventory to allocate a genuinely new inverse relation pair without adding a relation-specific solver branch.
