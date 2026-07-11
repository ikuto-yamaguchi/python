# Phase 11b results: reusable macro library induction

The learner alpha-normalizes repeated program subtrees across distinct tasks.
A subtree observed in only one program is not admitted to the library.

## Library induction

- source programs: **2**
- macros discovered: **1**
- macro support: **2 distinct programs**
- macro body: `["SUB", ["ARG", 0], ["ADD", ["ARG", 1], ["ARG", 2]]]`
- macro storage: **984 bits**

## New target

- primitive-only search failed at **20,000 candidates**: **True**
- library search candidates: **3,275**
- library search depth: **1**
- macro calls in compact program: **1**
- training accuracy: **100.0%**
- held-out accuracy: **100.0%**

## Lifetime adoption

- compact program: **488 bits**
- expanded program: **504 bits**
- search evaluations saved: **16,725**
- normalized lifetime gain: **15,757 bits**
- adopted: **True**

## Verdict

- Phase 11b success: **True**

The macro does not add a domain-specific solver.  It shortens future search by
reusing a verified causal computation learned in other tasks.  This is still a
bounded library mechanism, not open-ended representation invention.

## Limitations

- macro candidates come from already induced and verified programs rather than raw language
- only argument-parametric expression subtrees are abstracted; stateful and recursive macros are excluded
- the normalized lifetime objective assigns one bit to one candidate evaluation for this experiment
- macro argument instantiation is still enumerative and can grow with arity
- library dispatch, versioning, forgetting, and conflicting macro semantics remain incomplete
- the task is synthetic and does not establish broad language-model scalability
