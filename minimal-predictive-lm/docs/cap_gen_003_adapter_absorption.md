# CAP-GEN-003-AAF-001: adapter absorption and operational reuse

## Purpose audit

The research goal is a tiny learner that acquires broadly reusable intelligence from mixed experience. COT-001 moved from local action-identifiability theory to cross-domain reuse. The next danger is to declare success merely because a small shared core and large domain adapters fit every training transition.

AAF-001 is therefore an anti-shortcut gate. It asks whether knowledge actually transfers to a held-out domain with fewer stored transition facts and fewer grounded interactions, without reading future successors.

## Prior-art boundary

The following are established and are not claimed as new:

- MDP homomorphisms and action-equivariant latent dynamics, including commuting transition diagrams;
- impossibility of unsupervised disentanglement without inductive bias (Locatello et al., arXiv:1811.12359);
- counterexamples for domain-invariant representation learning under conditional shift (Zhao et al., arXiv:1901.09453);
- representation collapse and anti-collapse objectives in self-supervised learning;
- memorization failure modes in meta-learning (Yin et al., arXiv:1912.03820);
- minimum-description-length and universal-interpreter accounting.

AAF-001 is a project-specific theorem gate and resource accounting rule, not a publication-level novelty claim.

## Adapter absorption theorem

Consider any finite collection of deterministic one-action domains with transition tables `T_d`.

An unrestricted factorization can use:

```text
shared core U(adapter, state) = adapter[state]
domain adapter A_d = complete table T_d
```

Then for every domain and state:

```text
U(A_d, state) = T_d(state)
```

The shared core is constant size and the commutation/execution error is zero, even when the domains have unrelated dynamics. Therefore:

> zero training loss plus a small shared core does not establish shared operational knowledge.

The transition information has merely moved into the adapters.

## Complete accounting corollary

For three frozen arbitrary domains containing 18 transitions:

- separate tables: 18 entries;
- reported shared core: 1 entry;
- domain adapters: 18 entries.

Counting only the core produces an apparent reduction of:

```text
18 / 1 = 18x
```

Charging core and adapters gives:

```text
18 / (1 + 18) = 0.947...
```

The supposedly shared representation is larger than the separate tables.

This is not an argument against adapters. It is an argument that adapter data, adapter induction, grounding, inference, memory, and support must never be omitted from the lifetime resource vector.

## Held-out non-identifiability

Two held-out worlds can expose the same state set and the same one grounded transition while disagreeing on every other successor.

In the frozen construction:

- state count: 8;
- common grounded evidence: 1 transition;
- transitions guaranteed across both worlds: 1 of 8.

Without a certified reusable structural restriction, no learner can guarantee all unobserved successors from this evidence. A model that does so has either:

1. imported a real reusable prior;
2. consumed additional interactions;
3. leaked future active successors;
4. guessed.

## Operational reuse certificate

For a held-out domain of `n` transition facts, AAF-001 certifies operational reuse only if all conditions hold:

1. prospective held-out exact accuracy is 1;
2. no unobserved future active successor was used by the adapter;
3. held-out adapter storage is less than `n`;
4. held-out grounded interactions are fewer than `n`.

The gate intentionally rejects three misleading cases.

### Lawful partial lookup

One grounded transition is stored and no future data leaks.

- accuracy: 1/8;
- storage saving: 7;
- interaction saving: 7;
- certificate: rejected because it does not predict the unseen transitions.

### Future-leaking lookup

One interaction is reported, but all eight successors are inserted into the adapter.

- accuracy: 8/8;
- leaked future successors: 7;
- certificate: rejected.

### Fully grounded lookup

All eight transitions are directly acquired and stored.

- accuracy: 8/8;
- storage saving: 0;
- interaction saving: 0;
- certificate: rejected because this is a separate table, not transfer.

## Positive control

The previous COT-001 shared cycle operator is re-evaluated by the new gate rather than accepted by construction.

On the frozen nine-state held-out domain:

- prospective accuracy: 9/9;
- held-out adapter entries: 1;
- grounded interactions: 1;
- future-successor leakage: 0;
- storage saving: 8;
- interaction saving: 8;
- certificate: accepted.

This does not make the cycle example evidence of general intelligence. It only shows that the new gate separates genuine finite reuse from lookup absorption.

## Research direction changed

AAF-001 removes a broad class of fake progress:

- tiny shared cores backed by full domain tables;
- training-only MDL claims that omit adapter payloads;
- perfect held-out scores obtained from leaked successors;
- full relearning renamed as adaptation.

The next learner must earn transfer prospectively.

## New hypothesis candidate

The unverified candidate is a raw mixed-stream learner that jointly discovers event boundaries, domain contexts, adapters, and shared executable operators while optimizing:

```text
K(shared operators)
+ K(adapters)
+ C(induction)
+ C(grounding)
+ C(inference)
+ M(peak)
+ D(identifying support)
+ prospective error/risk
```

A shared operator may enter the library only when it produces positive held-out operational reuse surplus across more than one structural family or capability axis.

## Stagnation guard

The next step must not add more arbitrary transition tables or cycle sizes. It must do at least one of:

- infer an operator and adapter from a mixed stream without supplied domain labels;
- demonstrate transfer on a public or natural interaction trace;
- reuse one learned executable component across two different CAP-GEN capability axes;
- derive a search rule whose advantage survives complete lifetime accounting.

Another finite lookup counterexample alone is not research progress.
