# CAP-GEN-003-ORI-001: opaque event-role induction

## Purpose audit

The research goal is a tiny learner that acquires broadly reusable executable knowledge from heterogeneous experience. RBOR-001 removed explicit context-reset markers, but its records still used semantic labels such as `EDGE` and `STEP`. ORI-001 removes those labels.

The learner receives only opaque triples:

```text
ka amber birch
zu amber ember
```

The first field has no fixed meaning. In one context `ka` denotes passive topology and `zu` denotes active transitions; in another context the mapping is reversed. Reusing the surface spelling is therefore an invalid shortcut.

## Prior-art boundary

The following are established and are not claimed as new:

- latent-action learning from videos without ground-truth action labels;
- hidden-task inference and belief-state inference in meta reinforcement learning;
- non-identifiability of unsupervised representations without inductive biases;
- action-equivariant representations and MDP homomorphisms;
- graph automorphisms, permutation ambiguity, and finite hypothesis search;
- event schema and semantic-role induction.

ORI-001 is a project bridge gate. It is not a publication-level novelty claim.

## Explicit inductive bias

The finite hypothesis language assumes that each useful context contains two local relation symbols:

1. one relation can be interpreted as an undirected connected degree-two cycle;
2. the other relation can be interpreted as a deterministic successor operation selecting one orientation of that cycle.

This assumption is supplied. The learner does not discover the cycle family from unrestricted raw data. The purpose of the gate is to remove supplied event-role names while making the remaining bias visible and testable.

## Local role permutation

Let a context contain opaque relation symbols `r` and `s`. The learner evaluates both assignments:

```text
r -> topology, s -> action
r -> action,   s -> topology
```

An assignment survives only if:

- topology records remain a valid prefix of a connected degree-two cycle;
- action records remain a deterministic transition table;
- after topology completion, observed actions agree with at least one cycle orientation.

A training context is certified only when exactly one role assignment survives, the orientation is unique, and every state has an observed action transition.

The role adapter is local. The same surface symbol may change role across contexts.

## Role non-identifiability proposition

Suppose both opaque relations form complete directed cycles over the same undirected topology, but in opposite orientations. Then both role assignments satisfy the supplied structural family:

```text
x -> topology, y -> action
x -> action,   y -> topology
```

If these assignments induce different prospective successor tables, observations do not identify which semantic role is correct within the hypothesis class.

The learner must therefore abstain. Choosing one assignment by token order, frequency, or implementation accident would manufacture semantics that the data do not support.

## Causal boundary proposal

The reset-free parser maintains every role interpretation consistent with the current prefix. A boundary is proposed only when the current opaque record has zero support under all retained interpretations and the preceding context is already certifiable.

The proposal uses only past and current records. It does not inspect withheld future transitions. Boundary proposal and context certification remain separate: a surprising record can start a candidate segment, but that segment is not accepted as reusable knowledge until it supports prospective transfer.

## Role absorption theorem

An unrestricted parser can assign each observed transition a private semantic role and store its successor in a one-entry adapter. A constant lookup core then obtains zero training error for arbitrary data.

For `N` observed transitions:

```text
reported shared core = 1
parser payload        = N
adapter payload       = N
fully charged total   = 1 + 2N
```

Counting only the core reports `N`-fold compression. Complete accounting gives:

```text
N / (1 + 2N) < 1
```

For the frozen twelve-transition training prefix, the apparent reduction is `12x`, while the fully charged reduction is `12/25 = 0.48`.

A small shared core is therefore not evidence of learned semantics when the parser or adapters contain the examples.

## Future-role leakage

A held-out role adapter may not inspect withheld successor records to decide which opaque relation means action. Such a parser can report one grounded interaction while silently reading the other eight targets.

ORI-001 records this as eight future successors used and rejects the certificate regardless of final accuracy.

## Frozen stream

The 38-record stream contains:

- a complete five-state training context;
- a complete seven-state training context whose two opaque role symbols are reversed;
- a nine-state held-out context with complete passive support and one grounded active transition;
- an unsupported path-shaped context.

There are no `RESET`, `EDGE`, `STEP`, `FREEZE`, task-name, domain-name, or episode-number tokens in the stream.

The required results are:

- both training contexts have exactly one surviving role interpretation;
- their local role mappings are opposite;
- copying the first mapping into the second context causes contradiction;
- all boundary proposals are causal;
- one held-out interaction yields exact prediction of all nine transitions;
- zero held-out interactions leaves two orientations and causes abstention;
- unsupported topology is rejected;
- the symmetric role control causes abstention;
- future-role leakage is rejected;
- role absorption fails complete accounting.

## Resource vector

Separate transition tables use:

```text
executable entries = 21
active interactions = 21
passive observations = 0
boundary proposals = 0
```

The shared opaque-role representation uses:

```text
executable entries = 9
  opaque record parser
  causal boundary rule
  shared operator
  three role adapters
  three orientation adapters
active interactions = 13
passive observations = 21
boundary proposals = 3
```

With every component assigned unit cost, the global scalar surplus is `-4`. ORI-001 is therefore not a universal resource victory.

After the shared library exists, the incremental new-context comparison is:

```text
separate = 9 stored transitions + 9 active interactions = 18
shared   = role adapter + orientation adapter + one active interaction
         + nine passive observations + one boundary = 13
incremental surplus = 5
```

The result supports economical reuse for additional contexts under the frozen cost model, while honestly retaining the global trade-off.

## What this establishes

ORI-001 removes supplied event-role names and permits context-local role permutation. It demonstrates that executable structure can identify opaque roles prospectively, and that non-identifiable roles can be handled by abstention rather than guessing.

It does not establish:

- discovery of record fields or event spans from raw bytes;
- induction of the executable structural family itself;
- stochastic-noise robustness;
- semantic grounding in a physical environment;
- transfer across multiple structural families or capability axes;
- public benchmark progress;
- natural-language understanding;
- high-school-level or LLM-level intelligence.

## Next hypothesis

The next learner must remove another supplied structure. The strongest direction is joint induction of record boundaries and executable program candidates from raw or weakly delimited sequences, with calibrated evidence under noise.

A candidate component may enter the shared library only when it improves prospective operational reuse after charging:

```text
K(record parser)
+ K(boundary rule)
+ K(role adapters)
+ K(shared programs)
+ K(context adapters)
+ C(induction)
+ C(active grounding)
+ C(passive support)
+ C(inference)
+ M(peak)
+ prospective error and abstention risk
```

## Stagnation guard

The next step must not add more opaque tag spellings, deterministic cycle sizes, or hand-designed role permutations. It must do at least one of:

- infer record boundaries from raw bytes or an undelimited symbol stream;
- induce more than one executable structural family with a shared component;
- handle stochastic noise with calibrated abstention;
- evaluate the same artifact on a public or natural interaction trace.

Another finite opaque-tag cycle stream by itself is not research progress.
