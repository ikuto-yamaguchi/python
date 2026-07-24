# Prior-Art Audit 001

This is a first-pass map, not a novelty claim. The search must continue until the assumptions and contribution of each adjacent line are checked in the full paper and code.

| Work | What it establishes | Structure/supervision supplied | Gap relative to RQ-001 |
|---|---|---|---|
| Ahuja et al., *Interventional Causal Representation Learning*, ICML 2023 | Identifiability of latent causal factors under perfect/interpretable interventions, up to permutation/scaling; weaker block identification under imperfect interventions | Interventional environments; mathematical assumptions on observation/support | No raw language alignment or instruction following |
| Varici et al., *General Identifiability and Achievability for CRL*, AISTATS 2024 | General nonparametric identifiability with uncoupled hard interventions | Multiple intervention environments; latent causal model assumptions | Does not jointly discover lexical/utterance equivalence |
| Varici et al., *Unknown Multi-node Interventions*, 2024 | Identifiability with unknown multi-node interventions under linear observation mixing | Linear mixing; sufficiently diverse interventions | Closest unknown-target theory, but no raw language |
| Ng et al., *CRL from General Environments under Nonparametric Mixing*, AISTATS 2025 | Broader identifiability conditions across general environments | Distribution-shift assumptions | No language grounding task |
| Markham et al., *Intervening to learn and compose causally disentangled representations*, CLeaR 2026 | Context module learns composable causally disentangled concepts in expressive generative models | Concept/context information and model architecture assumptions | Must inspect whether concept information corresponds to known intervention labels; no raw Japanese |
| Liu et al., *CausalTriplet*, CLeaR 2023 | Actionable counterfactual benchmark; current methods struggle without object-centric priors | Visual scenes, intervention structure, object-centric downstream task | No natural-language acquisition |
| Brady et al., *Provably Learning Object-Centric Representations*, ICML 2023 | Conditions for unsupervised object-centric identifiability | Compositionality and irreducibility of scene generator | No actions or raw language |
| Gaddy & Klein, *Pre-Learning Environment Representations for Data-Efficient Neural Instruction Following*, ACL 2019 | Language-free transition pretraining improves instruction following | Environment transitions and task action structure | Does not target causal identifiability or unknown intervention targets |
| Han & Schlangen, *Grounding Language by Continuous Observation of Instruction Following*, EACL 2017 | Incremental action traces improve sub-utterance grounding | Observed human action sequence and GUI domain | No latent causal variable identifiability |
| Zhong et al., *SILG*, NeurIPS 2021 | Unified multi-environment interactive language grounding benchmark; shared recurrent/entity-centric baselines | Symbolic observations/actions and environment APIs | Suitable reproduction benchmark; semantics are not jointly identified with latent causal state |
| Ueda et al., *J-CRe3*, LREC-COLING 2024 / JNLP 2024 | Real-world Japanese reference grounding with egocentric video/dialogue | Bounding-box and crossmodal reference annotations | Realistic Japanese audit; not an intervention/action benchmark |
| Shelton et al., *PQB-EQA*, ACL 2025 | Balanced environments expose language-only guessing in embodied QA | Paired question/environment construction | Useful control principle, not a learning principle |

## Initial conclusion

The previous program rediscovered pieces of known identifiability and grounding ideas without establishing novelty. The defensible candidate gap is narrower:

> joint identification of a latent intervention partition and cross-expression language equivalence from the same trajectories, when intervention targets are hidden and no pretrained parser/object slots are supplied.

This remains only a candidate gap. The next search must include:

- language-conditioned causal representation learning
- latent action discovery from text and trajectories
- unsupervised semantic parsing from interaction
- unknown intervention target CRL
- multimodal nonlinear ICA with language views
- object-centric instruction following without slots
- 2025–2026 CLeaR, ICML, ICLR, NeurIPS, ACL and CoRL papers

## Primary sources

- https://proceedings.mlr.press/v202/ahuja23a.html
- https://proceedings.mlr.press/v238/varici24a.html
- https://arxiv.org/abs/2406.05937
- https://proceedings.mlr.press/v258/ng25a.html
- https://proceedings.mlr.press/v323/markham26a.html
- https://proceedings.mlr.press/v213/liu23a.html
- https://proceedings.mlr.press/v202/brady23a.html
- https://aclanthology.org/P19-1188/
- https://aclanthology.org/E17-2079/
- https://proceedings.neurips.cc/paper_files/paper/2021/hash/b3e3e393c77e35a4a3f3cbd1e429b5dc-Abstract.html
- https://aclanthology.org/2024.lrec-main.829/
- https://aclanthology.org/2025.acl-short.11/
