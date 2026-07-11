# Phase 11b: reusable macro library induction

## Motivation

Phase 11a replaced per-domain handwritten solvers with one bounded typed program
synthesizer.  That removed some human engineering cost, but it exposed another
failure mode: a useful depth-three program could exhaust the search budget even
when all required primitives were already present.

Increasing the budget merely moves cost from human engineering to brute-force
induction.  Phase 11b therefore treats previously verified programs as data from
which a reusable typed library may be learned.

## Macro identity

A candidate subtree is alpha-normalized by replacing concrete argument indices
with parameters in first-occurrence order.  Two subtrees are considered the same
macro only when their normalized typed expression trees are identical.

For example, programs that independently induce

```text
x - (y + z)
```

with different concrete argument positions produce the same normalized body:

```text
SUB(ARG0, ADD(ARG1, ARG2))
```

A candidate must occur in at least two distinct verified programs.  Multiple
occurrences in one program do not count as independent support.  This blocks the
most direct path from the library becoming a cache of one-off solutions.

Phase 11b abstracts only argument-parametric expressions.  Subtrees containing
exact state keys are rejected because retaining them would silently recreate
per-domain handlers.

## Search with a library

A macro call is treated as one search-level atom while retaining an expanded
primitive expression for execution and verification.  Search therefore operates
on a compact representation such as

```text
MUL(CALL(M0, ARG0, ARG1, ARG2), ARG3)
```

while the verifier executes the fully expanded expression.

Macro parameters are bound only to dynamic `ARG` or `STATE` atoms.  Constants
observed in training outputs are not enumerated as call arguments.  Without this
restriction, an arity-k macro would generate approximately

```text
(number of arguments + number of observed constants)^k
```

bindings and the library itself would create a new combinatorial explosion.

## Lifetime adoption objective

A discovered candidate is not automatically permanent.  In the experiment the
normalized decision is

```text
gain = expected call-site serialization savings
     + avoided candidate evaluations * cost per evaluation
     - macro storage bits
```

and the macro is admitted only after held-out verification and positive gain.
The current experiment uses one bit as the explicit normalized price of one
candidate evaluation.  This coefficient is a declared accounting choice, not a
physical equivalence between memory and CPU energy.

A production objective must separately price:

- discovery computation;
- macro storage and index cost;
- dispatch and expansion cost;
- verification and regression testing;
- migration of existing programs;
- invalidation under distribution change;
- rollback and forgetting;
- future search reduction.

## Experiment

Two independently induced tasks share the same three-argument remaining-value
program.  Their held-out accuracy is 100%, and the repeated normalized subtree is
admitted as one macro.  A third task requires the deeper composition

```text
remaining(a, b, c) * d
```

Primitive-only search exhausts a 20,000-candidate budget.  With the learned macro,
the target is found at search depth one after 3,275 candidate evaluations and
achieves 100% training and held-out accuracy.

The macro occupies 984 bits.  The compact call site is 488 bits versus 504 bits
for the expanded expression.  Serialization alone would need 62 calls to repay
the macro, but the measured search reduction makes the normalized lifetime gain
positive immediately in this experiment.

## What this establishes

The result shows that a shared learner can convert repeated verified computation
into a reusable abstraction and use it to solve a task that was unreachable under
the previous bounded search.  No revenue-specific or inventory-specific solver is
added.

It does not establish open-ended intelligence.  The system still receives
structured traces, fixed task boundaries, and a fixed primitive grammar.  Macro
argument binding is enumerative, recursive and stateful abstractions are absent,
and semantic conflicts between macros are not yet handled.

## Next step: Phase 11c

Phase 11c must address representation failure rather than search depth.  When no
program in the current grammar explains a persistent residual, the learner should
propose the smallest new primitive or state distinction, validate it across
multiple tasks, and retain it only when its lifetime utility exceeds its
implementation, verification, storage, and migration cost.

The `uppercase(text)` failure from Phase 11a is the first controlled target.  A
credible solution may not simply add a hardcoded `UPPERCASE` primitive because a
researcher noticed the failure.  The primitive proposal must be derived from an
external operation or executable candidate generator, tested on held-out inputs,
and rejected if it fails to transfer beyond the originating task.
