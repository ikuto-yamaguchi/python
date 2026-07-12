# Phase 17d: Interventional semantic identifiability

## Question

Phase 17b and 17c operate behind a human-designed parser. They therefore do not
show that raw language can be grounded into reusable meaning. Phase 17d asks a
smaller, mathematically decidable question:

> Can a learner recover ordered lexical semantics from raw symbol sequences and
> observed world transitions, and can we prove when recovery is impossible?

The experiment uses a three-token controlled micro-language rather than natural
language. It is intentionally tiny so the complete hypothesis class can be
enumerated and every identifiability claim can be checked exactly.

## Micro-world

A sentence has the surface form

```text
ENTITY VERB ENTITY
```

The world assigns one binary value to each entity. A latent semantic frame contains

```text
(source, destination)
```

and executes

```text
value[destination] <- value[source]
```

Each of four opaque verbs contributes one unknown direction bit. The learner sees
only the raw sentence, the complete state before the sentence, and the state after
execution.

The hypothesis class also contains a global swap of the two internal argument
coordinates. Swapping the coordinates and flipping every verb bit leaves all world
behavior unchanged. Hence raw parameters are not identifiable, but semantic
behavior may be identifiable modulo this gauge transformation.

## Negative theorem: symmetric observations cannot identify meaning

Let the two participants have the same value before execution. Copying left to right
or right to left then produces the same after-state. Therefore both meanings of the
observed verb are consistent.

With `V` independent verbs, symmetric observations leave

```text
2^V
```

distinct semantic behavior classes. No learner, regardless of compute or model
size, can recover the true directions from those observations alone. This is an
information-theoretic failure, not an optimization failure.

Phase 17d verifies the statement by exhaustive enumeration of all syntactic
hypotheses and grouping them by their predictions on the complete finite probe
universe.

## Positive theorem: one asymmetric intervention per verb is sufficient

For each verb, set the two participant values to different bits. The two possible
copy directions now produce different after-states, revealing that verb's one
independent semantic bit.

For `V` verbs:

- there are `2^V` semantic behavior classes before observations;
- at least `log2(2^V) = V` bits of evidence are required;
- one independent asymmetric intervention per verb supplies those `V` bits;
- after these interventions, one semantic behavior class remains;
- two syntactic parameterizations remain because of the global coordinate gauge.

Thus semantic behavior is identifiable up to an explicit isomorphism, and the
lower bound is achieved.

## Exact separation from a declared surface classifier

The held-out suite consists of adjacent role-reversal pairs. Each pair has:

- exactly the same unordered sentence tokens;
- exactly the same complete before-state;
- different correct after-states.

For the representation

```text
(sorted unigram multiset, complete before-state)
```

both examples in a pair are identical. Any deterministic classifier over that
representation must return the same target for both and can score at most 50% on a
balanced suite. The upper bound is computed exactly by majority target within each
representation-equivalence class.

The induced semantic interpreter is evaluated on unseen entity names and unseen
sentences. An exact sentence memorizer has zero coverage, while the semantic
interpreter can reuse the learned verb directions compositionally.

## Internal intervention test

For every held-out sentence, Phase 17d extracts the learned latent frame, swaps only
`source` and `destination`, and executes the intervened frame. The result must equal
the model's prediction for the corresponding surface role-reversed sentence.

This is stronger than probing whether role information is decodable: changing the
latent role variable must cause the predicted world transition to change in the
corresponding way.

## What passing proves

Passing all checks demonstrates, for this finite controlled language, that:

1. symmetric data is provably insufficient;
2. specified interventions make the semantic behavior identifiable;
3. the number of informative interventions reaches the information lower bound;
4. a positionless surface representation has an exact 50% ceiling;
5. exact sentence memorization does not cover the held-out inputs;
6. the learned representation supports causal latent-role interventions and
   systematic reuse across new entity names.

## What passing does not prove

It does not demonstrate unrestricted natural-language understanding. The following
inductive biases remain human-designed:

- sentences contain exactly three tokens;
- the verb is in the middle position;
- the world state exposes the entity symbols;
- meanings are binary copy directions;
- the verb vocabulary is fixed during the campaign.

A sufficiently general classifier can implement the same semantic algorithm, so it
is meaningless to prove that the system is not a classifier in the broad
function-approximation sense. The valid claim is narrower: it cannot be reduced to
the declared positionless surface representation or exact memorization, and its
latent variables have verified causal function.

## Resource accounting

Report separately:

- the information-theoretic lower bound on acquired semantic bits;
- serialized acquired-hypothesis bits;
- Phase 17d source-module bytes;
- excluded platform substrate, currently Python and its standard library.

No 729-byte or LLM-size claim may use this experiment without also including the
front-end grammar and runtime costs.

## Next gate

The next campaign should relax exactly one fixed bias at a time while preserving the
negative and positive identifiability controls:

1. induce verb position and argument slots from repeated state-grounded examples;
2. introduce multiple paraphrastic templates with held-out template/verb pairs;
3. induce entity, action, and relation categories rather than receiving them from
   state keys;
4. add composition of two latent operations and reserve unseen compositions;
5. compare against sequence-aware finite-state and neural baselines, not only
   positionless unigrams;
6. keep intervention-based version-space and latent-causal tests as hard gates.

If semantic behavior ceases to be identifiable under a relaxation, the campaign
must report an impossibility boundary or add explicitly justified supervision. It
must not hide the ambiguity with more parameters or benchmark-specific rules.
