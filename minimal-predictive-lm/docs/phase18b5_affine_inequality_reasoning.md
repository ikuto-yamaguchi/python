# Phase 18b-5: Affine inequalities and exact interval reasoning

## Question

Phase 18b-5 asks whether four Japanese comparison expressions can be grounded from interval supervision and then reused to solve unseen affine inequalities, including negative coefficients, strictness, multiple-constraint intersection, point intervals, half-lines, and the empty set.

## Induction

The surface forms `以上`, `以下`, `より大きい`, and `より小さい` are assigned to `GE`, `LE`, `GT`, and `LT` by searching all 24 permutations. Calibration intervals include boundary points; without boundary observations, `GE` versus `GT` and `LE` versus `LT` are observationally indistinguishable.

Each constraint

```text
a*x + b OP c
```

is normalized at exact rational threshold `(c-b)/a`. When `a < 0`, the comparison direction is reversed. When `a = 0`, the constraint is classified as always true or impossible. Intersections retain open/closed endpoints and distinguish a singleton interval from the empty set.

## Verification

The proof records each original constraint, normalized threshold, normalized comparison, and zero-coefficient status. An independent verifier recomputes every normalization and the full interval intersection. Altered endpoints are rejected.

## Frozen evaluation

The held-out suite contains negative coefficients, negative and fractional thresholds, open and closed bounds, a singleton, an empty intersection, a half-line, and a redundant always-true constraint. Unknown comparison vocabulary must abstain.

## Claim boundary

This is controlled one-variable affine inequality reasoning over exact rationals. It does not include ordinary prose, autonomous variable choice, absolute values, nonlinear inequalities, integer domains, optimization, or general Japanese high-school mathematics.
