# Prior-Art Audit 001

This is a living primary-source map, not a novelty claim. Every row records what is actually established and what remains outside scope.

| Work | What it establishes | Structure/supervision supplied | Gap relative to RQ-001 |
|---|---|---|---|
| Ahuja et al., *Interventional Causal Representation Learning*, ICML 2023 | Identifiability of latent causal factors under perfect/interpretable interventions, up to permutation/scaling; weaker block identification under imperfect interventions | Interventional environments; mathematical assumptions on observation/support | No raw-language alignment or instruction following |
| von Kügelgen et al., *Nonparametric Identifiability of Causal Representations from Unknown Interventions*, 2023 | Nonparametric latent-variable and graph identifiability from unknown perfect interventions, subject to genericity and intervention diversity | Distribution-level environments; perfect interventions; for general dimension, at least two distinct perfect interventional domains per node | No language view; the environment partition itself is observed |
| Varici et al., *General Identifiability and Achievability for CRL*, AISTATS 2024 | General nonparametric identifiability with uncoupled hard interventions | Multiple intervention environments; hard-intervention and latent-model assumptions | Does not jointly discover lexical/utterance equivalence |
| Varici et al., *Linear CRL from Unknown Multi-node Interventions*, 2024 | Identifiability under unknown multi-node interventions | Linear observation mixing; sufficiently diverse interventions | No raw language; linear mixing |
| Ng et al., *CRL from General Environments under Nonparametric Mixing*, AISTATS 2025 | Recovers latent DAG and variables from broader environment changes under nonparametric mixing | Sufficient mechanism-change conditions, including higher-order derivative conditions; latent noise-model assumptions | No language grounding; environment shifts remain a supplied grouping |
| Li et al., *On the Identifiability of Causal Abstractions*, AISTATS 2025 | Characterizes the granularity recoverable from arbitrary-subset unknown interventions; exact low-level identity may collapse to an identifiable abstraction | Contrastive pre/post pairs and a family of possible interventions | Direct warning that RQ-001 may only admit abstraction-level recovery; no language alignment |
| Lee et al., *Beyond Identifiability: Learning Causal Representations with Few Environments and Finite Samples*, arXiv 2026 | Finite-sample recovery of latent graph, mixing representation and unknown multi-node targets with logarithmically many environments in the studied model | Linear/statistical model assumptions and multiple environment distributions | Shrinks the novelty of “unknown targets with few environments”; no raw language or interactive policy semantics |
| Schneider et al., *Generative Intervention Models for Causal Perturbation Modeling*, ICML 2025 | Jointly estimates a causal model and maps observed perturbation features to distributions over atomic interventions, including unseen perturbation features | Perturbation features, distributional intervention data and causal-model assumptions | Closest overlap: `language features -> intervention distribution` alone is not novel; raw interactive utterance equivalence without supplied feature semantics remains outside scope |
| Lin et al., *Isolated Causal Effects of Natural Language*, ICML 2025 | Formal estimation of the causal effect of focal language changes on external outcomes; analyzes omitted-variable bias from non-focal language | Defined focal language intervention, outcome and approximation of non-focal text | Language-as-treatment is prior art; no latent intervention-partition recovery or interactive instruction following |
| Gamella et al., *Sanity Checking CRL on a Simple Real-World System*, ICML 2025 | Representative CRL methods fail on a controlled real optical system and often already fail in simplified synthetic ablations | Controlled system satisfying headline CRL assumptions and known ground truth | Makes public reproduction and real-data sanity checks mandatory before theory or toy success is treated as evidence |
| Markham et al., *Intervening to Learn and Compose Causally Disentangled Representations*, CLeaR 2026 | Learns composable causal concepts under intervention/context supervision | Concept/context and architecture assumptions | Must not be treated as raw semantic birth; no raw Japanese |
| Liu et al., *CausalTriplet*, CLeaR 2023 | Actionable counterfactual benchmark; exposes dependence on object-centric priors | Visual scenes and intervention structure | No natural-language acquisition |
| Brady et al., *Provably Learning Object-Centric Representations*, ICML 2023 | Conditions for unsupervised object-centric identifiability | Compositionality and irreducibility of scene generator | No actions or raw language |
| Gaddy & Klein, *Pre-Learning Environment Representations for Data-Efficient Neural Instruction Following*, ACL 2019 | Language-free transition pretraining improves instruction following | Environment transitions and task action structure | Environment-first learning is prior art, not our novelty |
| Han & Schlangen, *Grounding Language by Continuous Observation of Instruction Following*, EACL 2017 | Incremental action traces improve sub-utterance grounding | Observed human action sequence and GUI domain | No latent causal-variable identifiability |
| Zhong et al., *SILG*, NeurIPS 2021 | Unified five-environment interactive language-grounding benchmark and shared recurrent/entity-centric baselines | Symbolic observation/action APIs and environment-specific wrappers | Reproduction benchmark; state/object/action interface is substantially exposed |
| Zhong et al., *Language Dynamics Distillation*, NeurIPS 2022 | Language-conditioned next-dynamics pretraining improves sample efficiency and generalization on SILG | Language-described expert demonstrations, actions and observed transitions | Joint language–dynamics learning is prior art; hidden intervention partition is not recovered |
| Wong et al., *Learning Grounded Action Abstractions from Language*, ICLR 2024 | Learns reusable action abstractions for planning from language/task evidence | Planner/action interface and program-library induction assumptions | Not raw semantic birth without supplied planning structure |
| Ueda et al., *J-CRe3*, LREC-COLING / JNLP 2024 | Real-world Japanese crossmodal reference grounding, including predicate-argument and bridging references | Egocentric video, dialogue transcripts and bounding-box reference annotations | Realism audit only; not an intervention/action benchmark |
| Shelton et al., *PQB-EQA*, ACL 2025 | Balanced paired environments expose language-only guessing | Paired question/environment construction | Useful control principle, not a learning principle |

## Updated conclusion — 2026-07-24

The broad form of RQ-001 is not novel. Unknown intervention-target recovery, nonparametric identifiability, abstraction-level recovery, finite-sample recovery from few environments, perturbation-feature-to-intervention modeling, interactive grounding, language-conditioned dynamics learning and causal estimation of language effects already exist as separate mature lines.

The only defensible candidate gap is narrower:

> On a fixed public interactive benchmark, does raw language contain statistically necessary information about an intervention partition or causal abstraction beyond state, action, history and environment identity, and can that information be recovered up to joint permutation without intervention-target labels, semantic parsers, object slots, pretrained language models or supplied perturbation-feature semantics?

Even this is not adopted. It must be rejected if any primary source already demonstrates the same joint recovery, if GIM already subsumes the operational setting once utterances are represented as perturbation features, or if SILG reproduction shows that language adds no stable held-out-mechanism signal beyond state/action/history controls.

## Consequences for the program

1. “Unknown intervention target” alone is not a contribution after the 2023–2026 CRL results.
2. `language embedding -> intervention distribution` alone is also not a contribution after GIM.
3. Exact variable or utterance-target names are not identifiable under joint latent/language permutation without an observable anchor; evaluation must be permutation- or abstraction-aware.
4. Exact variable identity may be impossible; abstraction-level recovery must be an allowed theoretical outcome.
5. SILG/LDD must be reproduced before designing a new model because multi-environment grounding and language-conditioned dynamics are established baselines.
6. Public reproduction is a scientific requirement, not housekeeping, given the real-system CRL failures reported by Gamella et al.
7. J-CRe3 remains an external Japanese realism audit rather than the causal benchmark.
8. Novelty requires a joint theorem or external result showing a language-specific gain that cannot be explained by state, action, history, environment ID, transition statistics, perturbation features or label leakage.

## Reproduction facts pinned in this audit

- SILG PyPI package: `silg==0.0.1`, released 2021-10-20, Python `>=3.7.10`, MIT.
- SILG official instructions require installing individual environments, then `pip install -r requirements.txt`, `pip install -e .`; experiments enter through `run_exp.py` / `launch.py`.
- Initial reproduction target remains RTFM or Messenger, not all five environments.
- J-CRe3 public dataset repository: `https://github.com/riken-grp/J-CRe3`; public metadata availability date 2026-04-06.

## Primary sources

- https://proceedings.mlr.press/v202/ahuja23a.html
- https://arxiv.org/abs/2306.00542
- https://proceedings.mlr.press/v238/varici24a.html
- https://arxiv.org/abs/2406.05937
- https://proceedings.mlr.press/v258/ng25a.html
- https://proceedings.mlr.press/v258/li25g.html
- https://arxiv.org/abs/2603.25796
- https://proceedings.mlr.press/v267/schneider25a.html
- https://proceedings.mlr.press/v267/lin25k.html
- https://proceedings.mlr.press/v267/gamella25a.html
- https://proceedings.mlr.press/v323/markham26a.html
- https://proceedings.mlr.press/v213/liu23a.html
- https://proceedings.mlr.press/v202/brady23a.html
- https://aclanthology.org/P19-1188/
- https://aclanthology.org/E17-2079/
- https://proceedings.neurips.cc/paper_files/paper/2021/hash/b3e3e393c77e35a4a3f3cbd1e429b5dc-Abstract.html
- https://proceedings.neurips.cc/paper_files/paper/2022/hash/51053d7b8473df7d5a2165b2a8ee9629-Abstract-Conference.html
- https://openreview.net/forum?id=qJ0Cfj4Ex9
- https://aclanthology.org/2024.lrec-main.829/
- https://github.com/riken-grp/J-CRe3
- https://aclanthology.org/2025.acl-short.11/
