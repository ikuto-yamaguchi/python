# Phase 16a results: frozen third public capability slice

The complete Phase 15d system is frozen before five further public tasks are
evaluated. No benchmark example, target, document, primitive, handler, or surface
compiler is added.

## Anti-specialization checks

- public examples / axes: **200 / 5**
- model fingerprint unchanged: **True**
- exact overlap with the first two public slices: **0**
- benchmark training examples / targets: **0 / 0**
- new handlers / primitives / documents / compilers: **0 / 0 / 0 / 0**

## Frozen public accuracy

| axis | correct | answered | wrong | abstained | examples | accuracy |
|---|---:|---:|---:|---:|---:|---:|
| adjective order | 0 | 0 | 0 | 40 | 40 | 0.0% |
| belief propagation | 0 | 0 | 0 | 40 | 40 | 0.0% |
| causal judgement | 0 | 0 | 0 | 40 | 40 | 0.0% |
| formal validity | 0 | 1 | 1 | 39 | 40 | 0.0% |
| reference resolution | 0 | 0 | 0 | 40 | 40 | 0.0% |

Overall accuracy / coverage: **0.0% / 0.5%**
Answered/correct: **1 / 0**

## Capability gaps

- **causal_judgement**: counterfactual causation, norm sensitivity, intention, and preemption
- **reference_resolution**: syntactic roles, discourse salience, lexical selectional preferences, and ambiguity calibration
- **formal_validity**: quantified proposition normalization and proof or countermodel search
- **adjective_order**: latent semantic adjective classes and language-specific ordering constraints
- **belief_propagation**: speaker truth-state propagation through quoted positive and negative claims

## Resource observation

The frozen run reports approximately 9.62 MB of model and knowledge bytes,
127 MB peak RSS, 91,601 counted primitive operations, 426 reads, and one write
for the 200 examples. These numbers do not establish efficiency because quality
is zero. Resource Pareto claims require matched nonzero quality.

## Claim boundary

This is a frozen failure boundary. No result here authorizes adaptation claims,
open-model parity, runtime Pareto, or general-LLM parity.

## Limitations

- the third slice is still a five-task benchmark sample rather than a complete measure of intelligence
- only the first forty examples of each public task are used
- the frozen system already contains benchmark-informed compilers from Phase 15, although none target these five tasks
- WordNet and fixed provenance documents remain available to the frozen worker
- no matched open-model comparison is included
- a low score identifies missing mechanisms but does not select the correct architecture by itself
- free-form dialogue, real-repository coding, long context, multimodal perception, and autonomous parser induction remain untested
