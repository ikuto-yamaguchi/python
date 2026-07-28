# Causal Identifiability Audit C076

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code availability audit, and (d) an applicability/identifiability counterexample.
- Numerical execution is not started; model size, peak RSS, runtime, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C075 established that action-conditioned finite-sample bisimulation-metric estimation has explicit theory, while an executable full-consequence partition estimator still requires coverage, consequence augmentation, and a separation-margin contract.

C076 asks:

> Does Dadashi et al.'s offline pseudometric learning provide the missing executable finite-sample LBQ001-B4 partition estimator from logged trajectories?

## Primary prior art

Primary paper:

- Robert Dadashi, Shideh Rezaeifar, Nino Vieillard, Léonard Hussenot, Olivier Pietquin, and Matthieu Geist, *Offline Reinforcement Learning with Pseudometric Learning*, ICML 2021.
- Primary publication record: `https://proceedings.mlr.press/v139/dadashi21a.html`.
- Primary paper PDF: `https://proceedings.mlr.press/v139/dadashi21a/dadashi21a.pdf`.
- Supplementary material is linked from the PMLR publication page.

The paper learns a pseudometric from logged transitions and uses it to measure how far candidate state-action behavior lies from the offline dataset support. It proves convergence of the iterative pseudometric construction, extends the construction to sampled function approximation, and uses the learned distance as a lookup malus in the PLOFF offline-RL algorithm.

## What the prior art establishes

The central correction is:

> Learning a bisimulation-related pseudometric directly from offline transition samples is existing prior art.

Therefore the following claims are removed from possible novelty:

- that a state/action behavioral pseudometric cannot be learned from a fixed logged dataset;
- that finite-sample function approximation for a bisimulation-related metric is absent from offline RL;
- that dataset-support proximity based on a learned behavioral metric is new;
- that a learned metric cannot be incorporated into offline policy optimization;
- that arbitrary online access is always required before a behavioral metric can be estimated.

## Assumption and guarantee comparison

| Object | Dadashi et al. pseudometric/PLOFF | LBQ001 finite-sample B4 requirement |
|---|---|---|
| Data source | fixed offline transition dataset | finite controlled trajectories with preregistered coverage contract |
| Controlled identity | state-action samples represented in the dataset | all admissible action identities must be retained |
| Unseen actions | outside-support behavior is penalized; not identified by data alone | missing actions must remain explicitly uncertain, not silently merged |
| Consequence law | reward and sampled successor behavior used by the metric | all preregistered non-semantic sensors, costs, availability, terminal and held-out consequences |
| Output | real-valued pseudometric and offline-policy regularizer | direct partition estimate scored against Storm B4 oracle |
| Quotient guarantee | zero/small distance is not converted into a preregistered exact partition guarantee | margin/stability-controlled merge rule required |
| Coverage | inherited from the logged dataset and behavior distribution | explicit state-action coverage or declared unidentifiable pairs |
| Latent ontology | no direct `Q/P/d` recovery | language-blind `P` only; `Q,d` remain separate |
| Public implementation | no paper-specific official immutable repository confirmed in this run | pinned executable preferred before numerical execution |
| Resource bundle | not supplied as the LBQ001 contract | seeds `17 / 29 / 43`, bytes, RSS, wall time, commands and digests mandatory |

## Suitability decision

Dadashi et al. is admissible as:

> **an offline finite-sample pseudometric-learning prior-art and coverage diagnostic**

It is not admissible as:

> **the principal executable LBQ001 finite-sample B4 partition estimator**

The mismatch is not merely implementation availability. The learned pseudometric is designed to characterize proximity to logged support and to regularize policy optimization. LBQ001-B4 requires recovery of a controlled, full-consequence equivalence partition relative to all preregistered actions and consequences.

## Counterexample 1: identical logged data, different controlled quotient

Consider two states `s` and `t`, and actions `a` and `b`.

The offline behavior policy always selects `a`. Under action `a`, both states have identical reward, successor distribution, cost, and sensor consequences. Therefore every logged transition and every learned dataset-supported pseudometric statistic can be identical for `s` and `t`.

Under the unobserved action `b`:

- from `s`, `b` leads to terminal physical outcome `x`;
- from `t`, `b` leads to terminal physical outcome `y`;
- `x` and `y` have distinct preregistered non-semantic sensor signatures.

Two MDPs are compatible with exactly the same logged dataset:

1. model A, in which `b` has the same consequence from `s` and `t`;
2. model B, in which `b` has the distinct consequences above.

A metric learner using only the logged data cannot distinguish the two models. Storm's complete-model B4 oracle merges `s,t` in model A and separates them in model B.

Therefore:

> An offline pseudometric can be perfectly estimated on the observed support while the action-complete B4 quotient remains unidentified.

This is a coverage non-identifiability result, not an optimization failure.

## Counterexample 2: metric accuracy does not determine a partition

Suppose an offline estimator recovers pairwise pseudometric values to uniform error `epsilon`. A partition rule merges state pairs whose estimated distance is at most threshold `delta`.

For pairs with true distances `delta - eta` and `delta + eta`, if `epsilon >= eta`, both opposite merge decisions remain compatible with the metric guarantee.

Thus direct partition recovery still needs a preregistered separation/stability condition such as

`min_between_block d - max_within_block d > 2 epsilon`.

Convergence of a sampled pseudometric or successful policy regularization does not itself provide this B4 quotient margin.

## Counterexample 3: reward/successor pseudometric can omit an independent consequence

Let `s` and `t` have identical rewards and successor-state distributions for every observed action, but differ in a calibrated sensor consequence `z` included in the preregistered B4 family and excluded from the metric input.

The learned pseudometric can legitimately assign zero distance while B4 must separate the states. Adding `z` to the metric input is admissible only when the channel and encoding were fixed independently of language, target identity, parser slots, reward labels, and evaluator semantics.

Therefore:

> Offline pseudometric learning becomes a full-consequence candidate only after an explicit, codebook-independent consequence augmentation contract; without it, zero distance is only relative to the supplied behavioral channels.

## Public-code availability audit

The PMLR page, paper PDF, supplementary material, Google Research publication record, OpenReview record, author publication records, and GitHub search results were checked.

Confirmed:

- primary peer-reviewed paper and supplementary material;
- a sampled function-approximation procedure;
- offline-policy experiments on manipulation and locomotion;
- convergence and policy-relevant pseudometric analysis.

Not confirmed as an official immutable reproduction bundle:

- a paper-specific author-managed public repository and exact commit;
- a canonical command reproducing the pseudometric tables/figures;
- dependency lock or immutable container;
- direct finite-state quotient output;
- Storm-compatible partition export;
- full-consequence augmentation manifest;
- coverage and unidentifiable-pair report;
- ARI/AMI/pairwise-F1/VI evaluation;
- seeds `17 / 29 / 43` and model-size/RSS/runtime instrumentation.

Community implementations are not promoted to the canonical baseline because provenance and correspondence to the paper theorem were not established.

No numerical execution was started.

## Consequence for RQ-001

This prior art concerns the language-blind behavioral side. It does not identify raw-language equivalence `Q`, denotation `d`, or external semantic orientation.

It refines the B4 gate as follows:

1. offline sampled pseudometric learning is prior art;
2. policy-relative or dataset-support-relative distance must not be presented as an action-complete target quotient;
3. state-action coverage must be part of identifiability, not merely an empirical quality statistic;
4. unobserved actions create multiple observationally compatible B4 partitions;
5. metric-to-partition conversion still requires a separation margin;
6. all full-consequence channels must be preregistered and semantic-codebook independent;
7. no official immutable executable matching the complete LBQ001-B4 contract was confirmed.

## Decision

**NARROWED: OFFLINE SAMPLED PSEUDOMETRIC LEARNING IS EXISTING PRIOR ART, BUT IT IDENTIFIES ONLY DATA-SUPPORTED BEHAVIORAL DISTANCE; IT DOES NOT CLOSE THE ACTION-COMPLETE FULL-CONSEQUENCE PARTITION GATE — NOT ADOPTED.**

The baseline stack is refined to:

1. DeepMDP B3 reward/transition control;
2. Storm exact-model B4 MDP oracle;
3. Kiefer–Tang LMC finite-sample diagnostic;
4. Tao–Xu–You GBSM finite-sample action-conditioned metric theory;
5. Dadashi et al. offline sampled-pseudometric/coverage diagnostic;
6. a still-missing pinned executable that returns a full-consequence controlled partition or explicitly abstains on pairs lacking coverage, under a preregistered margin rule.

## Next admissible work

1. audit public finite-MDP model-estimation or probabilistic-model-checking pipelines that preserve action identity, expose confidence intervals, and export an empirical MDP to Storm;
2. determine whether an unchanged public plug-in estimator plus Storm constitutes a reproducible B4 estimator without creating a new architecture;
3. preregister an abstaining partition rule: merge, separate, or unidentified according to confidence intervals and the separation margin;
4. freeze the complete-consequence encoding and prohibit target- or language-derived labels;
5. freeze the DeepMDP compatibility manifest and Storm input format;
6. begin numerical execution only after exact commands, three seeds, resource instrumentation, dataset digest, result digest, coverage and abstention outputs are fixed.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Public-code availability audit: completed.
- Applicability/identifiability counterexamples: completed.
- Offline sampled pseudometric learning: existing prior art.
- Action-complete quotient recovery from arbitrary logged data: not guaranteed.
- Full-consequence partition estimator: not selected.
- Public numerical reproduction: not started.
- Model size, RSS, runtime, three seeds: mandatory after execution starts; not yet applicable.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- RQ-001: narrowed and not adopted.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
