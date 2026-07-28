# Causal Identifiability Audit C033

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, branch, or PR chain was introduced.

## Primary work newly audited

### Identifiable Multimodal Causal Representation Learning under Partial Latent Sharing

Manal Benhamza, Marianne Clausel, and Myriam Tami. arXiv:2605.19135, version 1, 18 May 2026.

Primary record:

- arXiv: https://arxiv.org/abs/2605.19135
- PDF: https://arxiv.org/pdf/2605.19135

The paper studies multimodal observations in which modality \(m\) is generated from a subset \(A_m\) of latent causal variables,

\[
x^{(m)}=f_m(z_{A_m}),
\]

so the latent structure is only partially shared across modalities. Its central relevance to RQ-001 is that a language channel can be represented mathematically as one additional modality. Therefore, before treating language/trajectory alignment as a new joint-identification principle, the strongest multimodal partial-sharing identifiability result must be removed from the novelty space.

The inspected theorem assumptions include:

- smooth nonlinear modality-specific generating functions;
- full-column-rank Jacobians for the true and estimated generating functions;
- proper generating functions;
- a directed restriction in which shared variables may cause modality-specific variables, but modality-specific variables do not cause shared variables;
- conditional and marginal independence restrictions across modality-specific variables;
- for every modality, existence of another modality with no shared latent variables;
- a mixing-density condition excluding non-component-wise latent transformations that would make the cross-modality causal graph no denser;
- an estimated causal graph at least as sparse as the true graph on non-sharing modality pairs.

Under the block-identification conditions, shared latent blocks are identified. Under the additional non-overlap, mixing-density, and causal-structural-sparsity conditions, shared and modality-specific variables are identified up to permutation and component-wise smooth bijections. The guarantee is observational and does not require intervention labels or a pretrained language model.

The proposed estimator uses modality-specific autoencoders, a Wasserstein-based module for discovering and aligning partially shared latent elements, and a normalizing-flow causal model with sparsity and acyclicity penalties. This is a learning construction accompanying the theorem; it is not evidence that arbitrary raw language automatically satisfies the theorem's assumptions.

## Official-code audit

The arXiv record and targeted GitHub repository search performed on 2026-07-26 did not expose a paper-specific author repository whose commit, dependency lock, dataset version, and reproduction command could be immutably pinned. A generic third-party page offered only a “request code” action. Therefore no public baseline experiment was started in this cycle.

This is classified as **official code not verified**, not as evidence that no code exists. Reproduction remains blocked until an author-controlled repository or archived artifact is located.

## Theorem / assumption boundary added to the prior-art matrix

The following claims are excluded from the novelty space:

- aligning a language channel and an environment channel through shared latent variables is by itself a new identifiability principle;
- partial sharing between language, state, action, and outcome modalities necessarily prevents component-wise recovery;
- nonlinear or undercomplete observations require language-specific supervision before shared and modality-specific latent variables can be identified;
- discovering which latent variables are shared between language and trajectory is equivalent to discovering raw-language equivalence;
- a Wasserstein alignment, multimodal reconstruction score, shared-latent probe, or cross-modal transfer result demonstrates identification of a semantic intervention-target partition;
- adding a human-readable modality removes the component-wise reparameterization ambiguity without an externally fixed denotation law.

The result also creates a required applicability audit for RQ-001. A language channel can contribute to identifiability through ordinary multimodal structure only if the benchmark actually satisfies the paper's partial-sharing graph, rank, properness, independence, non-overlap, density, and sparsity assumptions. If those conditions hold, the corresponding shared/component-wise recovery is prior art. If they do not hold, task performance cannot be used as a substitute for an identifiability proof.

## Identifiability counterexample: perfect multimodal latent recovery without raw-language equivalence recovery

Let the observed modalities be trajectory \(X\) and raw language \(U\). Suppose the strongest multimodal result correctly identifies a shared causal variable \(C\) and modality-specific variables \(S_X,S_U\), up to component-wise smooth bijections:

\[
X=f_X(C,S_X),\qquad U=f_U(C,S_U).
\]

Assume \(C\) contains an intervention-relevant block \(B\), but the scientific target is a finer partition \(P=\{P_1,\ldots,P_r\}\) inside \(B\), together with a raw-utterance equivalence relation \(Q\).

Construct Model A with \((P,Q,d)\), where \(d:U/Q\to P\) is a denotation map. Construct Model B by applying a nontrivial bijection \(\pi\) within \(B\), recoding the fine target partition to \(P'=\pi(P)\), recoding utterance classes to \(Q'\), and replacing the denotation and language generator by

\[
d'=\pi\circ d,
\]

with the corresponding inverse transformation inside \(f_U\) and the language encoder.

The two models can preserve:

- the complete joint distribution of all observed modalities;
- the partially shared latent incidence structure;
- every shared/modality-specific block recovered by the multimodal theorem;
- the latent causal graph up to the theorem's allowed component-wise transformations;
- reconstruction, cross-modal prediction, Wasserstein alignment, and normalizing-flow likelihood;
- next-state prediction, action accuracy, and task success;
- paraphrase accuracy, language-shuffle gaps, and cross-modal transfer whenever these depend only on the recovered shared block.

Nevertheless, \(P\neq P'\) and \(Q\neq Q'\). Thus:

> Component-wise identification of partially shared multimodal causal variables does not identify the raw-utterance equivalence classes or their fine-grained denotation into a latent intervention-target partition.

This counterexample remains even when language is the only modality that names the shared variable. Human readability is not an anti-recoding constraint: the target block, utterance classes, denotation map, and language encoder can still be transformed jointly unless the denotation is fixed outside the learned multimodal system.

## Necessary boundary for a surviving language contribution

Let \(S_{MM}\) contain the complete non-language trajectory, the multimodal shared/specific incidence structure, all latent components identifiable under the audited theorem, actions, outcomes, environment IDs, and interaction history. Let \(P_{residual}\) be the target partition remaining after this strongest multimodal recovery.

A necessary information condition is

\[
I(P_{residual};L\mid S_{MM})>0.
\]

This remains insufficient. Adoption additionally requires an externally fixed language law that is not jointly learnable with the representation and that makes the residual automorphism group trivial. In particular, language must not merely:

- identify which modality-shared block is active;
- paraphrase a shared variable already recoverable from trajectory;
- encode environment identity, reward, action target, or completed outcome;
- provide a class label whose meaning is learned only through the same latent alignment objective.

## Updated decision for RQ-001

**NARROWED BEYOND PARTIALLY SHARED MULTIMODAL COMPONENT-WISE IDENTIFIABILITY — NOT ADOPTED**

The only remaining candidate is:

> After applying the strongest applicable multimodal partial-sharing identifiability result to language, state, action, and outcome channels, can a preregistered externally fixed denotation law distinguish a residual intervention-target partition inside an already identified shared component, jointly identify raw-utterance equivalence, and eliminate every joint recoding of the target block, utterance classes, denotation map, and language encoder?

Adoption now requires at minimum:

1. an explicit mapping from SILG observations, instructions, actions, and outcomes to modalities and latent subsets;
2. an audit of full-column-rank, properness, partial-sharing graph, conditional-independence, non-overlap, mixing-density, and sparsity assumptions;
3. the maximal shared and modality-specific representation identifiable without semantic target labels;
4. a concrete countermodel pair with identical multimodal observable law and different residual target/utterance partitions;
5. language information unavailable from states, actions, rewards, environment IDs, and completed trajectories;
6. a denotation anchor fixed before model fitting;
7. a proof that the residual joint automorphism group is trivial with the anchor and nontrivial without it;
8. direct recovery metrics for both raw-utterance equivalence and target partition;
9. language-blind, state-only, modality-shuffle, target-label-shuffle, and outcome-shuffle controls on identical instances;
10. immutable reproduction of an applicable public multimodal or non-language baseline before architecture work;
11. preregistration before any new mechanism is authorized.

## Status

- RQ-001: further narrowed; not adopted
- partially shared multimodal component-wise identifiability: prior art under explicit assumptions
- raw-language equivalence identification: not established
- fine intervention-target partition identification: not established
- official paper-specific immutable code: not verified
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
