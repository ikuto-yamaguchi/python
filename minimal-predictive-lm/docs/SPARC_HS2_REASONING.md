# SPARC-HS2: bounded relational microprograms

HS2 adds an event-driven relational cortex to the interactive HS1 language model.

## Resource principle

Global knowledge capacity and per-query activity are separated. Facts are stored as sparse typed edges. A query starts from the mentioned entity and propagates only along the requested relation, under hard limits on hops, activated nodes and inspected edges. There is no dense graph scan, full-history attention or growing KV cache.

## Supported bootstrap relations

- taxonomic inclusion (`isa`), including bounded transitive inference;
- explicit negative evidence;
- named properties;
- causal chains;
- ordered comparisons such as height, size, speed, weight and length.

The returned answer includes the local evidence path, allowing reasoning to be audited.

## Scale profiles

- CI: 100,000 entities, 1,000,000 relation edges, at most 128 activated nodes;
- desktop-large: 2,000,000 entities, 32,000,000 edges, at most 256 activated nodes;
- desktop-XL: 8,000,000 entities, 128,000,000 edges, at most 512 activated nodes.

Capacity is allocated only for learned entities and edges.

## Claim boundary

The Japanese relation templates are bootstrap perceptual reflexes, not a learned general semantic parser. HS2 is therefore not Japanese high-school-level intelligence. HS3 must induce relation schemas from broad natural text and compose novel Japanese answers instead of relying on fixed answer forms.
