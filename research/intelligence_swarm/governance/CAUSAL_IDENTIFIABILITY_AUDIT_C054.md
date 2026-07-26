# Causal Identifiability Audit C054

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code availability audit + identifiability counterexample**.

No new architecture, old A–E toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced. No experiment was started.

## Primary work newly audited

### Provable Limitations of Acquiring Meaning from Ungrounded Form: What Will Future Language Models Understand?

William Merrill, Yoav Goldberg, Roy Schwartz, and Noah A. Smith. Transactions of the Association for Computational Linguistics, 2021.

Primary records:

- ACL Anthology: https://aclanthology.org/2021.tacl-1.62/
- journal record / DOI: https://doi.org/10.1162/tacl_a_00412
- arXiv: https://arxiv.org/abs/2104.10809

The paper formalizes whether a learner exposed only to symbolic form plus textual assertions can emulate semantic relations such as equivalence. It proves a positive result for strongly transparent languages and a negative computability result once context-sensitive constructs such as variable binding are admitted.

This is directly relevant to the language-dynamics-pretraining component of RQ-001. It establishes that distributional form augmented by assertion-like textual evidence can sometimes recover an equivalence-preserving representation, but only under a strong transparency condition. It does not identify an external latent intervention ontology or a denotation from raw utterance classes to intervention targets.

## Assumption, observation, and guarantee comparison

Let:

- `Sigma*` be the set of finite expressions;
- `L` be a formal language with a semantic interpretation;
- `N_L(e1,e2 | c)` be an assertion oracle indicating whether expressions `e1` and `e2` are semantically equivalent in context `c`;
- `E_L` be the target semantic-equivalence relation;
- `Q` be the unknown raw-language equivalence relation required by RQ-001;
- `P` be the unknown latent intervention-target partition;
- `d: Sigma*/Q -> P` be the denotation map required by RQ-001.

### Observations available in the audited work

The learner receives symbolic expressions and access to assertion information internal to the language. It does not receive:

- external world states;
- interventions on latent causal variables;
- action-conditioned trajectories;
- target identities;
- a cross-system denotation map;
- an independently fixed external semantic ontology.

Assertions provide indirect semantic evidence because the distribution or availability of assertion contexts depends on semantic relations inside the language.

### Positive boundary: strong transparency

For strongly transparent languages, semantic equivalence is stable across the relevant contexts. The paper gives a constructive emulator: an expression can be mapped to a canonical representative found through the assertion oracle. Thus, under strong transparency and oracle access, the equivalence relation is emulatable.

This excludes the following claim from the novelty space:

> Assertion-like language dynamics can never recover an equivalence-preserving representation without non-linguistic grounding.

That absolute claim is false. Under strong transparency, assertions are sufficient for semantic emulation of the internal equivalence relation studied by the paper.

### Negative boundary: contextual opacity and variable binding

When the same expression can take different semantic values in different contexts, the canonicalization argument no longer applies. The paper constructs language classes for which semantic emulation from ungrounded assertion form becomes uncomputable.

This establishes a stronger limitation than ordinary finite-data insufficiency. More language-only pretraining, larger models, or lower perplexity cannot by themselves provide a general guarantee over those language classes.

The result does not prove that natural-language grounding is impossible. It proves a formal limitation for the specified model of languages, assertions, equivalence, and emulation.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded from the novelty space:

- using assertion-like textual contexts as indirect evidence about semantic equivalence;
- recovering canonical representatives of expressions in strongly transparent languages;
- showing that raw-form learning can emulate an internal semantic relation under transparency assumptions;
- showing computability barriers for ungrounded semantic emulation under context-sensitive interpretation;
- claiming that language dynamics or next-token structure alone universally determines meaning;
- treating lower language-model loss as proof that context-sensitive semantic equivalence has been identified;
- treating successful paraphrase prediction as proof that an external intervention ontology has been recovered;
- claiming that adding assertions to pretraining is by itself a new grounding principle.

The paper establishes both a positive and a negative prior-art boundary. RQ-001 must therefore specify exactly which cross-system observations break the ungrounded-form limitation and which transparency assumptions are being replaced.

## What the existing guarantees do not identify

The audited theorem line does not identify:

- an unknown intervention-target partition `P` in an external causal system;
- a denotation `d` from raw-language classes to target blocks;
- whether the internal equivalence relation used by the language coincides with causal equivalence under interventions;
- whether two expressions with the same textual assertion profile denote one external target or two intervention-aliased targets;
- an absolute identity for target blocks beyond simultaneous relabeling;
- semantic distinctions that never alter assertion truth, trajectories, interventions, rewards, or outcomes;
- joint recovery of `Q`, `P`, and `d` from language dynamics alone.

Even perfect emulation of internal expression equivalence is weaker than joint semantic-causal identification.

## Theorem/assumption boundary for RQ-001

Define:

- `Q_text` as the finest equivalence relation recoverable from all legitimate language-only observations, including assertions;
- `P_causal` as the finest target partition recoverable from all legitimate non-language observations and interventions;
- `Aut_text` as transformations preserving the complete language observation law;
- `Aut_causal` as transformations preserving the complete causal observation/intervention law;
- `Aut_joint` as simultaneous transformations preserving both marginal laws and all observed cross-system interactions.

The audited positive result can establish recoverability of an internal equivalence relation when transparency makes `Aut_text` sufficiently small. It does not establish:

\[
Q_text = Q,
\]

nor:

\[
P_causal = P,
\]

nor uniqueness of:

\[
d: Q \to P.
\]

For RQ-001, a necessary condition is that the observed cross-system law reduce every semantics-changing element of `Aut_text x Aut_causal` to an equivalence accepted by the target notion of identification.

Informally, language and causal dynamics must constrain each other in a way that cannot be reproduced by a joint recoding.

## Identifiability counterexample A: perfect transparent-language emulation, unknown denotation

Assume the language is strongly transparent and an oracle learner perfectly recovers the internal equivalence classes:

\[
Q_text = \{q_1,\ldots,q_m\}.
\]

Assume also that a causal learner perfectly recovers target blocks:

\[
P_causal = \{p_1,\ldots,p_m\}.
\]

Construct Model A with denotation:

\[
d_A(q_i)=p_i.
\]

For any non-identity permutation `sigma`, construct Model B with:

\[
d_B(q_i)=p_{\sigma(i)}.
\]

Simultaneously permute all target-indexed environment interfaces, policy inputs, decoder outputs, and logged target labels by `sigma`.

Models A and B preserve:

- every raw-text distribution;
- every assertion-oracle answer;
- the canonical representative of every expression;
- the recovered internal equivalence relation;
- every observational and interventional distribution after target relabeling;
- every action, reward, outcome, and task-success statistic;
- every next-token and next-state prediction score;
- every language-shuffle statistic defined only through the same joint interface.

Yet `d_A` and `d_B` assign different external target meanings to the same raw-language class.

Therefore:

> Perfect semantic emulation inside a transparent language and perfect causal-target recovery do not jointly identify denotation when a simultaneous cross-system permutation remains observationally valid.

## Identifiability counterexample B: identical assertion profile, different external ontology

Let raw expressions `u1` and `u2` have identical assertion behavior in every observable linguistic context.

Construct Model A:

- `u1` and `u2` belong to one equivalence class;
- both denote one target block `p`.

Construct Model B:

- `u1` and `u2` belong to distinct intended semantic classes;
- they denote distinct target blocks `p1` and `p2`;
- `p1` and `p2` have identical transition, intervention, reward, feedback, and outcome laws under every admissible experiment.

Both models preserve:

- all language strings and frequencies;
- all assertion truth values;
- all context-conditioned language dynamics;
- all observational and interventional distributions;
- all policies and values;
- all task outcomes;
- all paraphrase and language-model metrics.

Nevertheless:

\[
Q_A \ne Q_B, \qquad P_A \ne P_B,
\]

and their denotation maps differ.

Thus neither transparent-language emulation nor unlimited language-dynamics pretraining can resolve semantic distinctions that are aliased in both the assertion law and the complete external causal law.

## Identifiability counterexample C: opaque semantics defeat a universal language-only guarantee

Suppose the meaning of an expression depends on a context containing variable binding or another opaque operator. Two expressions may be equivalent in one context and inequivalent in another.

A pretraining objective that observes only finite strings, next-token distributions, and assertion instances may fit all observed data while implementing different unseen-context equivalence relations. The audited paper's negative result shows that no universal emulator exists for the relevant language class.

For RQ-001 this imposes a strict audit rule:

- language-dynamics pretraining may be used as a baseline or representation source;
- it may not be credited with identifying raw-language equivalence unless the applicable transparency or cross-context coverage assumptions are stated and tested;
- successful interpolation on sampled contexts is not a proof of equivalence recovery;
- an external interactive law must be shown to remove the specific opacity-induced alternatives, not merely improve predictive accuracy.

## Consequence for interactive language grounding

A defensible experiment must separate:

1. **language-internal equivalence emulation** from assertions or distributional form;
2. **non-language causal target recovery** from observations and interventions;
3. **cross-system denotation identification** from interactions linking utterances to causal consequences.

The following controls are now mandatory before RQ adoption:

1. a language-only assertion/dynamics baseline;
2. a strongest available language-blind causal-target baseline;
3. direct scoring of internal utterance equivalence, target partition, and denotation separately;
4. transparent and context-opaque language subsets reported separately;
5. held-out binding/context tests rather than only paraphrase or perplexity tests;
6. utterance permutation, target permutation, and simultaneous joint-permutation controls;
7. countermodels with identical assertion and intervention laws but different ontologies;
8. disclosure of every external anchor, including parser slots, target IDs, environment templates, rewards, success labels, and completed trajectories;
9. preregistration of the cross-system observations expected to break each residual automorphism;
10. no new architecture until the baselines and preregistration are complete.

## Official public-code audit

The ACL Anthology, journal record, arXiv record, and author publication record provide the paper and formal constructions. This audit did not locate a paper-specific author-maintained experiment repository.

The primary contribution is theoretical. The constructive emulator is presented as pseudocode / a simple enumeration procedure, while the impossibility result is theorem-level rather than an empirical baseline package.

This audit did not locate:

- an official immutable implementation commit;
- a dependency lockfile;
- a container digest;
- a canonical experiment manifest;
- fixed datasets or split checksums;
- raw logs;
- a multi-seed reproduction protocol;
- model-size, peak-RSS, or wall-time records.

Classification:

> Primary paper, formal definitions, constructive positive result, and negative computability result are public; no paper-specific official empirical implementation was located. Public baseline reproduction is not claimed in C054.

No unofficial architecture or reimplementation was started.

## Decision

**NARROWED BEYOND UNGROUNDED ASSERTION-BASED SEMANTIC EMULATION — NOT ADOPTED**

Reason:

- assertion-like language evidence can already emulate internal semantic equivalence under strong transparency;
- context-sensitive languages already have formal ungrounded-emulation limitations;
- neither result jointly identifies an external intervention-target partition or denotation;
- perfect recovery of both language-internal equivalence and causal target blocks still permits simultaneous cross-system recoding;
- distinctions aliased in both the assertion law and causal law remain unidentifiable.

## Surviving candidate after C054

> After recovering the finest raw-expression equivalence emulatable from all legitimate language-only assertions/dynamics and the finest intervention-target partition identifiable from all legitimate non-language observations/interventions, determine whether a preregistered interactive cross-system law uniquely identifies only the residual equivalence classes and denotation, including context-opaque expressions, while eliminating every simultaneous utterance/target recoding that preserves the complete language, causal, and interaction laws.

This candidate is not adopted. It requires a positive automorphism-elimination theorem or a valid counterexample showing that no non-leaking observation design can provide one.

## Next gate

Before any architecture proposal:

1. map SILG/J-CRe3 language observations to assertion-only, interaction-derived, and leaked-anchor categories;
2. define `Q_text`, `P_causal`, and the residual joint automorphism group on the actual benchmark schema;
3. select and preregister a language-only baseline and a language-blind unknown-target CRL baseline;
4. construct paired transparent/opaque examples with identical surface statistics;
5. directly evaluate `Q`, `P`, and `d`, rather than task success alone;
6. prove which interactive observations eliminate which residual recodings;
7. reject the RQ if the required anchor simply supplies the denotation being claimed as discovered.

## Claim discipline

- RQ-001: narrowed, not adopted.
- Assertion-based internal semantic emulation: established prior art under strong transparency.
- Universal language-only semantic recovery: blocked for the audited context-sensitive language classes.
- External target partition and denotation: not identified by the audited work.
- Public baseline reproduction: not started.
- Experiment: not started.
- Model size / peak RSS / wall time / three seeds: not yet applicable.
- New architecture: none.
- Old A–E toy mechanism: none added.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
