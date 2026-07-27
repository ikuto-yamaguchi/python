# Causal Identifiability Audit C065

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- C responsibility: determine whether joint identification of raw-language equivalence and a latent intervention-target partition is open relative to prior work and identifiable under the declared observations.
- No new architecture.
- No extension of legacy A–E toy mechanisms.
- No novelty, intelligence-principle, or capability-progress claim.
- This run satisfies the C064 decision gate by formalizing and preregistering a concrete codebook-independent anchor protocol and proving a finite-partition positive sufficient condition.
- Numerical reproduction is not started.

## Why C065 is decision-relevant

C064 prohibited further progress claims based only on another paper-specific relabeling counterexample. It required one of five stronger outcomes, including a positive symmetry-elimination proof or a concrete preregistered anchor protocol.

C065 completes both in a restricted finite-partition setting:

1. `benchmarks/grounded_causal/PREREGISTERED_ANCHOR_PROTOCOL_AP001.md` fixes an auditable probe construction before language and semantic target labels are exposed;
2. Proposition AP001.1 proves that an injective independently fixed anchor signature identifies the cross-system denotation once the language and target quotients are separately identified;
3. explicit leakage controls and falsification criteria prevent the anchor from silently becoming a gold target codebook.

This is a positive theoretical advance relative to C064, but not yet an empirical result and not yet a novelty claim relative to the complete literature.

## Factorized identification problem

Let:

- `Q` be the finest raw-language quotient identified by language-side observations;
- `P` be the finest intervention-target quotient identified by non-language observations;
- `d: Q -> P` be the disputed cross-system denotation.

The C026–C064 audits show that recovery of `Q` and `P` separately does not determine `d` when a residual joint automorphism may permute language classes, target blocks, and target-indexed interfaces together.

C065 therefore does not attempt to identify all three objects from one undifferentiated objective. It isolates the remaining problem: eliminate the residual symmetry in `d` using observations whose identity is fixed independently of both codebooks.

## AP001 anchor construction

For `m` candidate target blocks, AP001 creates a binary probe matrix `B in {0,1}^{k x m}` before target labels, utterances, parser slots, reward rules, or evaluators are generated.

The matrix is regenerated until every target column is distinct. Each column is bound to an independently enumerated I/O channel serial number. The seed, matrix, binding manifest, and executable probe implementation are hashed and frozen before language data are exposed.

The learner observes probe indices and responses but does not receive the hidden semantic column order. The language generator, parser, policy, reward, evaluator, and target ontology are prohibited from reading the matrix or binding.

In the noiseless binary case, a counting lower bound is:

`k >= ceil(log2(m))`.

This lower bound only permits distinct signatures; it does not establish independence of the binding. Independence is a separate audited assumption.

## Proposition C065.1 — finite-partition symmetry elimination

Assume:

1. language-side observations identify `Q` up to a permutation;
2. non-language observations identify `P` up to a permutation;
3. `d: Q -> P` is bijective on the evaluated subset;
4. every `p in P` has an injective anchor signature `b(p)`;
5. anchor identities and response laws are fixed independently of language and target codebooks;
6. each language class is observed with the signature of its denoted target;
7. the declared trivial equivalence cannot change independently fixed anchor channel identities.

Then `d` is identifiable up to the already-declared trivial equivalences of the separately recovered quotients.

### Proof

Every recovered target block is matched to exactly one frozen anchor signature because `b` is injective. Every recovered language class is associated with the anchor signature of its denoted target. Therefore each language class is matched to the unique target block with the same signature.

If an observationally equivalent model proposed another denotation `d'`, equality of the frozen anchor transcript would require

`b(d'(q)) = b(d(q))`

for every language class `q`. Injectivity implies `d'(q) = d(q)` for every `q`. A non-trivial joint permutation changing `d` would have to change the independently fixed anchor channel identities and is therefore inadmissible. Hence the residual denotation automorphism is eliminated.

## What the proposition does and does not prove

The proposition is a sufficient condition for the remaining cross-system matching problem. It does not prove:

- that any selected language baseline identifies `Q`;
- that any selected unknown-target CRL baseline identifies `P` under the benchmark conditions;
- that real hardware or a simulator implementation actually satisfies codebook independence;
- that the bijective restriction is adequate for natural language;
- that noise, missing coverage, polysemy, synonymy, or many-to-many denotation preserve the same guarantee;
- that the condition or protocol is novel relative to all prior work.

The theorem also becomes vacuous supervision if the frozen signature is assigned from gold semantic labels. The independence audit is therefore a mathematical assumption and an experimental obligation.

## Merge/split boundary

AP001 eliminates merge/split ambiguity only when every candidate split member has a distinct independently fixed signature. If two disputed targets share the same complete anchor response law, the protocol identifies only their anchor-equivalence quotient.

Therefore no ontology finer than the complete frozen probe-response equivalence relation may be claimed as identified.

## Required controls

AP001 preregisters the following controls:

- anchor-response shuffle;
- duplicate-column anchor matrix;
- no-anchor baseline;
- probe-index permutation without changing frozen channel binding;
- explicit leaked-gold-ID positive control;
- language randomization with non-language trajectories preserved;
- target-instance randomization with language preserved.

A claimed semantic identification result is invalid if direct denotation recovery is unchanged by anchor-response shuffling or duplicate-column replacement.

## Relationship to the audited prior-art boundary

The existing audited lines of work recover one or more of:

- causal coordinates, graphs, or unknown intervention targets;
- intervention-response or target-relevance quotients;
- language-internal predictive or assertion-based quotients;
- reward-, policy-, construction-, or future-prediction-sufficient functional grounding.

AP001 does not replace these baselines. It composes their separately recovered quotients with an independently fixed cross-system measurement law. The positive theorem applies only after the two marginal quotient recovery assumptions are verified.

The next numerical work must therefore reproduce selected public baselines rather than introduce a new architecture.

## Experimental consequences

The first experiment under AP001 must use three fixed seeds and report:

- exact source commits and dependency locks;
- generated-data, anchor-seed, matrix, binding, and raw-result hashes;
- model bytes;
- peak RSS;
- training and evaluation wall time;
- direct recovery metrics for `Q`, `P`, and `d`;
- all negative and leakage controls.

Task success, reward, language likelihood, next-state prediction, or other functional metrics are secondary and cannot substitute for direct recovery.

## Decision

**NARROWED TO A TESTABLE FINITE-PARTITION ANCHOR IDENTIFICATION PROGRAM — CONDITIONALLY ADMISSIBLE, NOT YET ADOPTED**

The candidate RQ now has a positive path:

> After public baselines independently recover the finest supported language quotient `Q` and non-language target quotient `P`, does a preregistered codebook-independent probe bank with injective frozen signatures satisfy the AP001 assumptions in practice and identify denotation `d`, while the shuffle, duplicate-signature, and leakage controls behave as predicted?

The RQ is not adopted yet because the marginal identification assumptions, codebook independence, and empirical falsification tests have not been established.

## Status

- C064 decision gate: satisfied through a positive restricted theorem and preregistered protocol.
- AP001 protocol: committed.
- Positive sufficient condition: proved for a finite bijective quotient setting under explicit assumptions.
- Full general-language theorem: not proved.
- Prior-art novelty of AP001: not established.
- Public baseline reproduction: not started.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- Experiment: not started.
- Model size, RSS, runtime, and three seeds: not yet applicable.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
