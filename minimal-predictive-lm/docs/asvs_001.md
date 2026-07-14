# CAP-GEN-002-ASVS-001: anytime-safe symmetry version space

## Research question

IAS-001 used exact auxiliary tables. Real interaction data are finite, noisy, adaptively collected, and inspected repeatedly. A plug-in estimate can therefore delete a true symmetry by chance and report grounding certainty that the evidence does not support.

The question is not how to add another auxiliary channel. It is what object should represent residual grounding ambiguity when every symmetry decision is uncertain.

## Prior-art boundary

Active sequential hypothesis testing, safe tests and e-values, confidence sequences, sequential familywise error control, finite-sample group-symmetry tests, automorphism groups, subgroup enumeration, stabilizers, and group bases are prior art. Relevant primary references include arXiv:1203.4626, arXiv:1906.07801, arXiv:1307.7667, arXiv:2307.15834, and arXiv:2412.14391.

ASVS-001 does not claim a new statistical-testing or group-theoretic theorem.

## Why elementwise non-rejection is wrong

Let `G` be the ambient automorphism group. At time `t`, let

```text
C_t = {g in G : g has not been rejected by time t}.
```

Even with valid individual tests, `C_t` need not be a group. It may contain `g` while excluding `g^2`, or contain `g` and `h` while excluding `gh`. Therefore `|C_t|` is not the number of possible grounded worlds, and a group-base calculation cannot be applied directly to `C_t`.

## Anytime certificate

Each Bernoulli channel-action stream receives an all-times Hoeffding interval. At sample count `n`, its error budget is

```text
delta / (M * n * (n + 1)),
```

where `M` is the number of streams. Since the sum of `1/(n(n+1))` over positive `n` is one, the simultaneous probability that any stream misses its true mean at any inspected sample size is at most `delta`.

A permutation is rejected only when at least one mapped pair has disjoint intervals. Under the stated conditional Bernoulli and non-anticipating sampling assumptions,

```text
Pr(true symmetry group H is contained in C_t for every t) >= 1 - delta.
```

The construction is intentionally conservative. Its purpose is to establish the correct logical object before optimizing power.

## Subgroup version space

Define

```text
V_t = {K <= G : K is a subgroup and K is contained in C_t}.
```

On the simultaneous confidence event, the true symmetry group belongs to `V_t` at every time.

### Logical pruning

Let `L_t` be the union of all subgroups in `V_t`. Every true symmetry remains in `L_t`, but an individually non-rejected element is removed when no complete subgroup containing it remains possible.

The finite gate retains the identity and a quarter rotation of a square while rejecting the square of that rotation. Elementwise reasoning retains two transformations. Subgroup reasoning retains only the identity because a quarter rotation cannot be a symmetry unless all of its powers are symmetries.

### Robust grounding base

The direct-grounding problem is

```text
minimize |B|
subject to K_(B) = {identity} for every K in V_t.
```

A second counterexample leaves two incompatible worlds plausible: the square's rotation subgroup and one reflection subgroup. One carefully selected action grounds either world, so the version-space robust base has size one. Generating a single group from their union recreates the full dihedral group, whose base size is two. A single generated envelope therefore overcharges grounding.

The project-specific insight is that a confidence-safe set of plausible subgroups can be sharper than both raw elementwise non-rejection and one group generated from every remaining element. Equivalent prior formulations may exist; publication-level novelty is not claimed.

## Experiment-selection counterexample

Counting rejected elements can choose the worse experiment.

- Experiment A rejects six of eight elements but leaves one complete reflection subgroup, so one direct grounding action remains.
- Experiment B rejects only five elements, but its retained elements cannot form any nontrivial subgroup, so no direct grounding remains.

Experiment utility must therefore depend on version-space reduction and complete lifetime resource, not raw rejected-element count.

## Frozen gate

The controlled gate uses an eight-action cycle and two stable binary markers with `delta=0.05`.

- At 16 samples per stream, all 16 dihedral symmetries remain and two grounding anchors are still required.
- At 32 samples per stream, only the identity remains.
- When all channel means are equal, the full group remains and no false grounding is reported.
- The allocated all-times error budget through 100,000 samples remains below `delta`.

These are fixture-specific numbers, not a general sample-complexity theorem.

## Stagnation guard

The next step must not add markers, graph sizes, or another deterministic example. It must address a sharper anytime-valid process under adaptive experiment selection, an information lower bound and stopping rule, unknown raw event/environment boundaries, learned auxiliary-test grammar, or natural/public interaction data.

Merely replacing Hoeffding with another interval without changing theory, resource separation, or real-data reach is not research progress.
