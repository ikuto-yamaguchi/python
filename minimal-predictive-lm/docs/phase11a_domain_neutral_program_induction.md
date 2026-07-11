# Phase 11a: domain-neutral program induction and the real scalability criterion

## The concern

A system that needs a new handwritten parser, solver, reward rule, or workflow for every domain is not a scalable alternative to a general language model. It may minimize runtime after an engineer has compiled the domain, while hiding an engineering cost that grows with the number of domains.

Therefore the optimization objective must include human and machine induction costs, not only inference:

\[
J = L_{task} + B_{engine} + B_{learned} + C_{grounding} + C_{search}
    + C_{verification} + C_{migration} + C_{runtime} + C_{human}.
\]

A new domain is scalable only when it can be added primarily through observations or interaction traces, rather than by editing the inference engine.

## Fixed learner, learned program

Phase 11a replaces several task handlers with one bounded typed synthesizer:

\[
p_D^* = \arg\min_{p \in \mathcal{G}}
\left[
L(p) + L(D\mid p) + C_{search}(p) + C_{run}(p)
\right].
\]

The learner receives:

- typed arguments,
- sparse state before an action,
- sparse state after the action,
- an observed output.

It is not given a domain name such as mathematics, conversation, inventory, or tool use. The same primitive grammar is used for every task:

- argument and constant access,
- state read,
- addition, subtraction, multiplication, division,
- string concatenation,
- conditional choice,
- sparse state update.

Programs are selected by held-out consistency and description length. Expressions with the same observational signature are merged so the learner does not retain multiple programs that make identical predictions on the available evidence.

## The correct scalability measurements

Accuracy alone is insufficient. Every new-domain experiment must report:

1. human engine-code changes,
2. new primitive count,
3. grounding or interaction examples,
4. learned-program bits,
5. candidate evaluations and verification calls,
6. held-out and shifted accuracy,
7. cross-domain primitive or macro reuse,
8. the fraction of tasks outside the representation grammar.

If code changes or primitive count grow approximately linearly with domain count, the architecture has merely moved a collection of applications into one repository.

## Why domain cost cannot be exactly zero

No learner can identify an arbitrary new task without information that distinguishes it from alternatives. Domain information must enter through at least one of:

- demonstrations,
- interaction outcomes,
- rewards or preferences,
- tool schemas,
- grounded language,
- perception,
- prior reusable concepts.

This is an identification cost, not an implementation accident. The goal is to encode domain information once in the smallest reusable representation, not to pretend that the information is unnecessary.

## Engineering cost can become search cost

A universal synthesizer does not automatically solve scalability. Searching all programs up to depth \(d\) can grow exponentially. Phase 11a therefore uses:

- type-directed candidate generation,
- observational-equivalence pruning,
- target-type gating for conditionals,
- bounded typed chain composition,
- explicit candidate budgets.

The remaining search-budget failures are retained as evidence. Raising the budget until a small example passes would hide the same cost explosion that this phase is intended to measure.

## Why a fixed DSL is still insufficient

A fixed grammar can learn many domains without new handlers, but it is not open-ended. Two distinct failures remain:

1. **Missing primitive**: the desired transformation cannot be expressed at all.
2. **Composition depth**: the desired program is expressible but too expensive to rediscover from primitive operations.

The first requires representation or primitive invention. The second requires library induction: successful subprograms must become reusable macros when their future savings exceed storage, dispatch, migration, and verification costs.

For a candidate macro \(m\), retain it only when

\[
\mathbb{E}[C_{future}^{without\ m} - C_{future}^{with\ m}]
>
B(m) + C_{discover}(m) + C_{verify}(m) + C_{migrate}(m).
\]

## Next phases

### Phase 11b: automatic library induction

- find repeated subtrees and repeated residual transformations,
- abstract varying leaves into typed parameters,
- add the macro only when lifetime MDL improves,
- compare search candidates before and after the library is available,
- delete macros that stop paying for themselves.

The immediate target is to learn a reusable `remaining(a,b,c) = a-b-c` macro and use it to reduce `(a-b-c)*d` from a depth-three search to a short macro composition.

### Phase 11c: representation and primitive invention

- detect residuals that no current program can express,
- propose the smallest new primitive or state distinction,
- require improvement on held-out tasks across more than one domain,
- maintain rollback and deletion evidence,
- charge discovery and migration costs to the lifetime objective.

### Phase 11d: remove structured-trace assumptions

- infer task boundaries,
- ground raw language, code, tool output, and perception into the shared trace format,
- use uncertainty and Value of Information when grounding is ambiguous.

## Honest conclusion

Phase 11a can remove per-domain handwritten algorithms for tasks inside a shared grammar. It does not make learning free, does not solve raw-language grounding, and does not yet provide open-ended representation invention. The research criterion is now explicit: a capability is not considered scalable merely because its runtime is small; it must also have low incremental human code cost, low induction cost, and reusable learned structure.
