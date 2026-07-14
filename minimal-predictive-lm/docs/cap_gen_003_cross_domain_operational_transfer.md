# CAP-GEN-003-COT-001: cross-domain operational transfer

## Purpose audit

The research goal is not to perfect a finite symmetry toolkit. It is to build a tiny learner that acquires broadly reusable intelligence from data. CAP-GEN-002 established safety and identifiability constraints for action grounding, but continuing to refine finite tests would become a local loop. COT-001 therefore changes the measured capability: one learned operational structure must transfer across domains with different surface vocabularies.

## Prior-art boundary

The following are established and are not claimed as new:

- program-library learning and abstraction invention, including DreamCoder and Stitch;
- MDP homomorphisms and action-equivariant latent representations;
- generalist agents trained across many modalities and tasks;
- shared action tokenizers and latent action spaces across embodiments;
- graph automorphisms, orientation, stabilizers, and symmetry breaking.

COT-001 is a project gate, not a publication-level novelty claim.

## Negative result: shared surface is not shared operation

Two domains may use the same action spelling while assigning opposite executable effects. Training domains and a held-out domain can therefore share every action token but disagree on the correct successor relation. Surface identity, embedding similarity, or compression of repeated words cannot certify transferable control semantics.

The frozen gate uses the action spelling `step` everywhere. A surface-only baseline copies the orientation index learned in the first domain and obtains zero exact transitions on the held-out domain.

## Positive finite theorem

Assume each domain supplies an observable connected undirected cycle over its local state surfaces. A shared executable operator is known to select one of the two cycle orientations. Then:

1. with no grounded active transition, the two orientations are observationally indistinguishable;
2. one grounded directed edge selects exactly one orientation;
3. once the orientation is selected, the shared successor operator determines every active transition in the domain;
4. if the passive topology is not a connected degree-two cycle, the transfer certificate does not apply and the learner must abstain.

This is a finite graph-homomorphism and symmetry-breaking fact, not a new mathematical theorem.

## Frozen cross-domain gate

The same learner and artifact receive:

- a five-state domain with complete active support;
- a seven-state domain with complete active support and the opposite surface orientation;
- a held-out nine-state domain with passive topology and only one grounded active edge.

There are no domain-specific solvers. Domain names and state spellings are opaque to the algorithm. The learner validates the structural family, learns one `oriented-cycle-successor` operator, infers one orientation adapter per domain, and predicts all nine held-out transitions.

Baselines and controls:

- zero held-out anchors must abstain with two remaining orientations;
- a separate transition table with one observation covers only one of nine states;
- copying the shared surface token orientation must fail on every held-out state;
- a path topology must be rejected rather than forced into the learned family;
- incomplete training support must not certify the shared operator.

## Resource accounting

For the frozen domains of sizes 5, 7, and 9:

- separate control tables store 21 transition entries and require 21 active interactions;
- the shared representation stores one operator plus one orientation adapter for each of three domains, for four incremental control entries;
- acquisition uses all 12 training transitions plus one held-out grounding interaction, for 13 active interactions;
- the held-out domain saves eight of nine direct control interactions;
- incremental control-entry reduction is 21 / 4 = 5.25x.

The passive graph, surface identifiers, parsing cost, induction operations, inference operations, and memory must be charged separately in later raw-stream experiments. They are not free merely because this finite gate focuses on incremental control knowledge.

## What this does and does not establish

COT-001 establishes a bridge from action-grounding theory to cross-domain reuse. It does not establish:

- raw event-boundary discovery;
- natural-language understanding;
- transfer to a genuinely novel structural family;
- public benchmark improvement;
- high-school-level or LLM-level intelligence.

The topology and relation types are supplied in structured finite form. The result is therefore evidence for the objective and a rejection gate for surface-only transfer, not evidence of general intelligence.

## New hypothesis candidate

The unverified candidate is a learner that, from one raw mixed interaction stream and without task identifiers, jointly discovers:

1. event boundaries and connected interaction contexts;
2. domain adapters;
3. shared executable operators whose diagrams commute across domains;
4. the minimum grounding interactions needed for a new domain;
5. a shared library chosen by lifetime code, induction, inference, memory, support, and interaction cost.

The key transfer criterion is operational: applying a domain action and then encoding must agree with encoding first and applying the shared operator. Surface token equality is neither necessary nor sufficient.

## Stagnation guard

The next step must not add more cycle sizes, spellings, or graph colors. It must do at least one of the following:

- infer relation/event roles from a less structured mixed stream;
- transfer one shared operator across structurally different but homomorphic public or natural traces;
- jointly learn the adapter and operator rather than receiving passive topology;
- connect the same artifact to multiple CAP-GEN capability axes.

A further finite cycle example by itself is not research progress.
