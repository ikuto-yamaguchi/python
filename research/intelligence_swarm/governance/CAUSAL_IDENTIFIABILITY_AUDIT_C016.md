# Causal Identifiability Audit C016

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + identifiability counterexample**.

No new architecture, toy mechanism, intervention ontology, benchmark, memory mechanism, or branch was introduced.

## Primary work newly audited

### Isolated Causal Effects of Natural Language

Lin, Morency and Ben-Michael, ICML 2025.

Primary sources and official code:

- https://proceedings.mlr.press/v267/lin25k.html
- https://openreview.net/forum?id=Z0jnz149L1
- https://github.com/torylin/isolated-text-effects

The paper studies estimation of the isolated causal effect of a **predefined focal language-encoded intervention** on an external outcome. Its central difficulty is approximating all non-focal language well enough to avoid omitted-variable bias. It evaluates effect-estimate quality through fidelity and overlap and provides sensitivity analysis when the non-focal approximation is imperfect.

The official repository reproduces the paper's Amazon and tirzepatide experiments. This is relevant public code, but it is not a causal-representation or latent-partition recovery baseline: the focal treatment concept and external outcome are specified before estimation.

## Precise boundary with RQ-001

The paper answers a different question from RQ-001.

- Lin et al.: given a focal text intervention `A`, non-focal text `W`, and outcome `Y`, estimate the causal effect of changing `A` while preserving or approximating `W`.
- RQ-001: discover whether raw utterance equivalence classes and an unknown latent intervention-target partition can be jointly identified.

Effect identification does not imply representation identification. Even a perfectly estimated nonzero effect of a named language feature does not show that the feature corresponds one-to-one with a latent mechanism component, nor that the latent target partition is uniquely recoverable.

This removes another overbroad novelty route:

> A language feature has a reproducible causal effect on behavior, therefore its latent intervention target has been identified.

That implication is invalid without an additional bridge theorem.

## Counterexample: identified text effect, unidentified latent target partition

Let a predefined focal language treatment be binary, `A in {0,1}`, and let the observed outcome satisfy

`Y = A xor U`,

where `U` is observed or randomized away so that the average causal effect of `A` is identifiable.

Consider two latent mechanism models.

Model M1:

- `A` acts on one latent target `Z1`;
- `Y` is generated from `Z1`.

Model M2:

- `A` acts jointly on two latent targets `(Z1', Z2')`;
- the outcome depends only on their parity, `Z1' xor Z2'`.

Choose the intervention and outcome maps so that both models induce exactly the same distribution over `(A, W, Y)` under every supported text intervention. The isolated causal effect of `A` on `Y` is then identical and can be estimated without bias, while the latent target cardinality and partition differ.

Therefore:

- randomized or well-controlled language interventions can identify an effect;
- fidelity and overlap can validate that effect estimate;
- neither result identifies the latent intervention partition;
- an injective, externally anchored map from language intervention components to latent mechanism effects is still required.

## Bridge conditions required for partition identification

To use an isolated-language-effect design as evidence for RQ-001, all of the following must be added and proved:

1. **Externally fixed focal intervention semantics.** The focal language manipulation must be defined independently of the learned latent representation.
2. **Exclusion.** The manipulation may affect the observed dynamics only through the claimed latent mechanism block, or the permitted multi-block map must be explicit.
3. **Injectivity or separating family.** Distinct latent target partitions must induce distinguishable families of anchored language effects.
4. **Sufficient overlap.** Every comparison needed to separate candidate targets must have support; lack of overlap cannot be repaired by representation learning.
5. **Non-focal fidelity.** Approximation error in the remaining language must be bounded tightly enough that omitted-variable bias cannot mimic target separation.
6. **No joint recoding.** The language intervention map may not be transformed together with the latent representation.
7. **Population generalisation.** Separation must persist on unseen utterance forms, compositions and systems, not only a finite intervention vocabulary.

Without these conditions, language-effect estimation is at most evidence that wording matters for an outcome, not evidence that raw language equivalence or latent intervention partitions are identified.

## Refined theorem/assumption comparison

| Dimension | Isolated causal effects of language | Causal representation / partition identification | Remaining RQ-001 burden |
|---|---|---|---|
| Object identified | Effect of a predefined focal language intervention | Latent variables, graph, mechanism blocks or abstraction | Prove an effect family uniquely separates candidate latent partitions |
| Language structure | Focal versus non-focal content supplied or operationalised | Raw equivalence and component structure may be unknown | No supplied target/component/paraphrase labels |
| Main assumptions | Fidelity, overlap, treatment definition, confounding control | Mixing, interventions, variation, sparsity, symmetry restrictions | Combine both without smuggling in the answer |
| Main failure | Omitted-variable bias and poor support | Observational equivalence and latent reparameterisation | Show anchored language removes a stated residual symmetry |
| Official code role | Effect-estimation reproduction | Not a latent-partition baseline | Prior-art boundary only; no RQ reproduction claimed |

## Updated admissible RQ

The remaining admissible formulation is now:

> After applying the strongest non-language causal-representation criteria, can a population of externally fixed language interventions with verified fidelity and overlap form an injective separating family over the remaining causal abstractions, so that raw unseen utterance relations strictly refine an otherwise unidentified latent intervention-target partition?

This formulation is **not adopted**. It remains a preregistration candidate only.

## Adoption conditions added by C016

In addition to C015 requirements, adoption now requires:

1. an explicit distinction between causal-effect identification and latent-partition identification;
2. a bridge theorem from an anchored family of language effects to strict refinement of the residual causal equivalence class;
3. a counterexample showing failure when injectivity or exclusion is removed;
4. fidelity and overlap diagnostics for every language intervention cell;
5. comparison against the public isolated-text-effect estimator where applicable;
6. no claim that a nonzero language effect, shuffle gap or intervention prediction accuracy alone identifies a target.

## Decision on RQ-001

### Decision: NARROWED TO INJECTIVE ANCHORED LANGUAGE-EFFECT SEPARATION — NOT ADOPTED

The existence of a causal language effect is no longer admissible as evidence by itself for latent intervention-target identification. The candidate survives only if a constrained, externally anchored family of language interventions provably separates the residual non-language causal abstractions.

No experiment or architecture is authorised by this result.

## Resource accounting

This cycle is theory, primary-literature and official-code audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: prior-art refinement, theorem/assumption comparison and effect-versus-partition counterexample
- isolated language effect as partition-identification evidence: rejected
- official code: found, but classified as effect-estimation code rather than latent-partition baseline
- RQ-001: narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
