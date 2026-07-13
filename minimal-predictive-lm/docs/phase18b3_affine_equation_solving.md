# Phase 18b-3: Symbolic affine equation solving

## Question

Phase 18b-2 executes an exposed recursive arithmetic program from fully known
initial values. Phase 18b-3 removes one initial value, supplies a final
observation, and asks whether the machine can construct and solve the implied
one-variable affine equation exactly.

This is an intermediate algebra gate. It is not a claim of natural Japanese
word-problem understanding or high-school mathematics.

## Problem representation

Each problem contains four top-level semantic blocks:

```text
開始値【アキ=?、ボブ=2、チカ=3、ダイ=4、エリ=5、フミ=6】。
実行した操作【続いて【アキを5だけ増やす】【アキを3だけ倍にする】】。
最後の観測【アキ=24】。
求める初期値【アキ】。
```

The surrounding labels vary and are not prelisted. Block roles are recognized
from their contents:

- a complete entity assignment containing exactly one `?`;
- one recursive Phase 18b-2 arithmetic program;
- one observed final entity value;
- one queried entity.

The queried entity must be the unique unknown.

## Symbolic execution

Every entity value is represented as an affine expression:

```text
a*x + b
```

The unknown starts as `(1, 0)` and known values start as `(0, value)`.
Induced arithmetic operations transform the coefficients:

```text
ADD k: (a, b) -> (a, b+k)
SUB k: (a, b) -> (a, b-k)
MUL k: (a, b) -> (k*a, k*b)
```

Sequence, reverse sequence, conditions on known quantities, and suppressed
subtrees are handled recursively. If a condition genuinely depends on the
unknown value, the machine abstains rather than selecting a branch without a
case analysis.

For an observed final value `y`, the machine constructs:

```text
a*x + b = y
```

and solves exactly over rational numbers:

```text
x = (y-b)/a
```

The candidate is then replayed numerically through the original arithmetic
program. A solution that fails the final observation is rejected.

## Frozen evaluation

The evaluation contains six unseen recursive equation structures under two
contexts each, for 12 equations total. It includes:

- negative solutions;
- non-integer rational solutions;
- reversed execution order;
- nested operation sequences;
- known-value condition branches;
- suppressed subtrees;
- changed numerical constants and observations.

Calibration problem strings and held-out problem strings do not overlap.

## Verified symbolic derivation

Trace steps record:

- affine coefficient and offset before each operation;
- affine coefficient and offset after each operation;
- recursive execution order;
- condition expressions and selected branch;
- subtree suppression;
- the final equation coefficients, observation, and exact solution.

The verifier reconstructs symbolic execution from the original problem and
compares every trace step before numerically replaying the solved value.
Empty traces, modified affine offsets, and wrong solutions are rejected.

## Falsification and abstention gates

The campaign fails unless:

1. all 12 exact rational solutions are correct;
2. all derivations are independently verified;
3. both negative and fractional solutions occur;
4. whole-problem memorization has zero coverage;
5. returning the observed final value as the unknown scores below 50%;
6. changing the observation changes every corresponding solution;
7. empty, tampered, and wrong-solution traces are rejected;
8. coefficient-zero equations with no unique solution are rejected;
9. problems with two unknowns are rejected;
10. conditions depending on the unknown are rejected;
11. a query for a different entity is rejected.

## Resource accounting

The learned payload includes inherited operation/control semantics plus the
compact affine representation and solve schema. Python, the fixed parser,
`Fraction` implementation, and verifier source are excluded from learned
payload and reported separately.

## Claim boundary

Passing Phase 18b-3 demonstrates exact construction and solution of
one-variable affine equations in a bracketed controlled language. It does not
establish:

- equation extraction from ordinary prose;
- simultaneous equations;
- inequalities or unknown-dependent piecewise cases;
- polynomials, powers, roots, or functions;
- geometry, probability, statistics, or proof;
- Japanese high-school-level mathematics or intelligence.

The next gate should remove the exposed calculation tree by learning several
natural-language relation paraphrases and mapping them to equations, with
held-out paraphrase and relation-composition splits.
