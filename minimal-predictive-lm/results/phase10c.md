# Phase 10c results: concept-first intelligence and language as a codec

World concepts are induced from state transitions before language is attached.
Language is then learned as a sparse bidirectional codec over the shared concepts.

## Non-linguistic concept induction

- interactions: **48**
- opaque surface actions: **12**
- induced concepts: **4**
- pairwise partition recovery: **100.0%**
- experience / concept-machine bits: **147,176 / 4,208**
- compression ratio: **34.98x**

## Language as codec

- calibration examples: **24**
- selected rules: **12**
- near held-out accuracy: **100.0%**
- codec bits: **13,608**

## Language-first versus concept-first

- concept-first total: **17,816 bits**
- language-first repeated programs: **29,160 bits**
- language-first / concept-first: **1.64x**

## New language

- calibration interactions: **8**
- held-out accuracy: **100.0%**
- additional bits: **4,256**

## Language-free planning

- unseen target transitions: **1,024**
- accuracy: **100.0%**
- language feature reads: **0**

## Grounding lower bound

- text-only equivalent groundings: **24**
- minimum symmetry-breaking evidence: **4.585 bits**

This phase does not increase the Stage-C score because it is a synthetic
architecture experiment rather than public open-domain evidence.

## Limitations

- the experiment supplies a finite state relation vocabulary
- each interaction changes exactly one fact
- arguments are already segmented before language grounding
- near held-out language shares lexical roots with calibration examples
- language carries abstract and social knowledge that cannot always be recovered from local physical interaction
- no finite learner can eliminate unavoidable identification, observation, and search costs
