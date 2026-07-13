# Phase 18c-1: dimension-checked multiplicative relation core

## Goal

Move beyond linear equalities by introducing one reusable exact product graph for three school-math relation families:

- distance = speed × time,
- solute mass = concentration × solution mass,
- total price = quantity × unit price.

## Induction

Each relation presents three ordered slots. The learner searches which slot is the product of the other two. Three relations produce `3^3 = 27` orientation hypotheses. Six exact rational examples must leave one orientation model.

## Runtime

The graph stores equations of the form `product = factor_left × factor_right` and dimension vectors. With exactly two quantities known, the third is derived by multiplication or exact division. A work-list propagates through chained equations, while a replay verifier independently reconstructs the result and proof steps.

## Gates

- all three unknown positions across speed, concentration, and price,
- fractions and negative dimension exponents,
- two-equation chained reasoning,
- constraint-order invariance,
- ambiguous and inconsistent orientation examples,
- dimension mismatch,
- two-unknown underdetermination,
- division by zero,
- contradictory known quantities,
- proof tampering.

## Claim boundary

This is a new controlled multiplicative family beyond the Phase 18b linear core. It is not a general nonlinear solver. Inputs are structured, dimensions are supplied, and raw Japanese compilation is deferred.
