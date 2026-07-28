# Causal Identifiability Audit C089

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, and (d) an identifiability counterexample.
- Numerical execution is not started; model size, peak RSS, wall time, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C088 replaced forced point completion with the joint identified set of `(Q,P,d)` and required any language-side exclusion of a compatible target completion to be justified by an explicit cross-system observation or assumption.

The question for C089 is:

> Can language dynamics pretraining identify the raw-language quotient `Q` strongly enough to shrink the joint identified set, and does an anchor-word or separable-topic guarantee provide any identification of the external target quotient `P` or denotation `d`?

## Primary prior art

### Separable topic models and anchor words

Arora et al. give a practical polynomial-time topic-model algorithm with provable guarantees under a separability assumption. In its canonical form, each latent topic has at least one anchor word whose positive probability is exclusive to that topic. The word co-occurrence geometry then exposes topic-specific extreme points, allowing the topic matrix to be recovered up to the usual latent-topic permutation under the stated population and robustness assumptions.

This establishes a strong positive result for language-internal latent decomposition. It rules out any claim that identifying a latent language partition from raw co-occurrence dynamics under explicit anchor/separability assumptions is itself unresolved.

### Anchor-free correlated topic identification

Huang, Fu, and Sidiropoulos, and the later TPAMI treatment by Fu et al., show that anchor words are not the only route to topic identifiability. Under alternative second-order moment and sufficiently scattered/geometric conditions, correlated topic factors can be identifiable without one exclusive anchor word per topic.

Therefore the relevant boundary is not “language dynamics cannot identify latent structure without labels.” It can, under structural assumptions on the topic/simplex geometry and the data-generating law.

### Testability of the anchor-word assumption

Freyaldenhoven, Ke, Li, and Montiel Olea show that the existence of an anchor-word factorization is statistically testable rather than merely a harmless normalization. Their characterization distinguishes observable matrices that admit separable factorizations from those that do not, and they report rejection of the anchor-word null in one empirical corpus.

This matters for governance: an anchor-word assumption must be preregistered and audited against the observed language law. It cannot be introduced after seeing a convenient clustering and then treated as identification.

### Practical public implementations

The ICML 2013 paper publishes paper and supplementary material through PMLR. The EMNLP-IJCNLP 2019 Rectified Anchor Word work publishes an attachment with practical implementation materials and audits vocabulary curation, rectification, inference, and correlated-topic behavior.

These materials are public prior-art references for a language-only `Q` baseline. This run did not establish a paper-specific immutable Git commit with a hermetic three-seed command, so no executable canonical baseline is promoted yet.

## Theorem/assumption/guarantee comparison

| Object | Typical observations | Key identifying assumptions | Guarantee | Not guaranteed |
|---|---|---|---|---|
| Separable anchor-word topic model | document-word or word co-occurrence law | known/fixed topic count or compatible selection rule; separability; sufficient sampling; nondegenerate topic geometry | topic-word factors / language latent classes up to topic permutation and stated approximation error | external physical target identity, intervention partition, denotation |
| Anchor-free correlated topic model | second-order word moments | sufficiently scattered/geometric conditions; model correctness; rank/nondegeneracy | topic factors up to model symmetries | external semantic orientation or target binding |
| Anchor-word test | observable nonnegative matrix / corpus moments | declared rank/nonnegative-rank conditions and sampling model | reject or retain compatibility with separability | proof that an accepted anchor corresponds to a real-world intervention target |
| C087–C088 target object | controlled action/consequence law | complete point model or structural equalities for merge; explicit observation/assumption set | exact full-consequence quotient or its identified set | language-target coupling without a cross-system law |

The guarantees are therefore compositional but not interchangeable:

1. language dynamics may identify a latent language decomposition `Q` up to permutation;
2. controlled causal observations may identify an exact target quotient `P`, or only a set of compatible `P` values;
3. neither result alone aligns the two latent coordinate systems;
4. `d` requires a cross-system law that is not invariant under independent or joint relabelings.

## Proposition C089.1: language-internal point identification does not imply joint grounding

Assume the population language law identifies `Q` pointwise up to a permutation `pi_Q` by a valid separable or anchor-free topic theorem. Assume the controlled world law identifies `P` pointwise up to a permutation `pi_P` by an exact quotient theorem.

If the observed joint data contain no cross-system statistic whose law changes when `pi_Q` and `pi_P` are varied independently, then the denotation map `d : Q -> P` is not point identified.

Proof sketch:

1. Let one compatible model use denotation `d`.
2. For any permutation `sigma` of `P`, construct a second model with denotation `d' = sigma o d` and relabel the target-side latent representation, actuator bookkeeping, decoder, and evaluator consistently.
3. The marginal language law is unchanged because `Q` and its topic factors are unchanged.
4. The controlled world law is unchanged because the target-side quotient is changed only by an allowed latent permutation.
5. With no observed cross-system statistic fixing the relative alignment, both models generate the same declared observations but disagree on `d`.
6. Hence language-internal and target-internal point identification do not yield joint point identification.

This is a theorem/assumption boundary, not a new intelligence principle.

## Counterexample 1: an anchor word is not an external target anchor

Let language have two identifiable topics:

- topic `q1` has exclusive anchor word `alpha`;
- topic `q2` has exclusive anchor word `beta`.

Let the world have two exact target blocks `p1,p2` with distinct complete controlled laws. The following models both satisfy perfect language separability and perfect target identification:

- model A: `q1 -> p1`, `q2 -> p2`;
- model B: `q1 -> p2`, `q2 -> p1`.

All language-only co-occurrences, anchor tests, topic-recovery scores, target-only interventions, and target quotient metrics are identical. The word `alpha` is an anchor for a language topic, but nothing in the separability theorem states that it is an instrumented anchor for `p1` rather than `p2`.

Therefore:

> A language anchor fixes a vertex of the language simplex; it does not fix the orientation of that simplex relative to the external causal target quotient.

## Counterexample 2: topic splitting can be language-real but target-irrelevant

Suppose a corpus contains two perfectly separable topics corresponding to two stable discourse regimes:

- formal instructions using `alpha`;
- informal instructions using `beta`.

Both regimes refer to the same physical intervention target and induce the same complete controlled law. A correct topic model should recover two language components, while the exact full-consequence target quotient contains one block.

If the evaluation forces a bijection between recovered language topics and target blocks, it will falsely convert register/style variation into distinct denotations. Thus even exact `Q` recovery does not imply that `Q` and `P` have the same cardinality or that `d` is bijective.

## Counterexample 3: one language topic can denote multiple context-conditioned targets

Suppose one identifiable topic uses the same anchor distribution for utterances such as “activate it,” while the actual target is resolved by a nonlinguistic context variable `c` observed in the interaction history. The same language topic denotes `p1` when `c=0` and `p2` when `c=1`.

The language-only quotient is correctly one block, but a map `d : Q -> P` is misspecified. The correct object is a context-indexed relation `d(q,c)` or a relation over richer language-history classes.

Therefore a claimed failure of joint identification may be caused by an incorrect functional form, not only insufficient data. The map, relation, context domain, and polysemy assumptions must be preregistered.

## Counterexample 4: passing an anchor-assumption test does not validate grounding

Suppose the observable language matrix passes a valid separability test and the topic estimator recovers stable factors. This excludes some nonseparable language models, thereby shrinking the `Q` side of the identified set.

It does not exclude either of two joint models that share the same language factors and target factors but swap the relative `Q`–`P` correspondence. Therefore a successful assumption test can support language-side point identification while leaving every denotation permutation compatible.

The governance consequence is:

- test language assumptions for the claim they actually support;
- do not count an accepted language factorization as cross-system evidence;
- separately preregister the observation law used to exclude denotation permutations.

## Implication for language dynamics pretraining

Language dynamics pretraining can legitimately contribute in three ways:

1. recover or narrow a language-side quotient `Q` under audited generative assumptions;
2. estimate predictive language state sufficient for future-token or discourse dynamics;
3. propose candidate cross-system queries that are subsequently validated by independent controlled observations.

It cannot, by language likelihood alone:

- decide whether two linguistic modes denote one or two physical targets;
- determine the orientation of `Q` relative to `P`;
- turn an unresolved target merge into a certified separation;
- convert semantic plausibility into `must-denote` status;
- justify a bijection between language topics and intervention blocks.

Any use of pretrained embeddings, topic assignments, or language-model confidence to remove a `(Q,P,d)` completion must be recorded as an explicit linking assumption or be backed by an observed paired/interventional consequence.

## Admissible cross-system evidence classes

C089 narrows the remaining positive path to observations that can break the relative permutation without directly exposing target IDs. Candidate classes are admissible only if their law is specified before semantic labels and is independently observable:

- paired episodes in which raw language and controlled consequence are jointly observed;
- repeated interventions where utterance-conditioned action selection changes a preregistered physical response distribution;
- a third view with conditional-independence/rank conditions sufficient for shared latent-class identification;
- context perturbations that preserve language topic identity while selectively changing one target response;
- cross-environment invariances that constrain one relative alignment but not its permutations.

Each candidate still requires a theorem or countermodel audit. Listing it does not establish identifiability.

## Prior-art matrix update

| Prior art / object | What it establishes | What remains outside its guarantee | C089 classification |
|---|---|---|---|
| Arora et al. separable topic model | practical recovery of topic factors under anchor-word/separability assumptions | external target quotient and denotation orientation | language-side `Q` identification prior art |
| Fu/Huang/Sidiropoulos anchor-free topic identification | topic recovery under alternative second-order geometric conditions | language-world coupling | language-side `Q` identification prior art |
| Freyaldenhoven et al. anchor testability | separability/anchor compatibility is statistically testable | whether a language anchor denotes a particular causal target | assumption-audit prior art |
| Rectified Anchor Word implementation materials | practical public topic inference pipeline | immutable hermetic LBQ001 baseline and `Q/P/d` metrics | public baseline candidate, not pinned |
| C088 joint identified set | only invariant `must/cannot/may` assertions are identified under incomplete evidence | concrete leakage-free linking law | governing joint-identification contract |

## Public-code audit

Public materials were confirmed for:

- the PMLR ICML 2013 paper and supplementary material;
- the ACL Anthology EMNLP-IJCNLP 2019 paper and attachment for Rectified Anchor Word inference;
- independent open implementations of anchor-based topic inference.

This run did not promote an implementation to canonical baseline because the following are not yet fixed together:

- author-controlled immutable repository commit;
- exact corpus preprocessing and vocabulary curation;
- topic-count selection rule;
- population/separability diagnostic;
- deterministic or three-seed manifest;
- serialized model size, peak RSS, and wall time;
- direct language-relation metrics for `must-equivalent / must-distinct / unresolved`;
- a firewall preventing topic labels or anchor words from being treated as target IDs.

No numerical reproduction was started.

## Decision

> **NARROWED BEYOND LANGUAGE-INTERNAL TOPIC IDENTIFIABILITY: ANCHOR-WORD, ANCHOR-FREE, AND TESTABLE-SEPARABILITY RESULTS CAN IDENTIFY OR AUDIT A RAW-LANGUAGE LATENT DECOMPOSITION UNDER EXPLICIT ASSUMPTIONS, BUT THEY DO NOT IDENTIFY THE EXTERNAL TARGET QUOTIENT OR THE RELATIVE DENOTATION ALIGNMENT. A LANGUAGE ANCHOR IS NOT A WORLD ANCHOR, AND LANGUAGE DYNAMICS MAY SHRINK THE JOINT IDENTIFIED SET ONLY THROUGH AN EXPLICIT CROSS-SYSTEM OBSERVATION OR LINKING ASSUMPTION — RQ-001 NOT ADOPTED.**

## Consequence for RQ-001

The remaining candidate RQ is narrowed to:

> After separately identifying or partially identifying a language quotient `Q` and the exact full-consequence controlled target quotient `P`, which preregistered joint observation laws identify the relative alignment or context-indexed denotation relation, and which apparent language anchors merely identify language-internal topics while leaving target permutations, cardinality mismatch, synonymy, register variation, and polysemy unresolved?

Novelty is not established. Language-side latent identification and its assumption tests are prior art. A publishable positive result would require a leakage-free joint observation theorem or a sharp joint identified-set construction that is not already implied by multi-view latent-class, topic-model, or causal partial-identification theory.

## Next gate

1. Add a machine-readable language-side relation contract to LBQ001: `must-equivalent`, `must-distinct`, and `unresolved`, without forcing topic assignments into target blocks.
2. Audit paired multi-view identification results against the exact observation law available in `benchmarks/grounded_causal/`, especially conditional-independence, rank, and context assumptions.
3. Pin one author-controlled public language baseline only after preprocessing, topic-count, assumption test, and resource manifest are fixed.
4. Construct no new architecture. If a finite exact benchmark is used, it must enumerate joint completions rather than add another legacy toy mechanism.
5. Begin numerical work only after seeds `17 / 29 / 43`, model size, peak RSS, wall time, commands, commits, dataset digest, and raw-result digest are fixed.

## Current status

- prior-art matrix refinement: complete;
- theorem/assumption comparison: complete;
- identifiability counterexamples: complete;
- language-side latent topic identification: existing prior art under explicit assumptions;
- anchor-word assumption testability: existing prior art;
- language anchor as external target anchor: rejected;
- language-only orientation of `d`: not identified;
- cardinality equality and bijective `d`: not justified;
- public numerical reproduction: not started;
- new architecture: none;
- legacy A–E toy mechanism: none added;
- RQ-001: narrowed, not adopted;
- novelty, intelligence-principle, and capability-progress claims: none.

## Sources

- https://proceedings.mlr.press/v28/arora13.html
- https://arxiv.org/abs/1212.4777
- https://arxiv.org/abs/1611.05010
- https://pubmed.ncbi.nlm.nih.gov/29993625/
- https://www.philadelphiafed.org/the-economy/monetary-policy/on-the-testability-of-the-anchor-words-assumption-in-topic-models
- https://aclanthology.org/D19-1504/
