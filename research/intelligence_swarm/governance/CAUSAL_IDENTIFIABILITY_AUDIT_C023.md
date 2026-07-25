# Causal Identifiability Audit C023

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + identifiability counterexample + public-code availability audit**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, memory mechanism, or branch was introduced.

## Primary work newly audited

### Disentangling Dynamical Systems: Causal Representation Learning Meets Local Sparse Attention

Markus W. Baumgartner, Anson Lei, Joe Watson, and Ingmar Posner. Proceedings of the Fifth Conference on Causal Learning and Reasoning (CLeaR), PMLR 323, 2026. arXiv:2603.14483v2, 2026-06-11.

Primary records:

- PMLR: https://proceedings.mlr.press/v323/baumgartner26a.html
- arXiv: https://arxiv.org/abs/2603.14483
- proceedings PDF: https://raw.githubusercontent.com/mlresearch/v323/main/assets/baumgartner26a/baumgartner26a.pdf

The PMLR and arXiv records do not link a dedicated official implementation repository. Targeted title/code search located only the proceedings repository and third-party paper indexes, not an author-maintained reproduction package. Therefore no public-code reproduction was started in this cycle.

## Exact theoretical boundary relevant to RQ-001

The paper studies deterministic nonlinear Markovian dynamical systems

`x_{t+1} = f(x_t, theta)`

where the system parameter vector `theta` varies across trajectories and must be inferred from raw state trajectories. A trajectory encoder maps a trajectory to latent system parameters; a decoder reconstructs the dynamics from an initial state and those parameters.

The central result identifies the latent parameters up to permutation and element-wise diffeomorphism when the following hold:

1. each initial state and parameter setting induces a unique trajectory, so the trajectory contains enough information to recover the parameterisation;
2. the learned system is observationally equivalent to the ground-truth system up to an invertible parameter representation;
3. the transition model is faithful and Markov with respect to a parameter-to-state-component DAG defined by non-zero Jacobian entries;
4. the relevant state space is path connected;
5. the learned causal graph is no denser than the ground-truth graph;
6. the transition Jacobian varies sufficiently with individual parameters;
7. the parameter-to-state graph satisfies the graphical separation criterion

`for every parameter i: intersection over children a of i of Pa(a) = {i}`.

The paper further strengthens the criterion by replacing one global graph with state-dependent local causal graphs. A parameter can be identified when the intersection of its confounding parent sets across all local graphs reduces to that parameter alone. Hence local state-dependent sparsity can identify parameters even when the union/global graph is too dense.

This is an important non-language identifiability path: raw trajectories and sparse, varying causal influence can already determine a physically meaningful parameter representation without intervention-target labels, language descriptions, or interactive instruction following.

## What this prior art establishes

The following claims cannot be treated as novel contributions of RQ-001:

- learning latent environment or system parameters from raw trajectories without language;
- using action-free or passive transition dynamics to obtain disentangled environment representations;
- arguing that locally varying parameter influence provides stronger identifiability than a global dependency graph;
- using one-step or autoregressive trajectory reconstruction plus sparse causal influence to identify system parameters;
- treating a state-dependent dependency mask as the first route to recover local causal structure;
- treating successful next-state prediction together with sparse parameter-to-state influence as a language-specific grounding result;
- claiming that a language description of masses, damping, elasticity, or other system parameters is required to identify those parameters when the graphical criterion already holds.

## What this prior art does not establish

The paper does not provide:

- a raw-language observation model;
- equivalence classes over utterances or denotations;
- unknown intervention-target partitions induced by linguistic expressions;
- interactive query/answer grounding;
- a theorem jointly identifying language equivalence and a latent target partition;
- an anti-recoding external language anchor;
- guarantees for stochastic, non-Markovian, partially observed, or non-injective trajectory systems outside its assumptions;
- a result that language strictly refines an equivalence class left unresolved by local causal dynamics.

Its latent variables are system parameters governing trajectory dynamics, not semantic classes of raw utterances. Its empirical MCC evaluation uses known ground-truth parameters in synthetic systems and therefore cannot itself establish raw-language denotation.

## Theorem/assumption comparison

| Dimension | Baumgartner et al. 2026 | Current RQ-001 candidate | Remaining burden |
|---|---|---|---|
| Observation | Raw state trajectories with initial states | Raw utterances plus trajectories/interactions | Prove language adds information not measurable from trajectories |
| Latent object | System parameter vector varying across trajectories | Residual intervention-target partition and utterance equivalence | Formally separate dynamical parameters from denotational target classes |
| Dynamics | Deterministic nonlinear Markovian transition model | Potentially stochastic, interactive, partially observed environment | State the weaker/alternative observation model precisely |
| Identifying signal | Sparse parameter-to-state influence, especially local state-dependent graphs | Externally anchored language contrast after strongest non-language baselines | Show the residual symmetry survives local-dynamics CRL and is broken only by language |
| Guarantee | Permutation and element-wise diffeomorphism under graphical and variability assumptions | Joint identification of utterance equivalence and target partition | Supply an equivalence-class reduction theorem and estimator guarantee |
| Intervention metadata | Not required for system-parameter identification | Hidden intervention target associated with language | Explain why the target distinction is not already encoded in local transition influence |
| Evaluation | Reconstruction plus MCC against known synthetic parameters, eight seeds | Prospective task and transfer metrics plus latent-identification diagnostics | Do not infer semantic identification from prediction or MCC alone |

## Prior-art matrix refinement

The novelty matrix must now separate at least four non-language cases before a language claim is admissible:

1. global causal graph sparsity already separates the latent parameters;
2. the global graph fails but state-dependent local graphs separate them;
3. local graphs still leave parameters in a residual equivalence block;
4. trajectories are non-injective, insufficiently variable, disconnected, partially observed, or otherwise outside the theorem assumptions.

Only cases 3 or 4 can potentially motivate an additional language channel. Even there, language is relevant only if it supplies a distinction that is neither a deterministic nor statistically recoverable function of the full local transition process.

The following candidate claims are rejected as too broad:

- language dynamics pretraining is novel because it learns environment parameters before instruction following;
- language is needed to disentangle system parameters from transitions;
- local causal influence discovered through prediction is evidence of raw-language grounding;
- a language-conditioned parameter probe establishes a jointly identified utterance/target partition;
- superior next-state prediction after language pretraining proves semantic identifiability.

## Counterexample: language can name already identifiable dynamics without refining the causal equivalence class

Let `T` denote the complete trajectory distribution and let `theta = r(T)` be a system-parameter representation already identified up to permutation and element-wise diffeomorphism by the local graphical criterion.

Suppose raw language is generated only from this identified representation:

`L ~ p(L | theta)`.

For example, utterances may describe a heavy object, weak damping, a stiff spring, or a collision coefficient. A language model may learn stable paraphrase classes and predict those descriptions perfectly.

Now consider two denotation maps `q` and `q'` related by an admissible coordinate permutation/diffeomorphism of `theta`, with corresponding language generators transformed so that

`p_q(L, T) = p_q'(L, T)`.

Both models have identical:

- trajectory likelihood;
- next-state prediction;
- local causal graph sparsity;
- task success under policies that use the parameters;
- utterance reconstruction and paraphrase accuracy;
- language-blind and language-shuffle gaps, if the policy is trained to depend on the chosen encoding.

Yet they can assign different internal utterance equivalence maps or different fine-grained intervention-target partitions. The language channel has only named an already identifiable dynamical representation and has not fixed the residual semantic recoding.

Therefore:

> Language descriptions of locally identifiable dynamics do not establish joint identification of raw-language equivalence and a latent intervention-target partition.

## Stronger impossibility boundary

If the language channel is conditionally generated from a sufficient statistic of the full transition process,

`L ⟂ P_residual | S(T)`,

where `P_residual` is the target partition still unresolved after the strongest non-language local-dynamics model, then

`I(P_residual ; L | S(T)) = 0`.

In that case no estimator can use language to select among residual partitions that induce the same transition statistic. Better finite-sample optimisation or easier naming does not alter the population identifiability class.

A language contribution therefore requires an externally fixed contrast whose conditional information about the residual partition remains positive after conditioning on:

- complete local transition histories;
- initial states and environment identity;
- action/intervention histories;
- learned or oracle local causal graphs;
- system-parameter representations recoverable from trajectories;
- outcomes and completed trajectories.

Positive conditional information is necessary but not sufficient; the language law must also be protected against joint recoding with the latent representation.

## Updated admissible RQ

The surviving candidate is narrowed to:

> In systems where the strongest global and state-dependent local dynamics criteria leave an explicit residual parameter/target equivalence class, can a preregistered, externally anchored population language channel provide a distinction not measurable from the complete transition process, prevent joint recoding, and jointly identify raw-utterance equivalence with a strict refinement of the residual intervention-target partition?

This formulation is **not adopted**. It remains a preregistration candidate only.

## Adoption requirements added by C023

Before adoption, the candidate must provide:

1. the non-language equivalence class after applying both global and local causal-dynamics criteria;
2. an explicit countermodel pair with identical full trajectory and local-graph distributions but different residual target partitions;
3. a language law not measurable from trajectories, local graphs, initial states, actions, interventions, outcomes, or environment identity;
4. an external denotational anchor that cannot be jointly transformed with the parameter encoder and dynamics decoder;
5. a theorem proving strict refinement beyond permutation/diffeomorphism or the relevant remaining equivalence operator;
6. an impossibility result when language only names or paraphrases trajectory-identifiable system parameters;
7. direct baselines using global sparsity, state-dependent local sparsity, and unconstrained dynamics representation learning;
8. evaluation separating next-state/task success from latent partition recovery;
9. unseen utterance-form, composition, target-combination, dynamics, and system splits;
10. public baseline reproduction and one preregistered central claim before architecture work;
11. model bytes, peak RSS, training wall time, CPU inference latency, raw logs, checksums, and seeds `1/7/19` once an experiment begins.

## Decision on RQ-001

### Decision: NARROWED BEYOND STATE-DEPENDENT LOCAL-DYNAMICS IDENTIFIABILITY — NOT ADOPTED

Raw trajectory reconstruction and sparse local causal influence already provide a language-free route to identifiable system parameters under explicit assumptions. Language that names, paraphrases, or predicts those parameters does not establish a new equivalence-class reduction. The surviving question must begin with a concrete residual ambiguity left after local-dynamics identifiability and prove that an external language contrast, rather than trajectory information or representation recoding, uniquely resolves it.

No experiment or architecture is authorised by this result.

## Resource accounting

This cycle is a prior-art, theorem/assumption, code-availability, and counterexample audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: 2026 local-dynamics CRL prior-art refinement, theorem/assumption comparison, code-availability audit, and conditional-information counterexample
- language-free system-parameter identification from sparse local dynamics: established by prior art under stated assumptions
- naming trajectory-identifiable parameters as a novel grounding contribution: rejected
- next-state/task performance as joint semantic-identification evidence: rejected
- RQ-001: further narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
