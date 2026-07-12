# Phase 17g: Joint token-role and semantic grounding

## Removed shortcut

Phase 17e and Phase 17f knew which surface tokens were entities because those token
strings also appeared as world-state keys. Phase 17g removes that shortcut.

The learner sees:

- a variable-length raw token sequence;
- an anonymous numeric state vector before the event;
- the anonymous state vector after the event.

Surface entity names never equal coordinate names. No token is labeled as entity,
action, modifier, or distractor.

## Finite grounding hypothesis class

For every observation, the before/after intervention identifies one changed
destination coordinate and, when values are distinct, one source coordinate whose
value was copied.

For a token `w`, define its occurrence signature across observations as

```text
s_w[i] = 1 iff w occurs in observation i.
```

For anonymous coordinate `q`, define its causal participation signature as

```text
c_q[i] = 1 iff q is the source or destination in observation i.
```

A token may ground coordinate `q` only when

```text
s_w = c_q.
```

The learner enumerates injective token-to-coordinate matchings satisfying this
constraint. This is a strong exact-signature assumption, but it makes ambiguity
explicit and countable.

## Joint action and template induction

After a candidate entity grounding is selected, the learner enumerates recurrent
remaining token subsets. An accepted action lexicon must contribute exactly one
action token to every training event. The order of the two grounded entity tokens
and the action token defines a three-slot semantic subsequence; all other raw tokens
are treated as nuisance tokens only after the hypothesis survives the world
transition evidence.

The Phase 17f XOR graph learner then induces reusable action and template direction
bits. The action-template graph must be connected. A disconnected graph is rejected
rather than completed with arbitrary cross-component semantics.

## Identifiability criterion

Within the declared finite hypothesis class, the joint model is unique when:

1. every anonymous coordinate has one unique, uncontaminated token occurrence
   signature;
2. no recurrent distractor shares a coordinate participation signature;
3. exactly one recurrent action lexicon explains every transition;
4. the resulting action-template graph is connected and cycle-consistent.

These are sufficient conditions for this controlled environment, not a theorem for
unrestricted language.

## Negative controls

The campaign preserves three failures:

- duplicate entity signatures leave multiple token-coordinate matchings;
- a distractor deliberately given an entity's signature leaves multiple matchings;
- a disconnected action-template graph produces no accepted total semantic model.

More search or a larger model cannot resolve these cases without additional
information. They are retained as non-identifiability results.

## Evaluation

The held-out suite uses:

- unseen action-template combinations;
- entity-role reversal pairs;
- new distractor words;
- raw sentence lengths different from training examples;
- identical positionless token multisets within each reversal pair.

A classifier receiving only the token multiset and before-state has an exact 50%
upper bound. An exact sentence memorizer has zero coverage. The induced model must
achieve 100% accuracy and coverage while retaining the ambiguity controls.

## Accounting

Report separately:

- serialized acquired lexicon and factorization bits;
- Phase 17g implementation source bytes;
- excluded Python runtime and standard-library substrate.

The acquired payload must never be presented as total system size.

## Remaining biases

- interventions are noiseless;
- state values are distinct and reveal a unique copied source;
- state-vector dimensionality is given;
- each sentence contains exactly one binary copy event;
- exact occurrence signatures are used instead of statistical estimates;
- polysemy, synonymy, negation, recursion, discourse, and continuous perception are
  absent.

## Next gate

The next semantic-grounding campaign must replace exact signatures with a noisy
probabilistic estimator and establish finite-sample recovery bounds. It must also
allow optional arguments, multiple operations, and Japanese paraphrases before any
claim of natural-language understanding.
