# Phase 17e: Compositional lexical-template identifiability

## Relaxed assumption

Phase 17d proves identifiability only when the action word is always in the middle
position. Phase 17e removes that fixed-position assumption. The action may occur in
position 0, 1, or 2 of a three-token sentence.

The learner is still given a strong but explicit grounding signal: entity symbols
are the tokens that appear as keys in the observed world state, so the remaining
token is the action. This campaign therefore studies factorization of lexical
meaning and template orientation, not unrestricted part-of-speech induction.

## Factorized model

Let

- `v_i` be one unknown direction bit for verb `i`;
- `t_j` be one unknown argument-orientation bit for template position `j`.

For a sentence using verb `i` and template `j`, the effective surface direction is

```text
v_i XOR t_j
```

The observation of an asymmetric before/after transition reveals exactly this XOR.
The training data therefore defines a bipartite graph:

```text
verb nodes <-> template nodes
```

with one labeled edge for each informative observed verb-template pair.

## Identifiability theorem

The semantic behavior over every possible verb-template pair is identifiable,
modulo one global latent-coordinate flip, if and only if the bipartite observation
graph is connected.

### Necessity

If the graph has `c > 1` connected components, all bits in any one component may be
flipped without affecting its observed edges. After quotienting out the one global
flip that changes no behavior anywhere, `c - 1` independent relative component
flips remain. They change predictions on unobserved cross-component pairs.

Therefore the number of surviving semantic behavior classes is

```text
2^(c - 1)
```

and meaning is not identifiable.

### Sufficiency

Choose one latent bit as a reference. In a connected graph, the XOR label on every
edge propagates the value of all other verb and template bits along graph paths.
Only the simultaneous global flip remains, and that flip preserves every effective
verb-template direction. Hence one semantic behavior class remains.

## Minimum evidence

With `V` verbs and `T` templates there are `V + T` binary parameters and one global
gauge dimension. The semantic behavior class therefore contains

```text
V + T - 1
```

independent bits.

A connected graph on `V + T` nodes requires at least `V + T - 1` edges. A spanning
tree reaches both the graph-theoretic and information-theoretic lower bounds.

For Phase 17e:

```text
V = 4
T = 3
minimum informative observations = 6
```

The identifying training campaign uses exactly six verb-template examples forming a
spanning tree.

## Negative control

The negative campaign observes every verb and every template at least once, but the
observation graph has two connected components. This matters: merely covering all
symbols is insufficient. Relative orientation between the components remains
unconstrained, so two semantic behavior classes survive.

This is an impossibility result. Additional search, parameters, or optimization
cannot determine which cross-component behavior is correct without a connecting
observation or another justified source of supervision.

## Unseen composition evaluation

The held-out set contains every verb-template pair not present in the spanning-tree
training set. It also uses unseen entity names and role-reversal pairs.

The evaluation checks:

1. transfer to unseen verb-template compositions;
2. an exact 50% upper bound for classifiers receiving only positionless unigrams
   and the complete before-state;
3. zero coverage for an exact sentence memorizer;
4. causal consistency when the learned latent source and destination are swapped.

A successful result is evidence for reusable lexical-template factorization in this
controlled world. It is not evidence for unrestricted natural-language syntax.

## Accounting

Phase 17e reports:

- the semantic information lower bound;
- serialized acquired-factorization bits;
- combined Phase 17d and Phase 17e source bytes;
- excluded Python runtime and standard-library substrate.

The acquired semantic bits must not be presented as total model size.

## Remaining human biases

- every sentence has exactly three tokens;
- exactly two tokens are known world entities;
- exactly one token is an action;
- meanings are binary copy operations;
- no modifiers, polysemy, nested clauses, discourse, or noisy observations exist.

## Next gate

The next meaningful relaxation is to remove entity-category supervision by state-key
membership and induce token roles jointly from repeated interventions. A valid
campaign should include:

- tokens that may be entities in one context and non-entities in another;
- distractor and modifier tokens;
- more than one latent operation per sentence;
- held-out operation order and template compositions;
- a formal characterization of remaining automorphisms;
- sequence-aware finite-state and neural baselines;
- full front-end and runtime resource accounting.

If the enlarged observation model is not identifiable, the failure must be retained
as a theorem or counterexample rather than hidden through handcrafted parsing.
