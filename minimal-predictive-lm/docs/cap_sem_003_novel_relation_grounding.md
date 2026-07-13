# CAP-SEM-003: novel relation lexical grounding

## Ability definition

Ground previously unseen relation strings into the four latent relation classes already learned by `CAP-SEM-001`, using raw controlled-Japanese usage examples and final Boolean answers. The complete semantic graph runtime and the `CAP-SEM-002` surface bridge remain frozen.

This capability extends the vocabulary; it does not create a new relation concept.

## Training signal

The learner receives 384 raw examples. Eight meaningless relation aliases appear either in a fact or query while the other clause uses an already grounded relation expression. The learner sees no alias group, semantic ID, inverse label, parse tree, or proof trace.

For each unknown string, the learner evaluates all four latent codes through the frozen semantic runtime. A code is retained only when it reproduces every usable final truth label. Exactly one code must remain.

## Held-out gate

The 128 held-out records:

- contain two through five relation edges;
- use only the novel aliases, not the original vocabulary;
- use unseen entity names and irrelevant facts;
- vary alias choice, surface template, and fact order.

An exact raw-text memorizer is the baseline. A second run renames all eight aliases before training and evaluation.

## Negative controls

- evidence compatible with more than one latent code must be rejected;
- contradictory duplicate evidence must be rejected;
- an unregistered expression at inference must abstain rather than receive a default meaning;
- learner functions are audited not to reference the hidden alias-group generator.

## Claim boundary

Passing demonstrates usage-based lexical grounding into an existing, tiny semantic ontology. It does not invent a fifth relation, discover meanings from natural documents without answer supervision, understand unrestricted Japanese, or approach Japanese high-school intelligence by itself.

## Next capability

`CAP-SEM-004` must allocate a genuinely new relation pair rather than mapping a new word into one of the four existing classes. The runtime must grow from data without adding a relation-specific solver branch.
