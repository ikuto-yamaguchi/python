# Phase 18b-6: Generic two-category unit-rate word problems

## Question

Earlier Phase 18b experiments expose coefficients or symbolic operations directly. Phase 18b-6 asks whether one fixed, domain-neutral compiler can read a short Japanese paragraph containing two categories, their total count, two per-unit values, and one total attribute, then construct and verify the corresponding two-variable system.

## Compiler

The compiler extracts four clause roles:

1. category names, total count, and count unit;
2. each category's per-unit attribute;
3. the total attribute and attribute unit;
4. the requested category counts.

It constructs

```text
x + y = N
p*x + q*y = S
```

and solves exactly. Counts must be nonnegative integers. The verifier checks extracted rows, determinant terms, both substitutions, entity names, and units.

## Frozen evaluation

Twelve held-out problems cover six unseen domains: tickets and prices, animals and legs, colored objects and mass, stationery and cost, vehicles and wheels, and correct/incorrect answers with positive/negative scores. Clause order, two count paraphrases, query order, and harmless nonnumeric distractors vary.

The following must abstain:

- equal per-unit values, which do not identify category counts;
- fractional or negative count solutions;
- mismatched units;
- an additional unparsed numeric fact.

Changing only the total attribute must change the inferred counts, and proof-field tampering must be rejected.

## Resource and claim boundary

This campaign deliberately uses a fixed clause grammar. Acquired payload is therefore zero bits; source bytes and the Python runtime are separate costs and must not be hidden. The result is cross-domain recombination inside one controlled schema, not parser induction, open-domain word-problem understanding, or high-school intelligence.
