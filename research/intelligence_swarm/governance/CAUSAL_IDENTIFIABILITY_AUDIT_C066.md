# Causal Identifiability Audit C066

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- C responsibility: determine whether joint identification of raw-language equivalence and a latent intervention-target partition is open relative to prior work and identifiable under the declared observations.
- No new architecture.
- No extension of legacy A–E toy mechanisms.
- No novelty, intelligence-principle, or capability-progress claim.
- This run completes theorem/assumption comparison, prior-art-matrix refinement, and an identifiability/implementability counterexample.
- Numerical reproduction is not started.

## Decision-relevant question

C065 proposed AP001 as a positive finite-partition path. AP001 assumes that each unknown target block receives a distinct independently frozen anchor signature and that, for each language class, the signature of its denoted target is observed.

C066 audits whether this is a codebook-independent observation law or whether it supplies the disputed cross-system correspondence in another form.

## Primary prior-art comparison

Gresele et al., **“The Incomplete Rosetta Stone problem: Identifiability results for Multi-view Nonlinear ICA”**, UAI 2020, studies recovery of a common latent source from multiple sufficiently different noisy nonlinear views.

Primary source:

- PMLR: https://proceedings.mlr.press/v115/gresele20a.html
- Paper: http://proceedings.mlr.press/v115/gresele20a/gresele20a.pdf

The paper proves that joint multi-view observations can identify a shared latent source under explicit structural assumptions even though each view alone is non-identifiable. This is relevant because AP001 also attempts to align two separately recovered systems through an additional view.

The crucial difference is:

- multi-view nonlinear ICA derives alignment from a joint stochastic law and assumptions on the corruptions;
- AP001 A4–A6 assign every target a unique signature and expose the signature of the denoted target for every language class.

Therefore AP001 does not currently establish that an unlabelled third view induces the cross-system correspondence. It assumes access to a target-indexed signature channel whose observation is already paired with the denotation relation.

## Assumption decomposition

AP001 requires:

- A2: recover target quotient `P` up to permutation;
- A4: an injective signature `b(p)` for every `p in P`;
- A5: the signature binding is independent of semantic codebooks;
- A6: for every `q in Q`, observe `b(d(q))`.

The proof then matches the signature observed with `q` to the same signature attached to `p`.

This implication is mathematically valid, but its research content depends entirely on whether A4–A6 can be implemented without already possessing target-indexed access or the denotation pairing.

## Target-binding dichotomy

Consider the instruction in AP001:

> bind anchor column `j` to target block `p_j` through an independently enumerated physical or simulator I/O channel.

Exactly one of the following cases holds.

### Case 1 — target-indexed channel access exists

The experimenter can address a channel that is known to manipulate or read exactly one target block `p_j`.

Then the channel serial is an externally supplied target identity. Replacing a semantic name with a serial number removes human-readable semantics but does not remove target supervision. The channel-to-target map is a codebook sufficient to orient the recovered target permutation.

Under this case, AP001 is a valid supervised or instrumented matching protocol, but not a solution to unknown-target joint identification.

### Case 2 — target-indexed channel access does not exist

The experimenter only has unlabelled interventions or observations whose affected latent target is unknown.

Then a column cannot be bound to a particular latent block before recovering `P`. The observed response is associated only with an unlabelled intervention environment, not with a known `p_j`. A4 may define signatures over environments, but A6 cannot expose `b(d(q))` without an additional law that links the utterance class to the same latent block.

Under this case, the AP001 proof cannot be executed as written.

Hence the protocol faces a dichotomy:

> if the binding is implementable, it supplies target identity; if target identity is genuinely unknown, the required binding is not available.

## Circularity counterexample

Let `P={p_1,p_2}` be recovered only up to permutation and let two external channels have serials `c_1,c_2` with distinct signatures.

Two observational models are possible:

- Model A: `c_1 -> p_1`, `c_2 -> p_2`, and `d(q_1)=p_1`, `d(q_2)=p_2`;
- Model B: `c_1 -> p_2`, `c_2 -> p_1`, and `d(q_1)=p_2`, `d(q_2)=p_1`.

If the channel-to-target binding is not independently observed, both models preserve:

- the separately recovered quotient `P`;
- the set of channel signatures;
- all unlabelled intervention distributions;
- all language-side observations;
- the multiset of signature-bearing transcripts.

They differ only in the disputed channel/target/language correspondence. Distinct signatures do not eliminate the permutation because the signature columns themselves can be permuted with the unknown channel-to-target binding.

To distinguish the models, the protocol must observe which latent target each serial addresses or must observe a paired consequence tying `q` and the same target to a fixed external measurement. The first supplies target identity; the second is the still-unproved cross-system observation law.

## A6 is stronger than denotation identification

A6 states that for every language class `q`, the protocol exposes the signature of `d(q)`.

For injective `b`, the value `b(d(q))` uniquely specifies the target block. Therefore A6 is not merely a weak anchor assumption; together with A4 it is an encoded target label for every language class.

The proposition then proves:

> if every language class is observed with a unique externally indexed target identifier, the language-to-target map can be recovered.

This is correct but does not answer whether raw language equivalence and an unknown intervention partition can be jointly identified from non-codebook observations.

## Prior-art matrix refinement

| Line of work | Joint observation supplied | Main guarantee | Residual issue for RQ | AP001 relation |
|---|---|---|---|---|
| Multi-view nonlinear ICA / Incomplete Rosetta Stone | paired noisy views of one common latent source | shared latent recovery under structural assumptions | semantic denotation and target ontology need not be fixed | genuine joint-view identifiability route; assumptions must be mapped to language/causal data |
| Unknown-target CRL | multiple observational/interventional environments | latent coordinates/targets up to declared transformations | external meaning and language correspondence remain free | candidate non-language baseline for `P` |
| Language dynamics / assertion models | text sequences or language-internal relations | language-internal quotient or predictive structure | external target correspondence remains free | candidate language baseline for `Q` |
| AP001 as written | unique target signature plus `b(d(q))` paired to each language class | exact lookup of `d` | target-indexed binding is supplied or A6 is unavailable | supervised oracle upper bound, not codebook-independent joint identification |

## Consequence for the C065 theorem

Proposition AP001.1 remains logically true as a conditional matching lemma. It should not be described as establishing a codebook-independent positive path unless an implementable observation law is provided that satisfies A4–A6 without target-indexed access and without already pairing language classes to target signatures.

The current protocol does not provide such a law.

## Required replacement criterion

A positive program must replace A6 with a generative observation assumption that is weaker than the object to be identified. For example, it would need to specify a jointly observed random variable `Z` such that:

1. `Z` is generated without reading target IDs, parser slots, semantic labels, or `d`;
2. the joint law of language, intervention trajectories, and `Z` is empirically observable;
3. under explicit assumptions, every observationally equivalent model has the same `Q`, `P`, and `d` up to declared trivial equivalence;
4. the proof does not condition on `b(d(q))` or any injective surrogate for the unknown target label;
5. paired-view assumptions are compared directly with multi-view identifiability literature.

Until such a replacement exists, an AP001 experiment would test whether a model can use a supplied unique identifier, not whether denotation is discovered.

## Baseline consequence

The next empirical step must not spend resources on AP001 as a claimed identification experiment. AP001 may be retained only as:

- a leaked-oracle positive control;
- an upper bound on matching accuracy after explicit target instrumentation;
- a test of metric and pipeline correctness.

Public baseline reproduction remains required, but it should first target separate recovery of `Q` and `P` or a genuine paired multi-view baseline. No new architecture is permitted.

## Decision

**AP001 REJECTED AS A CODEBOOK-INDEPENDENT IDENTIFICATION SOLUTION; RETAINED ONLY AS AN INSTRUMENTED ORACLE CONTROL. RQ-001 REMAINS NOT ADOPTED.**

The candidate RQ is narrowed to:

> Is there an empirically available joint language/intervention observation law, not containing target-indexed channels or injective surrogates of `d(q)`, whose assumptions eliminate the residual language/target automorphism and merge/split alternatives? If so, can that law be connected to existing multi-view identifiability results and reproduced with public baselines?

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Identifiability/implementability counterexample: completed.
- AP001 conditional lemma: logically valid but not sufficient for the target RQ.
- AP001 codebook-independent claim: rejected.
- AP001 allowed future role: instrumented oracle positive control only.
- Public baseline reproduction: not started in this run.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- Experiment: not started.
- Model size, RSS, runtime, and three seeds: not yet applicable.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
