# Causal Identifiability Audit C024

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + public-code availability audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, researcher-authored intervention ontology, benchmark variant, memory mechanism, or branch was introduced.

## Primary work newly audited

### Isolated Causal Effects of Natural Language

Victoria Lin, Louis-Philippe Morency, and Eli Ben-Michael. Proceedings of the 42nd International Conference on Machine Learning, PMLR 267, 2025.

Primary records:

- PMLR: https://proceedings.mlr.press/v267/lin25k.html
- proceedings PDF: https://raw.githubusercontent.com/mlresearch/v267/main/assets/lin25k/lin25k.pdf
- official software: https://github.com/torylin/isolated-text-effects

The PMLR record explicitly links the author-maintained public repository. The repository README states that the released code reproduces the paper experiments through `./run_all_amazon.sh` and `./run_all_tirzepatide.sh`. The repository is therefore public prior art for estimating isolated causal effects of language-encoded interventions. It is not, however, a packaged causal-representation baseline with pinned dependency versions, pretrained checkpoints, or a theorem for latent intervention-target partition recovery.

No public baseline reproduction was started in this cycle because R0 forbids opening a new empirical track before the active external capability baseline and preregistration gates pass. The code availability and claim boundary were audited only.

## Exact estimand and observation boundary

The paper treats a focal language-encoded intervention as a treatment whose isolated effect on an external outcome is to be estimated while accounting for the rest of the text. Let:

- `A` denote the focal language intervention or focal textual attribute;
- `N` denote all non-focal language content;
- `Y` denote an external response or outcome;
- `X` denote observed pretreatment covariates.

The central problem is not latent causal representation recovery. It is estimating the effect of changing `A` while holding fixed, or sufficiently approximating, the non-focal content `N`. The paper emphasizes that poor approximation of non-focal language induces omitted-variable bias and evaluates effect estimates along fidelity and overlap dimensions.

Thus the identifying burden is attached to a causal effect estimand over an already specified focal intervention, not to discovering a unique latent partition of intervention targets or a unique equivalence relation over raw utterances.

## What this prior art establishes

The following claims cannot be treated as novel contributions of RQ-001:

- defining a language-encoded focal attribute as a causal intervention;
- estimating the isolated causal effect of changing a focal linguistic property on an external outcome;
- using learned text representations to approximate non-focal language content;
- diagnosing omitted-variable bias caused by inadequate representation of non-focal text;
- evaluating language intervention estimates through fidelity and overlap;
- using semi-synthetic or real-world text data to validate a language causal-effect estimator;
- treating a focal linguistic concept such as factual inaccuracy, framing, sentiment, or treatment mention as an intervention variable;
- claiming that causal effects of natural-language changes are themselves an unexplored problem.

## What this prior art does not establish

The paper does not provide:

- an unknown latent intervention-target partition;
- a theorem identifying raw-utterance equivalence classes;
- a theorem jointly identifying language equivalence and latent causal targets;
- causal representation recovery from low-level observations;
- intervention targets that must be discovered rather than specified as a focal textual attribute;
- an external denotational anchor preventing joint recoding of language and latent variables;
- interactive grounding through actions and environment transitions;
- guarantees that fidelity/overlap of a non-focal text representation imply uniqueness of a latent semantic partition;
- a result that isolated effect identification selects one denotation map among observationally equivalent language encodings.

A valid isolated effect estimate can coexist with multiple incompatible internal utterance partitions, provided they induce the same focal-treatment assignment, non-focal adjustment variables, and outcome law.

## Theorem/assumption comparison

| Dimension | Lin et al. 2025 | Current RQ-001 candidate | Remaining burden |
|---|---|---|---|
| Primary target | Isolated causal effect of a specified focal language intervention | Raw-language equivalence plus a residual latent intervention-target partition | Define the latent objects independently of the effect estimand |
| Treatment semantics | Focal linguistic intervention is specified or operationalised before estimation | Equivalence and target membership are unknown | Prove the treatment classes themselves are identifiable |
| Adjustment object | Approximation of all non-focal language | Strongest non-language statistic plus externally anchored language contrast | Show the language contrast is not merely an adjustment representation |
| Observation | Text, observed covariates, external outcomes | Raw utterances, trajectories/interactions, hidden targets | State which variables are pre-treatment and forbid post-treatment leakage |
| Guarantee | Effect estimation/sensitivity under fidelity and overlap considerations | Strict reduction of a latent causal equivalence class | Supply an equivalence-class theorem, not only an unbiased effect estimator |
| Failure mode | Omitted non-focal language and inadequate overlap bias the effect estimate | Joint recoding leaves utterance/target partitions non-unique | Show how an external anchor removes the recoding symmetry |
| Evaluation | Effect recovery and sensitivity diagnostics | Partition recovery plus prospective task/transfer metrics | Do not infer latent identification from effect accuracy alone |
| Public code | Author-maintained experiment scripts are available | Reproduction must be preregistered and resource audited | Pin dependencies, data provenance, seeds, logs, checksums before execution |

## Prior-art matrix refinement

The novelty matrix must now distinguish at least five different claims that were previously easy to conflate:

1. **language as treatment** — estimate the effect of a prespecified textual attribute;
2. **language as adjustment information** — represent non-focal text to control confounding or omitted-variable bias;
3. **language as outcome predictor** — improve prediction of an external response;
4. **language as denotational anchor** — supply information that selects among otherwise equivalent latent target partitions;
5. **joint identification** — uniquely recover both raw-utterance equivalence and a residual intervention-target partition.

Lin et al. directly covers cases 1 and 2 and evaluates case 3 as part of effect estimation. RQ-001 can only remain potentially novel in cases 4 and 5.

The following broad candidate claims are rejected:

- causal effects of natural-language interventions are unexplored;
- a significant language-treatment effect identifies the semantic class that caused it;
- a high-fidelity non-focal text representation identifies raw utterance equivalence;
- overlap of text embeddings across treatment groups identifies a latent target partition;
- unbiased outcome effects imply a uniquely grounded language representation;
- sensitivity to focal-language shuffle proves joint causal grounding.

## Counterexample: correct isolated effects with non-identifiable utterance and target partitions

Let raw utterances be `U`, a prespecified focal treatment extractor be `a(U) in {0,1}`, an observed adjustment representation be `n(U)`, and the outcome law be

`Y = tau * a(U) + g(n(U), X) + epsilon`.

Assume overlap holds and `n(U)` is sufficient for all non-focal outcome-relevant language. Then the isolated average effect `tau` is identifiable and can be estimated correctly.

Now let `q` and `q'` be two different equivalence relations over raw utterances. Let `P` and `P'` be two different latent intervention-target partitions. Construct them so that:

- `a(U)` is identical under both models;
- `n(U)` is identical under both models;
- the distribution of `(X, U, Y)` is identical;
- the same focal-language edits induce the same outcome distribution;
- all fidelity, overlap, effect-error, placebo, and sensitivity diagnostics are identical.

The two models may still disagree about whether two utterances are semantically equivalent and about which fine-grained latent target each utterance denotes. Because the effect estimator only requires the focal treatment and sufficient non-focal adjustment, it has no statistical reason to choose between `(q, P)` and `(q', P')`.

Therefore:

> Correct identification of an isolated causal effect of language does not identify raw-language equivalence or a latent intervention-target partition.

## Stronger impossibility boundary

Let `S(U, X)` be a sufficient statistic for the focal treatment assignment, non-focal adjustment, and external outcome law. If two candidate pairs `(q, P)` and `(q', P')` satisfy

`p(Y, A, S)_(q,P) = p(Y, A, S)_(q',P')`,

then any isolated-effect functional identified from `(Y, A, S)` is the same under both candidates. No improvement in outcome-effect estimation, fidelity, or overlap can distinguish the latent pairs.

Equivalently, if the proposed language anchor contributes no information about the residual partition after conditioning on the full effect-estimation statistic,

`I(P_residual ; L_anchor | A, S(U, X), Y) = 0`,

then isolated language effects cannot refine the residual target partition.

Positive conditional information remains only a necessary condition. The anchor must also be externally fixed so that it cannot be transformed jointly with the utterance encoder, target partition, and outcome model.

## Consequence for interactive language grounding

Interactive feedback does not automatically escape this boundary. If each response is used only to improve treatment assignment, non-focal adjustment, or outcome prediction, then it can improve isolated-effect estimation without identifying denotations.

A joint-identification claim must show an intervention or query whose answer distinguishes a countermodel pair that has:

- the same focal language treatment;
- the same non-focal adjustment statistic;
- the same complete interaction and outcome distribution;
- different raw-utterance equivalence and residual target partitions.

The query response must be generated by an externally fixed denotational law, not by the same latent model being identified.

## Updated admissible RQ

The surviving candidate is narrowed to:

> After conditioning on sufficient focal-treatment, non-focal-language, trajectory, interaction, and outcome statistics required by existing causal-effect and non-language CRL methods, can a preregistered external language law distinguish a concrete countermodel pair with identical isolated language effects but different raw-utterance equivalence and residual intervention-target partitions, and thereby strictly identify their joint refinement?

This formulation is **not adopted**. It remains a preregistration candidate only.

## Adoption requirements added by C024

Before adoption, the candidate must provide:

1. a formal separation between the isolated language-effect estimand and the latent utterance/target objects;
2. a countermodel pair with identical focal treatment, non-focal adjustment statistic, overlap, outcome law, and isolated effects but different latent partitions;
3. a language contrast that distinguishes that pair and is not measurable from text adjustment features, trajectories, actions, environment identity, outcomes, or completed interactions;
4. an externally fixed denotational anchor immune to joint recoding;
5. a strict joint-identification theorem or consistency result;
6. an impossibility theorem when language contributes only a focal treatment label or non-focal adjustment representation;
7. direct comparison against isolated-language-effect estimation and text-adjustment baselines;
8. preregistered prospective splits for unseen utterance form, composition, target combination, dynamics, and system;
9. explicit prevention of post-treatment, outcome, completed-trajectory, and target-label leakage;
10. public baseline reproduction before architecture work;
11. model bytes, peak RSS, training wall time, CPU inference latency, raw logs, checksums, and seeds `1/7/19` once an experiment begins.

## Decision on RQ-001

### Decision: NARROWED BEYOND IDENTIFIABLE ISOLATED LANGUAGE EFFECTS — NOT ADOPTED

The causal effect of a specified language-encoded intervention on an external outcome is already a formalised and publicly implemented research problem. Accurate isolated-effect estimation, faithful representation of non-focal language, and adequate overlap do not uniquely identify utterance equivalence or latent intervention targets. RQ-001 survives only if it proves that an externally fixed language law resolves a concrete latent ambiguity that remains after all effect-estimation and non-language sufficient statistics are conditioned upon.

No experiment or architecture is authorised by this result.

## Public-code status

Author-maintained software is available at `torylin/isolated-text-effects`. The public README exposes top-level experiment commands but does not provide an exact environment lock, release tag, pretrained artifact, resource manifest, or three-seed reproduction contract. A future reproduction would therefore need to pin the exact commit and all dependencies and preserve raw data/log/checksum provenance. No such reproduction was initiated in this cycle.

## Resource accounting

This cycle is a prior-art, theorem/assumption, public-code availability, and counterexample audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: isolated-language-effect prior-art refinement, theorem/assumption comparison, public-code audit, and identifiability counterexample
- isolated causal effect estimation for prespecified language interventions: established prior art
- non-focal language fidelity/overlap as joint semantic-identification evidence: rejected
- accurate isolated language effects as latent partition evidence: rejected
- RQ-001: further narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
