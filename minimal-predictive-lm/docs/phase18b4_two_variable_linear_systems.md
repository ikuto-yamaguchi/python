# Phase 18b-4: Two-variable linear systems from controlled Japanese

## Question

Phase 18b-3 constructs and solves one-variable affine equations. Phase 18b-4 asks whether two unknowns and two independent relations can be compiled from one Japanese text into an exact linear system, solved over rational numbers, and independently verified.

## Representation

Each relation sentence is reduced to one row

```text
a*x + b*y = c
```

The surface relation words `合わせる` and `引く` are not assigned ADD/SUB meanings in the learned model. Their mapping is selected from both permutations using calibration problems with known answers. Degenerate calibration rows with zero second coefficients are retained as a non-identifiability control.

For two rows, the solver computes

```text
D  = a1*b2 - a2*b1
Dx = c1*b2 - c2*b1
Dy = a1*c2 - a2*c1
x = Dx / D
y = Dy / D
```

All values are exact `Fraction` objects. The verifier recomputes the determinant and numerators, checks both substitutions, and rejects altered proof fields even when the final answer is unchanged.

## Frozen evaluation

- 3 calibration problems identify the relation semantics.
- 12 held-out problems use unseen coefficients, equation combinations, query orders, negative values, and rational solutions.
- Singular, inconsistent, and one-equation inputs must abstain.
- A zero-coefficient calibration demonstrates that relation semantics cannot be recovered without informative interventions.

## Claim boundary

This is exact two-variable linear-system solving in a controlled Japanese coefficient language. Coefficients and unknown names are explicit, exactly two equations are required, and variable selection is not autonomous. It is not ordinary word-problem understanding, general algebra, or Japanese high-school-level mathematics.
