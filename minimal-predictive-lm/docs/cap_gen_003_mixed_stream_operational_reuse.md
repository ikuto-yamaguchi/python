# CAP-GEN-003-MSO-001: mixed-stream operational reuse

## Purpose audit

The research goal is a tiny learner that acquires broadly reusable executable knowledge from heterogeneous experience. COT-001 showed finite cross-domain reuse, and AAF-001 rejected adapters that merely hide complete transition tables. The next missing capability is to remove supplied domain identities and learn from one ordered mixed stream.

MSO-001 therefore changes the measured capability. The learner receives typed events in one stream, but no task or domain name. It must use the same causal parser, shared operator, and held-out reuse certificate throughout.

## Prior-art boundary

The following are established and are not claimed as new:

- hidden-task inference in meta reinforcement learning, including Meta RL as Task Inference (arXiv:1905.06424);
- task-free continual learning without supplied task identities (arXiv:1812.03596);
- switching dynamical-system identification and segmentation (arXiv:2305.15925);
- online change-point detection, hidden Markov models, and regime inference;
- MDP homomorphisms, graph automorphisms, and action-equivariant latent dynamics;
- minimum-description-length sequence segmentation.

MSO-001 is a project bridge gate, not a publication-level novelty claim.

## Segmentation absorption theorem

For any finite stream containing `N` observed transitions, an unrestricted learner can create one context per transition:

```text
segmenter(event) = a new context for every transition
shared core(adapter, source) = adapter[source]
adapter_i = the one observed successor in segment i
```

This gives zero training error and a constant-size shared core for arbitrary unrelated transitions.

If only the shared core is counted, the apparent reduction is `N / 1`. Once the segmenter and all one-entry adapters are charged, the representation has `N + 2` entries and the reduction becomes:

```text
N / (N + 2) < 1
```

Therefore a small shared core plus perfect training segmentation does not establish reusable knowledge. Segmentation and adapter payloads must be included in the lifetime resource vector.

## Causal-boundary requirement

A segmentation decision used for prospective prediction must be available before the successor being predicted.

Consider two worlds with the same event prefix:

```text
STEP shared
```

but different successors. A boundary key that includes the successor can separate the two training examples perfectly, but it is unavailable at prediction time. Such a segmenter leaks future information and is rejected.

A valid context parser must depend only on the observable prefix, or explicitly charge a later observation and abstain until it arrives.

## Frozen mixed-stream gate

The stream contains only generic records:

```text
RESET
EDGE surface-a surface-b
STEP source successor
FREEZE
```

`RESET` is an observable causal episode boundary. `FREEZE` is the prospective evaluation split. Neither event names a task or domain. Domain names stored in fixture objects are never serialized.

The same parser receives:

- a complete five-state training episode;
- a complete seven-state training episode with the opposite local orientation;
- a held-out nine-state episode with passive structure and one grounded transition;
- an unsupported path-shaped held-out episode.

Within the supplied finite hypothesis language, the learner verifies that the two training episodes support the same oriented-cycle successor operator, creates one orientation adapter per episode, and applies the operator to held-out episodes.

## Results required by the gate

The held-out nine-state episode must satisfy:

- no domain-label token is used;
- zero grounded transitions leaves two orientations and causes abstention;
- one grounded transition selects one orientation;
- all nine transitions are then predicted exactly;
- no future successor is read;
- the path-shaped episode is rejected as unsupported.

A control repeats the same surface states in two episodes with opposite active directions. With causal `RESET` events they are separate contexts. If the resets are removed and the records are merged, the active table becomes contradictory. This establishes that the observed boundary event carries necessary context information in the frozen construction.

## Complete incremental control accounting

For training episodes of sizes five and seven and a held-out episode of size nine:

- separate control tables: 21 entries and 21 active interactions;
- shared representation: one operator, three orientation adapters, and one causal parser = 5 incremental control entries;
- shared acquisition: 12 training transitions plus one held-out grounding interaction = 13 active interactions;
- control-entry reduction: `21 / 5 = 4.2x`;
- held-out interaction saving: eight transitions.

The passive graph payload, raw token parser, induction operations, inference operations, memory, and identifying support are not free. This gate charges the new parser and adapters but remains an incremental control-knowledge experiment rather than a complete raw-data lifetime benchmark.

## What this establishes

MSO-001 advances the project from labeled finite domains to one mixed event stream with hidden domain identities. It demonstrates prospective operational reuse under a causal observable boundary and rejects post-hoc singleton segmentation.

It does not establish:

- discovery of event types from raw bytes or natural language;
- learning boundaries when no causal cue exists;
- induction across multiple structural families;
- transfer on a public or natural interaction trace;
- public benchmark improvement;
- high-school-level or LLM-level intelligence.

The operator hypothesis language is still supplied and contains the cycle family. The result is a bridge toward the objective, not evidence that the objective has been reached.

## Next hypothesis

The next candidate learner should remove at least one of the remaining supplied structures. A useful direction is joint search over:

```text
event parser
context boundary rule
shared executable program
context adapter
```

under a prospective objective:

```text
K(parser)
+ K(boundary rule)
+ K(shared programs)
+ K(adapters)
+ C(induction)
+ C(grounding)
+ C(inference)
+ M(peak)
+ D(identifying support)
+ prospective error and abstention risk
```

A context split is useful only when it creates positive held-out operational reuse surplus after every term is charged.

## Stagnation guard

The next step must not add more cycle sizes, state spellings, or explicit reset examples. It must do at least one of:

- infer boundaries from past-only statistical evidence rather than a supplied `RESET` token;
- learn event roles from less structured records;
- reuse one learned executable component across more than one structural family or CAP-GEN axis;
- evaluate on a public or natural interaction trace.

Another typed cycle stream by itself is not research progress.
