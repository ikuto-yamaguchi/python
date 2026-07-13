# CAP-SEM-003: open relation-expression grounding

## Ability definition

Ground relation expressions that are absent from the frozen CAP-SEM-001 vocabulary into its existing four latent relation codes, while keeping both the CAP-SEM-001 graph predictor and the canonical CAP-SEM-002 surface bridge frozen.

The learner must not receive relation IDs, inverse labels, parse trees, entity slots, proof traces, or the generator's novel-expression groups.

## Training signal

The learner receives a mixed set of continuous controlled-Japanese documents with two fields only:

- one raw string containing one fact and one query;
- one final Boolean answer.

Some documents use an opaque novel expression in the fact and a known frozen query anchor. Others use a known fact anchor and an opaque novel query expression. Every opaque expression is contrasted with all frozen relation codes in both argument directions. These examples act as behavioral definitions; they are not natural-language dictionary definitions.

The CAP-SEM-002 skeletons are compiled with an unconstrained marker span. The learner parses the raw strings, evaluates each possible frozen latent code through the unchanged CAP-SEM-001 predictor, and accepts a code only when it is the unique zero-error explanation.

## Held-out gate

Held-out documents contain:

- 128 unseen multi-hop records;
- only opaque relation expressions in facts and queries;
- unseen entity names;
- two-to-five-edge reasoning chains;
- irrelevant facts from another relation family;
- unseen template and fact-order combinations;
- opaque synonym substitution;
- alternate punctuation that requires relearning only the CAP-SEM-002 delimiter bridge.

## Frozen dependencies

The following SHA-256 fingerprints must remain unchanged:

- the CAP-SEM-001 learned semantic payload;
- the canonical CAP-SEM-002 surface bridge payload.

The learned CAP-SEM-003 object contains only the novel statement/query expression-to-latent-code adapter.

## Baselines and budgets

- Exact raw-text memorization must be beaten by at least 25 percentage points.
- Held-out accuracy and coverage must each reach at least 95%.
- Every template, ordering, entity-renaming, synonym, and punctuation variant must reach at least 95%.
- Learned lexicon payload: at most 4,096 compressed bytes.
- Executable total description: at most 500,000 bits.
- Training operation ledger: at most 500,000 operations.
- Average inference ledger: at most 1,024 operations per document.

## Claim boundary

The novel strings are genuinely absent from the frozen semantic vocabulary, but their meanings are learned from a complete controlled contrast set against known anchors. Passing does not demonstrate natural-language definition understanding, unrestricted vocabulary learning, arbitrary Japanese parsing, world knowledge, dialogue, or high-school intelligence.

## Next capability

CAP-SEM-004 must reduce the supervision requirement. It should infer new relation expressions from sparse, noisy definitions and ordinary multi-fact usage rather than a complete code-by-direction contrast matrix, while preserving the same semantic runtime and surface compiler.
