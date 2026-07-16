# SPARC: Surprise-Propagated Active Relational Cognition

## Why SACS is not enough

SACS removes the growing KV cache and bounds active memory, but it still applies
matrix-vector work for every input unit. This preserves an important inefficiency
shared by Transformers, SSMs and conventional RNNs: the system advances on the
clock or token stream even when nothing cognitively relevant changed.

SPARC changes the unit of computation from a token to a prediction error event.
If the active world model already predicts the observation within tolerance, the
system performs no memory write and almost no graph propagation.

## Computational substrate

### Sparse distributed event code

An observation is represented by a k-of-D code. Similar events overlap. The code
is not compared against every stored concept. An inverted index maps active bits
directly to the few concepts that could match.

### Novelty allocation

Candidate concepts vote by code overlap. If no candidate exceeds the familiarity
threshold, one new concept is allocated. Storage therefore grows with distinct
predictive structure, not raw sequence length.

### Local predictive microprogram

Each concept stores only:

- a sparse prototype;
- a compact prediction payload;
- bounded outgoing transition counters;
- local confidence and recency statistics.

A concept is updated only when its prediction error exceeds a threshold. The
update is local; no global backward pass or dense parameter sweep is required.

### Active relational frontier

Reasoning activates a bounded frontier of concepts. Messages propagate only
along the highest-confidence local edges. Compute is conditional on ambiguity:
known routine events halt immediately, while novel or difficult events expand a
few more graph steps.

### Multi-timescale consolidation

Frequently repeated microprograms are merged into stable semantic nodes. Rare
episodes remain compressed in cold storage. Consolidation may run asynchronously
or during idle periods, analogous to replay, so the interactive path remains
small.

## Resource behavior

Let k be active code bits, p the mean posting-list length, b the active frontier
width and d the bounded node degree.

- event lookup: approximately O(k * p), not O(number_of_nodes);
- one-step reasoning: O(b * d);
- write cost: paid only on surprise;
- working memory: O(k + b * d), independent of history length;
- long-term storage: proportional to distinct learned structure, not tokens.

This can beat a fixed-state matrix model when the world is predictable and event
sparsity is high. It can lose when every input is novel or the learned code
produces long posting lists; both failure modes must be measured.

## Relationship to the brain

SPARC uses only broad computational principles rather than claiming biological
fidelity:

- sparse distributed activity;
- prediction-error-driven updates;
- local plasticity;
- recurrent active sets;
- multiple consolidation timescales;
- asynchronous event processing.

The current prototype uses deterministic software data structures. Neuromorphic
or compute-in-memory hardware is a later co-design target, not assumed in the
algorithmic results.

## Language path

SPARC does not generate Japanese by replaying stored answers. The intended model
has two learned surfaces:

1. an event compiler that maps variable-length language spans into sparse event
   codes and prediction targets;
2. a small recurrent renderer that converts a semantic action plan into text.

Internal thought can run for several event steps without emitting tokens. Output
is generated only after the controller reaches a stable plan, avoiding the need
to perform full cognition again for every emitted character or subword.

## Falsifiable first gate

On a long stream with repeated latent structure and rare changes, SPARC must:

- retain associative and transition accuracy;
- allocate far fewer nodes than observations;
- write on a minority of observations;
- inspect a bounded, small candidate set;
- use less estimated work than a full scan and less state than a history cache;
- outperform a fixed single-state recurrence.

Passing this gate proves only that event-driven predictive memory is viable. It
does not prove language understanding or high-school-level intelligence.
