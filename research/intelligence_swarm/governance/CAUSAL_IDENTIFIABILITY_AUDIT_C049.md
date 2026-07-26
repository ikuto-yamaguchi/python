# Causal Identifiability Audit C049

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced. No experiment was started.

## Primary work newly audited

### Isolated Causal Effects of Natural Language

Victoria Lin, Louis-Philippe Morency, and Eli Ben-Michael. ICML 2025.

Primary records:

- PMLR: https://proceedings.mlr.press/v267/lin25k.html
- arXiv: https://arxiv.org/abs/2410.14812
- OpenReview: https://openreview.net/forum?id=Z0jnz149L1
- official code: https://github.com/torylin/isolated-text-effects
- audited official commit: `2848b78b344c33074f902aab1c8d89e27ce3597a`
- audited README blob: `cdb4955d55030b28ee264a134b55e2d8c303498c`

The paper formalizes the isolated causal effect of a focal language-encoded intervention on an external outcome while averaging over a common target distribution of all non-focal language. It develops identification by transporting the non-focal language distribution, a doubly robust estimator, and omitted-variable-bias sensitivity measures for fidelity and overlap.

This work is directly relevant because it is stronger than ordinary predictive grounding: it estimates a causal effect of a language attribute on a non-language outcome. It therefore provides an important boundary for claims that external outcome sensitivity is itself sufficient to discover language semantics.

It does **not** infer the focal intervention mapping from raw language. The mapping `a(X)` from text to the binary focal attribute is assumed known as a codebook function. It also does not discover an unknown latent intervention-target partition, an utterance equivalence relation, or a denotation between the two.

## Assumption, observation, and guarantee comparison

### Objects and observations in the paper

Let:

- `X` be a complete text;
- `Y(X)` be an individual's potential outcome after reading `X`;
- `a(X) in {0,1}` be a known focal language attribute;
- `a^c(X)` be all non-focal language;
- `P*` be a chosen target distribution over non-focal language.

The isolated effect is the average difference between `Y(a=1, a^c)` and `Y(a=0, a^c)` under the same `P*` distribution for `a^c`.

The paper assumes:

1. **Consistency**: the observed outcome equals the potential outcome associated with the observed focal and non-focal text;
2. **No unmeasured confounding conditional on non-focal language**: all confounding between the known focal attribute and outcome is captured by `a^c(X)`;
3. **Overlap**: both focal-attribute values have nonzero conditional probability across the relevant non-focal-language support;
4. a **known codebook function** `a(X)` defining the focal intervention;
5. access to, or a defensible definition of, the target non-focal distribution `P*`;
6. sufficiently accurate nuisance estimates for the treatment propensity and outcome model, with doubly robust protection when one of the two is correct.

Under these assumptions, the isolated effect is identified from observed text-outcome data using importance weighting and an outcome model. The paper further supplies sensitivity analysis for bias introduced by lossy approximations of the non-focal text.

### What is guaranteed

The guarantee concerns the scalar or low-dimensional causal estimand associated with a **predefined** focal attribute. It can justify statements of the form:

> Holding the distribution of non-focal language fixed to `P*`, changing the known focal attribute from 0 to 1 changes the external outcome by the identified average amount.

It also clarifies when a language representation is inadequate for causal adjustment because omitted non-focal information induces bias or poor overlap.

### What is not guaranteed

The framework does not identify:

- which distinctions in raw text should constitute focal interventions;
- an unknown equivalence relation over raw utterances;
- whether two utterance forms are synonyms or distinct but effect-equivalent meanings;
- an unknown latent partition of environment intervention targets;
- the number of target blocks;
- a denotation map from utterance classes to latent intervention blocks;
- semantic identity when two candidate language partitions yield the same isolated effect;
- removal of simultaneous recoding of focal labels, utterance classes, target blocks, and outcome mechanisms.

The paper therefore identifies an effect **conditional on a supplied semantic codebook**, not the semantic codebook itself.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded from the novelty space:

- defining causal effects of language attributes on external outcomes;
- isolating a focal language effect by averaging over a common non-focal distribution;
- treating all non-focal language as the adjustment object;
- using importance weighting to transport non-focal language distributions;
- using a doubly robust estimator for a language intervention effect;
- evaluating language representations by outcome fidelity and treatment overlap;
- using omitted-variable-bias sensitivity analysis for language causal estimates;
- comparing IATE- and IATT-style isolated language effects;
- claiming semantic discovery merely because a predefined language attribute has a reproducible external causal effect;
- claiming raw-language equivalence merely because two texts have the same estimated isolated effect.

The surviving novelty candidate must discover a cross-system partition and denotation without receiving the focal semantic attribute as a codebook.

## Theorem/assumption boundary for RQ-001

Define:

- `U`: raw utterance;
- `Q`: unknown equivalence relation over utterances;
- `P`: unknown latent intervention-target partition;
- `d: U/Q -> P`: denotation;
- `Y`: observed external outcome;
- `A_Q(U)`: a candidate language attribute induced by partition `Q`.

The isolated-effect framework starts after a mapping analogous to `A_Q` has already been fixed. RQ-001 instead asks whether `Q`, `P`, and `d` can be inferred jointly.

Even if the isolated effect of every supplied binary attribute is perfectly identified, this does not imply that the supplied attributes are the unique semantic partition. Multiple attribute maps can induce the same propensity, outcome regression, transported estimand, and sensitivity statistics.

A necessary information condition for distinguishing two residual target blocks remains:

\[
I(P_{residual}; U \mid S_{nonlang}, Y) > 0,
\]

where `S_nonlang` contains all legitimate state, action, reward, environment, trajectory, entity, parser, schema, and outcome information.

This condition is not sufficient. The observations must also eliminate every transformation that changes `Q`, `P`, or `d` while preserving all text-outcome distributions and all isolated-effect estimands.

## Identifiability counterexample: identical isolated effects, different semantics

Assume unlimited data and oracle nuisance models. Let two raw utterance forms `u1` and `u2` always occur with the same distribution of non-focal language and induce the same external outcome distribution under every legitimate context.

Construct Model A:

- `u1` and `u2` belong to one equivalence class in `Q_A`;
- that class denotes one latent target block `p`;
- a known focal codebook marks both forms as the same intervention value.

Construct Model B:

- `u1` and `u2` belong to distinct classes in `Q_B`;
- the classes denote distinct latent target blocks `p1` and `p2`;
- `p1` and `p2` are observationally and interventionally aliased under every available environment and outcome channel;
- the supplied focal codebook still maps both forms to the same binary attribute value.

Models A and B preserve:

- the complete observed text distribution;
- the known focal codebook values;
- the propensity score for the focal attribute;
- the outcome regression;
- the IATE and IATT isolated effects;
- the doubly robust estimating equation;
- fidelity and overlap metrics;
- omitted-variable-bias bounds;
- all reader or environment outcomes;
- task success and action accuracy when the policy treats the aliased targets identically.

Nevertheless, `Q_A != Q_B` and the latent target partitions differ. Thus:

> Perfect identification of every isolated causal effect defined by a supplied language codebook does not identify the raw-language equivalence relation, the latent intervention-target partition, or their denotation.

A second symmetry acts directly on the supplied focal label. Let `pi` swap the focal labels 0 and 1, transform the propensity model accordingly, transform the potential-outcome indexing, and reverse the sign convention of the reported effect. The observed data law is unchanged; only the externally chosen interpretation of the label changes. The effect estimand becomes semantically meaningful only because the codebook fixes what label 1 denotes before estimation.

Therefore an estimated language-to-outcome causal effect is evidence for a causal contrast **relative to a predefined intervention**, not evidence that the intervention or its semantic partition was discovered from raw language.

## Consequence for interactive language grounding

Interactive outcomes can strengthen grounding evidence when utterances cause different trajectories, rewards, or human responses. However, the isolated-effect result shows that this evidence must be interpreted in two separate stages:

1. define or discover the candidate language intervention;
2. estimate its causal effect while controlling non-focal language.

The ICML framework addresses stage 2 under a known codebook. It cannot validate stage 1 when the partition itself is learned from the same outcomes. Using a learned parser or target classifier as `a(X)` and then estimating a strong isolated effect risks circularity: the semantic partition used to define the treatment is treated as ground truth by the estimator.

For RQ-001, a valid benchmark must therefore separate:

- codebook-free partition discovery;
- isolated-effect estimation conditional on a frozen discovered partition;
- held-out falsification of the partition and denotation;
- comparison against alternative partitions with the same isolated effects.

## Official-code and reproducibility audit

The paper-specific official repository is `torylin/isolated-text-effects`. The audited head commit is:

`2848b78b344c33074f902aab1c8d89e27ce3597a`

The repository README states that all paper experiments are launched by:

- `./run_all_amazon.sh`
- `./run_all_tirzepatide.sh`

The inspected repository state contains paper code and data directories, Python and notebook content, and shell entry points for the two experiment groups.

Reproducibility limitations visible in the inspected public state:

- the README does not document a Python version;
- no lockfile or hash-pinned dependency manifest is documented in the README;
- no container or Nix environment is documented;
- dataset provenance and checksums are not documented in the README;
- exact paper table-to-command mapping is not documented beyond the two aggregate scripts;
- no canonical seed manifest is documented in the README;
- no raw-result checksums, model bytes, peak RSS, or wall-time contract are documented;
- the repository has only four visible commits and no release artifact.

Classification:

> **paper-specific official code and exact commit verified; aggregate experiment entry points are present; immutable dependency, dataset, seed, resource, and checksum contract is not established**

No experiment was started in this cycle. Model size, peak RSS, wall time, CPU latency, and three-seed measurements are therefore not applicable yet.

## Required controls before any adoption

A future joint-identification experiment must include identical domain × seed × instance cells for at least:

1. supplied gold-codebook isolated-effect estimator;
2. discovered-codebook isolated-effect estimator with the partition frozen before outcome fitting;
3. alternative partitions matched for treatment frequency and isolated effect;
4. language-blind unknown-target baseline;
5. state-only, trajectory-only, and outcome-only baselines;
6. random or untrained utterance encoder;
7. utterance-form shuffle preserving outcome and target frequencies;
8. codebook-label permutation;
9. target-block permutation;
10. non-focal-language representation ablations measuring fidelity and overlap;
11. direct recovery of `Q`, `P`, and `d`, not only isolated effect or task success;
12. countermodel pairs with identical isolated effects and different utterance/target partitions;
13. an independently fixed cross-system anchor and an ablation proving that it removes the residual automorphism.

## Updated decision for RQ-001

**NARROWED BEYOND ISOLATED CAUSAL EFFECTS OF PREDEFINED LANGUAGE INTERVENTIONS — NOT ADOPTED**

The surviving candidate is:

> After recovering the strongest non-language intervention partition and controlling all non-focal language needed for valid causal effect estimation, can a codebook-free, preregistered cross-system law jointly discover a residual raw-utterance equivalence relation and residual latent intervention-target partition, distinguish it from every alternative partition with identical isolated effects, and eliminate all utterance/target/denotation recodings without using supplied semantic labels?

Adoption now requires at minimum:

1. formal separation of intervention discovery from effect estimation;
2. exact inventory of every codebook, parser, entity, target, schema, reward, outcome, and trajectory channel;
3. proof that the candidate language intervention is not supplied or reconstructed from gold semantics;
4. direct metrics for utterance partition, target partition, and denotation;
5. countermodels sharing all isolated effects but differing in semantics;
6. held-out interactive interventions that distinguish the candidate partition from matched alternatives;
7. a cross-system anchor fixed before partition and effect fitting;
8. proof of the residual automorphism group before and after the anchor;
9. exact-commit, dependency, split, seed, resource, and checksum manifests before baseline execution;
10. preregistration before architecture or mechanism changes.

## Status

- RQ-001: further narrowed; not adopted
- isolated causal effects of predefined language attributes: prior art under stated assumptions
- causal effect estimation from text-outcome data: prior art
- unknown language-intervention discovery: not provided by the audited work
- raw-language equivalence identification: not established
- latent intervention-target partition identification by language: not established
- semantic joint identification: not established
- paper-specific official code: verified
- exact official commit: pinned
- public baseline reproduction: not started
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
