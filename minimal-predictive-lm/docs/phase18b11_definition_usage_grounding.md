# Phase 18b-11: definition, contrast, and usage grounding

## Question

Can completely novel relation tokens be grounded without sharing characters with the Phase 18b-10 anchors?

## Controlled evidence

Six nonce tokens are assigned to COUNT, RATE, and VALUE. A fixed definition metalanguage supplies:

- one direct concept definition,
- three same-meaning links,
- one different-meaning link,
- two negated concept links.

These statements intentionally leave RATE and VALUE exchangeable. The learner then evaluates correct-answer usage examples with the shared Phase 18b-7 solver and Phase 18b-9 raw sentence parser.

The hypothesis space is all `3^6` token-role assignments times three count programs and four value programs: 8,748 hypotheses. Definitions and contrasts leave 24 hypotheses. Usage examples must leave exactly one.

## Held-out gate

Held-out problems use only alias tokens that never appear in the usage examples, change domains, values, sentence order, target order, and question forms, and contain none of the Phase 18b-10 anchors.

## Failure boundaries

- definitions without usage remain ambiguous,
- unanchored synonym cycles remain ambiguous,
- contradictory positive and negative definitions have no model,
- unknown tokens and cues containing multiple grounded tokens abstain,
- counterfactual RATE/VALUE swapping fails,
- altered proof output is rejected.

## Claim boundary

This is controlled grounding from a fixed definition language plus demonstrations. It is not open dictionary learning, unrestricted Japanese definition understanding, morphology discovery, polysemy resolution, or high-school intelligence.
