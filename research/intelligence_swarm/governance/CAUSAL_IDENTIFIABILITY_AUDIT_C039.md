# Causal Identifiability Audit C039

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced.

## Primary work newly audited

### Causal Abstraction Learning based on the Semantic Embedding Principle

Gabriele D'Acunto, Fabio Massimo Zennaro, Yorgos Felekis, and Paolo Di Lorenzo. International Conference on Machine Learning, 2025.

Primary records:

- PMLR: https://proceedings.mlr.press/v267/d-acunto25a.html
- arXiv: https://arxiv.org/abs/2502.00407
- OpenReview: https://openreview.net/forum?id=J16AIOkjjY
- official code: https://github.com/SPAICOM/calsep
- audited official-code commit: `22492babeff3e8d6aac6c02e282cb84a023f4bf6`

The paper studies learning a causal abstraction between low- and high-level causal models when the structural causal models themselves are inaccessible, interventional data is unavailable, and samples across abstraction levels are not aligned. It introduces the semantic embedding principle (SEP): the high-level causal knowledge can be embedded into the low-level space and then reconstructed perfectly by the abstraction map.

For the implemented linear case, the abstraction is represented by a matrix on the Stiefel manifold. The learning objective aligns low- and high-level observational distributions, instantiated for Gaussian measures with Kullback–Leibler divergence. Three Riemannian-optimization methods are presented and evaluated on synthetic and brain data under different amounts of prior abstraction structure.

## Assumption, observation, and guarantee comparison

The audited setting assumes or uses:

1. separately observed low-level and high-level distributions;
2. known low- and high-level variable dimensions;
3. at least partial prior knowledge about the abstraction structure;
4. a constructive abstraction whose endogenous map admits a measurable right inverse;
5. for the implemented case, a linear abstraction matrix constrained to a Stiefel manifold;
6. Gaussian low- and high-level observational measures;
7. KL divergence as the distribution-alignment objective;
8. no interventional data and no aligned sample pairs;
9. direct access to high-level observations rather than discovery of a high-level language partition from raw utterances.

The semantic embedding principle guarantees high-level reconstruction after embedding and re-abstraction. It does **not** guarantee recovery of the unique ground-truth abstraction map. The paper explicitly states that zero distribution distance need not make the optimal abstraction coincide with the true causal abstraction and that the optimum is not unique. In the linear Gaussian objective, both `V` and `-V` are immediate equivalent solutions.

Accordingly, this work establishes a prior-art boundary for RQ-001:

- learning a distribution-preserving map between supplied low- and high-level causal representations is existing work;
- calling an alignment objective “semantic” does not identify the semantics of raw utterances;
- perfect reconstruction of an already supplied high-level distribution does not identify a unique low-to-high denotation;
- observational distribution alignment alone does not eliminate abstraction-map automorphisms;
- partial prior knowledge about abstraction support is materially different from discovering raw-language equivalence and latent intervention-target blocks jointly.

The work does **not** jointly identify:

- an unknown equivalence relation over raw utterances;
- a latent intervention-target partition under unknown target identity;
- a unique denotation from utterance classes to latent target blocks;
- a high-level language ontology not separately observed during training;
- a unique abstraction under all distribution-preserving rotations, signs, permutations, or within-block transformations;
- a language contribution that cannot be reconstructed from supplied high-level observations or prior abstraction support.

## Official-code audit

PMLR and OpenReview link `SPAICOM/calsep` as the official implementation. At audited commit `22492babeff3e8d6aac6c02e282cb84a023f4bf6`, the repository contains:

- `src/` implementations of the proposed algorithms;
- `example.ipynb` for full-prior and partial-prior cases;
- saved result data in Parquet format;
- `environment.yml`;
- an MIT license.

The environment manifest names Python, NumPy, SciPy, Matplotlib, Seaborn, pandas, NetworkX, Jupyter, Autograd, PyLops, PyProximal, scikit-learn, PyArrow, SCIP, CVXPY, CVXOPT, and Pymanopt. Package versions are not pinned. The repository has only two commits, no release, no lockfile, no container digest, no seed manifest, no expected result checksums, and no resource profile.

Classification:

> **official public code verified; paper-specific immutable R0 reproduction package not yet established**

No experiment was started in this cycle. A later reproduction must pin the audited commit, resolve and freeze all transitive package versions, identify notebook cells corresponding to each reported table or figure, set three seeds, and save model/object bytes, peak RSS, wall time, CPU inference or transform latency, raw logs, outputs, and checksums.

## Prior-art boundary added to the novelty matrix

The following claims are excluded from the novelty space:

- learning a causal abstraction from unaligned observational distributions;
- learning linear constructive abstractions by distribution matching;
- using a right-inverse embedding/reconstruction constraint for causal abstraction;
- optimizing a linear abstraction on a Stiefel manifold;
- using KL divergence between low- and high-level Gaussian measures;
- exploiting partial prior knowledge of the abstraction support;
- using a human-readable high-level representation as if its supplied semantics had been discovered;
- treating perfect high-level reconstruction as evidence that a unique denotation was identified;
- treating a low distribution-alignment loss, task success, next-state prediction, action accuracy, or language-shuffle gap as direct recovery of raw-language equivalence and a latent target partition.

## Identifiability counterexample: perfect semantic embedding with nonidentified denotation

Let `X` be a low-level state representation and `H` a separately observed high-level representation. Suppose a linear abstraction `V^T` satisfies SEP and perfectly aligns the distributions:

\[
H \overset{d}{=} V^T X,
\qquad
V^T V = I.
\]

Assume raw utterances `U` are encoded into the supplied high-level space through an unknown map `e`, and a denotation map associates utterance classes with high-level or intervention-target blocks.

Even before considering language, the paper's own objective admits nonunique abstractions. In the simplest case, `V` and `-V` preserve the same Stiefel constraint and can yield the same Gaussian covariance-level objective. More generally, if a transformation `R` preserves the high-level distribution and the allowed prior support, define

\[
V' = V R,
\qquad
H' = R^T H.
\]

Now transform consistently:

- the high-level decoder;
- the utterance encoder `e`;
- the utterance equivalence labels;
- the target-block labels;
- the denotation map.

The two models can preserve:

- the low-level observational distribution;
- the supplied high-level observational distribution;
- the SEP reconstruction equation;
- the KL alignment objective;
- prior-support constraints;
- all reconstructed high-level samples;
- downstream next-state prediction;
- action accuracy and task success;
- utterance likelihood and paraphrase accuracy;
- language-shuffle gaps that depend only on the aligned high-level statistic.

Nevertheless, the raw-utterance equivalence relation, intervention-target partition, and semantic denotation can differ.

A second ambiguity is more direct. If two distinct utterance classes map to the same supplied high-level variable or abstraction fibre, all SEP and distribution-alignment observations are unchanged whether those utterances are treated as one equivalence class or two. The observational abstraction objective contains no information that distinguishes extensional aliasing on the supplied high-level representation from genuine raw-language synonymy.

Therefore:

> Perfect reconstruction of a supplied high-level causal distribution under the semantic embedding principle does not identify raw-language equivalence, a fine-grained latent intervention-target partition, or a unique denotation between them.

The term “semantic embedding” denotes a structural reconstruction principle; it is not an anti-recoding theorem for natural-language meaning.

## Necessary boundary for a surviving language contribution

Let `S_SEP` contain all information available to the strongest SEP-style baseline:

- complete low-level observational distribution;
- complete supplied high-level observational distribution;
- variable dimensions;
- partial abstraction-support prior;
- the admissible abstraction family;
- the fitted abstraction and reconstruction maps;
- state, action, reward, outcome, environment identity, and completed trajectories;
- all downstream predictions derived from the supplied high-level representation.

Let `P_residual` be the intervention-target distinction left after conditioning on `S_SEP`. A necessary information condition for a language-specific contribution is

\[
I(P_{residual};L\mid S_{SEP})>0.
\]

This is insufficient by itself. The language law must be fixed before fitting and must remove every simultaneous transformation of the abstraction coordinates, utterance classes, target blocks, encoder, decoder, and denotation map that preserves the complete observational and task law. The anchor cannot merely provide the same high-level observations, variable names, abstraction support, environment IDs, rewards, outcomes, or completed trajectories already present in `S_SEP`.

## Updated decision for RQ-001

**NARROWED BEYOND SEMANTIC-EMBEDDING CAUSAL ABSTRACTION LEARNING — NOT ADOPTED**

The only remaining candidate is:

> After applying the strongest observational causal-abstraction learner with supplied high-level distributions and partial abstraction priors, can a preregistered externally fixed language law jointly identify raw-utterance equivalence and a residual latent intervention-target partition while eliminating every abstraction/denotation automorphism that preserves the complete low-level, high-level, interaction, and task law?

Adoption now requires at minimum:

1. a formal distinction among supplied high-level variables, learned abstraction coordinates, raw utterances, inferred utterance classes, and latent intervention-target blocks;
2. an immutable reproduction of `SPAICOM/calsep` at the audited commit with a fully frozen environment and three-seed manifest;
3. explicit computation of the equivalence class of abstraction maps admitted by the SEP objective and benchmark priors;
4. a concrete pair of models with identical low/high observational laws and task behavior but different utterance and target partitions;
5. language information unavailable from supplied high-level samples, prior abstraction support, state, action, reward, outcome, environment identity, and completed trajectories;
6. a denotational anchor fixed before model fitting;
7. proof that the residual joint automorphism group is nontrivial without the anchor and trivial with it;
8. direct recovery metrics for the raw-utterance partition, latent target partition, and denotation, rather than reconstruction or task success alone;
9. language-blind, state-only, high-level-label-shuffle, target-label-shuffle, outcome-shuffle, and abstraction-prior-shuffle controls on identical instances;
10. preregistration before any new architecture or mechanism is authorized.

## Status

- RQ-001: further narrowed; not adopted
- observational semantic-embedding causal abstraction learning: prior art
- official public code: verified
- immutable public baseline reproduction: not started
- raw-language equivalence identification: not established
- latent target partition identification: not established
- semantic joint identification: not established
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
