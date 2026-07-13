# CAP-GEN-002 prior-art matrix

This matrix is a rejection tool, not a citation count.  A candidate that reproduces a
row without a formal difference is not promoted.

| family | already provides | therefore insufficient as novelty |
|---|---|---|
| Factor graphs / variable elimination | sparse factorization and exact inference controlled by graph structure and treewidth | a learned Boolean table and min-sum runtime |
| Sum-product networks | deep sum/product circuits with tractable exact inference under structural conditions | replacing factors by a deep probabilistic circuit |
| Deep arithmetic circuits / hierarchical tensors | formal depth-efficiency and exponential shallow-vs-deep separations | merely observing that nonlinear or multiplicative composition is expressive |
| Recurrent networks | repeated shared nonlinear transformations with fixed parameters | weight sharing through time |
| Neural programmer-interpreters | task-agnostic recurrent core plus persistent program memory and compositional subprogram calls | adding a program table beside a recurrent core |
| DreamCoder / Stitch | learned reusable symbolic abstractions and corpus compression | extracting repeated symbolic subtrees into macros |
| MDL recurrent networks | compact neural solutions selected by description-length objectives, with proofs on formal languages | adding a parameter-count penalty to an RNN |
| Low-rank adapters / modular networks | parameter-efficient residual maps and reusable modules | quantized low-rank nonlinear residual blocks alone |
| Neural semigroup operators | consistency of composed learned evolution operators | enforcing only a semigroup law on learned maps |

## Candidate-specific unresolved differences

The resource-conditioned nonlinear generator grammar is not considered novel until all
questions below are answered.

1. Is its objective genuinely different from MDL neural training once compute and
   memory are encoded into the prior or loss?
2. Is approximate nonlinear macro invention different from library learning plus
   quantization or module merging?
3. Does learning the composition grammar from one unlabeled mixed stream provide a
   formal identifiability result not already covered by latent-program induction?
4. Is there a resource separation that depends on the complete architecture, rather
   than on the already-known benefit of depth or recurrence?
5. Can the same learned artifact improve unrelated public axes without a hidden
   domain-specific compiler?

Until at least one answer is supported by a theorem and the remaining answers are
bounded by explicit counterexamples, the candidate status is
`novelty_hypothesis_unverified`.

## Initial literature anchors

- Kschischang, Frey, and Loeliger: factor graphs and the sum-product algorithm.
- Poon and Domingos: sum-product networks.
- Cohen, Sharir, and Shashua: deep arithmetic circuits and tensor-analysis depth
  efficiency.
- Telgarsky: depth-separation results for repeated nonlinear constructions.
- Reed and de Freitas: neural programmer-interpreters.
- Ellis et al.: DreamCoder.
- Bowers et al.: Stitch / top-down library learning.
- Lan et al.: minimum-description-length recurrent neural networks.

This list is a starting boundary, not an exhaustive novelty search.
