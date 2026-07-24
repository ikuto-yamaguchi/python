# Causal Identifiability Audit C008

Date: 2026-07-25
Track: C — causal grounding / world identity / counterfactuals
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison**.

No new architecture, toy mechanism, ontology, intervention label, memory mechanism, pretrained language model, or branch was introduced.

## Question under audit

Does the surviving theory-only candidate RQ-001-T1 remain distinct from existing identifiability results when raw language is treated as side information or an auxiliary variable?

Current candidate:

> Under explicit observation and intervention assumptions, characterize when raw language strictly refines the causal equivalence class identifiable from trajectories alone, and prove impossibility when language contains no mechanism information conditional on the complete non-language history or when available interventions cannot separate competing partitions.

## Primary-source comparison

### Nonlinear ICA using auxiliary variables — Hyvärinen, Sasaki & Turner, AISTATS 2019

This work proves identifiability of nonlinear ICA by augmenting observations with an auxiliary variable `u`, which may be a time index, history, class/domain label, or other observed side information. The estimator distinguishes correctly paired `(x, u)` samples from samples where the auxiliary variable is randomized.

Primary source:

- https://proceedings.mlr.press/v89/hyvarinen19a.html

Relevant assumptions and guarantee:

- observations are an invertible nonlinear mixture of independent latent components;
- conditional latent distributions vary with the auxiliary variable;
- the variation must be sufficiently rich to satisfy a variability/rank condition;
- the recovered sufficient statistics are identifiable up to component-wise transformations and the theorem-specific equivalence;
- randomizing the auxiliary variable is part of the contrastive estimation construction.

Consequence for RQ-001-T1:

If raw language `L` is used only as an observed variable that indexes changes in latent distributions, then the broad claim

> language side information makes otherwise non-identifiable latent factors identifiable

is already prior art in auxiliary-variable nonlinear ICA. Replacing a domain label with an utterance encoder does not create a new identifiability result.

A future theorem cannot count the following as novelty:

1. treating an utterance embedding as auxiliary variable `u`;
2. contrasting correct trajectory-language pairs with shuffled pairs;
3. recovering components because their conditional distributions vary across utterances;
4. proving recovery only up to the same component-wise equivalence already obtained by auxiliary-variable nonlinear ICA.

### Nonlinear ICA of temporally dependent stationary sources — Hyvärinen & Morioka, AISTATS 2017

This work proves identifiability from temporal dependence by discriminating real temporal windows from temporally permuted windows.

Primary source:

- https://proceedings.mlr.press/v54/hyvarinen17a.html

Consequence:

Trajectory history itself may already serve as the identifiability signal. Therefore any claimed language contribution must be measured after conditioning on the complete temporal information used by trajectory-only identifiable models. A language gain obtained because the trajectory baseline omitted history is invalid evidence for T1.

### Unifying causal representation learning with the invariance principle — Yao et al., ICLR 2025

This work interprets many CRL identifiability results as alignment with symmetries/invariances induced by data-generating environments and interventions.

Primary source:

- https://openreview.net/forum?id=lk2Qk5xjeu

Consequence:

A claim that language selects an invariant representation or breaks a symmetry is too broad. T1 must specify exactly which trajectory-only symmetry group remains, which language observation removes it, and why this reduction is not merely an environment-indexed invariance result.

### Identifiable multimodal causal representation learning under partial latent sharing — Benhamza, Clausel & Tami, 2026

This work establishes component-wise identifiability for nonlinear multimodal observations with partially shared causal latent variables.

Primary source:

- https://arxiv.org/abs/2605.19135

Consequence:

Treating language and trajectory as two modalities with shared latent factors is also insufficient for novelty. T1 must not reduce to shared-latent multimodal identifiability with language as one modality.

## Assumption matrix

| Setting | Side information supplied | Source of identifiability | Guarantee | Why it does not establish the candidate claim |
|---|---|---|---|---|
| Auxiliary-variable nonlinear ICA | observed auxiliary `u` | conditional distribution variation and rank condition | component-wise/sufficient-statistic recovery under nonlinear mixing | does not identify semantic utterance equivalence or intervention partitions unless those are already encoded by `u` |
| Temporal nonlinear ICA | temporal adjacency/history | non-Gaussian temporal dependence | source recovery under temporal assumptions | language adds nothing unless it separates ambiguity remaining after complete history |
| Multimodal partial sharing | modality membership and shared structure | partial latent sharing under nonlinear mixing | component-wise causal latent recovery | language is only another modality; no unknown intervention partition is jointly discovered |
| RQ-001-T1 candidate | raw utterance plus complete trajectory | must be stated | must strictly refine a trajectory-only causal equivalence class | currently lacks a theorem beyond the three settings above |

## Sharpened no-novelty criterion

Let `X` contain all non-language observations, including full state/action/history/reward/time/policy/environment information. Let `L` be raw language and `M` an independently defined mechanism abstraction.

The condition `I(M; L | X) > 0` remains necessary but is not enough for either identifiability or novelty.

T1 is **not novel** if there exists a deterministic statistic `U = h(L)` such that:

1. `U` is merely an observed auxiliary/environment index;
2. the conditional latent family `p(z | U)` satisfies an existing auxiliary-variable nonlinear-ICA variability condition;
3. the claimed recovery is no finer than the component-wise equivalence guaranteed by that theorem.

In that case, the result is an application of existing auxiliary-variable identifiability, not a new language-causal theorem.

## Surviving distinction required for T1

For T1 to remain scientifically distinct, a preregistered theorem must exhibit all of the following:

1. **Trajectory-only equivalence:** two non-isomorphic or differently partitioned causal models induce the same distribution over complete non-language trajectories `X`.
2. **Same coarse auxiliary index:** the models remain indistinguishable under every language statistic that acts only as an environment/domain index.
3. **Compositional language relation:** raw utterances contain relational or equivalence constraints that cannot be reduced to a supplied class label or environment ID.
4. **Strict class refinement:** correct language reduces the trajectory-only equivalence class, while matched language shuffle does not.
5. **Intervention-supported semantics:** the refined class corresponds to independently separable mechanism effects, not researcher-named slots.
6. **Novel guarantee:** the conclusion is stronger or based on weaker/different assumptions than auxiliary-variable nonlinear ICA, temporal nonlinear ICA, multimodal shared-latent recovery, and environment-indexed CRL.

No such positive construction or theorem is currently present in the repository.

## Decision

### RQ-001-T1: NARROWED AGAIN — NOT ADOPTED

The theory-only candidate survives only in the following stricter form:

> Characterize whether compositional relations among raw utterances can remove a causal-model equivalence that remains after conditioning on complete trajectories and after quotienting out every use of language as a mere auxiliary/environment index; prove an impossibility result when language is reducible to such an index or when interventions do not separate the competing partitions.

This is a narrower and harder claim than the previous T1. It is not adopted because:

- no nontrivial positive construction has been established;
- the equivalence relation is not yet formalized;
- novelty beyond auxiliary-variable and multimodal identifiability is not proved;
- empirical Gate I remains rejected for lack of a qualifying public benchmark;
- R0.1 public capability reproduction remains incomplete.

## Required next C-cycle

Allowed work:

- formalize the trajectory-only model equivalence and the quotient by auxiliary-index information;
- construct one exact negative example showing that utterance labels reducible to environment IDs cannot identify semantic partitions;
- search for a primary theorem already covering relational/multi-view auxiliary variables;
- draft a preregistration only after the novelty matrix is complete.

Forbidden work:

- new architecture;
- a hand-authored language ontology;
- synthetic operation/goal mechanisms;
- an intervention target label invented for SILG;
- claiming novelty from language shuffle, mutual information, or multimodal fusion alone.

## Status

- Public capability baseline reproduced: no
- Empirical Gate I: rejected
- RQ-001-T1: narrowed, not adopted
- New architecture: none
- Novelty: not established
- Intelligence principle: not discovered
- Capability progress: not recognized
- High-school-level intelligence: not achieved
