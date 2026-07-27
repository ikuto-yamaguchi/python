# Preregistered Anchor Protocol AP001

## Purpose

AP001 is a preregistered observation protocol for testing whether an independently fixed cross-system probe can eliminate the residual joint automorphisms identified in C064 without using parser slots, simulator target names, reward labels, evaluator semantics, or clarification answers generated from the disputed ontology.

This document defines an experimental contract only. It introduces no architecture and makes no novelty, intelligence-principle, or capability claim.

## Objects to recover

- `Q`: the finest raw-language quotient supported by language-side observations.
- `P`: the finest intervention-target quotient supported by non-language observations.
- `d: Q -> P`: the cross-system denotation map.

The protocol is applicable only after language-only and non-language baselines have independently produced candidate quotients. AP001 does not permit those baselines to share target names, parser outputs, simulator latent names, or learned embeddings trained from the same names.

## Independent anchor construction

Let the candidate target blocks be `P = {p_1, ..., p_m}`. Before any utterance, target label, parser, reward rule, or evaluator is generated, construct an anchor bank:

1. Generate a public random seed `s_anchor` from a committed randomness source.
2. From `s_anchor`, generate a binary probe matrix `B in {0,1}^{k x m}`.
3. Reject and regenerate `B` until all columns are distinct.
4. Bind column `j` to a physical or simulator I/O channel using only an independently enumerated channel serial number, not a semantic target name.
5. Freeze the binding and publish hashes of `s_anchor`, `B`, the channel-serial manifest, and the executable probe implementation before language data are exposed.
6. The language generator, parser, policy, reward, evaluator, and target ontology are prohibited from reading `B`, its column order, or the channel-serial-to-target binding.

For target block `p_j`, probe `i` produces anchor response `B[i,j]` through the frozen channel. Noise may be added only under a preregistered target-independent law.

## Minimal number of noiseless binary probes

Distinct signatures require at least

`k >= ceil(log2(m))`.

This is a counting lower bound, not a guarantee that the simulator binding is independent. Independence is enforced separately by the construction and audit rules.

## Allowed observations

For each episode, the learner may observe:

- raw utterance and its language context;
- non-semantic environment identity;
- ordinary state, action, and trajectory observations admitted by the baseline;
- the selected probe index;
- the anchor response bit or calibrated scalar response;
- probe cost fixed before semantic labels exist.

## Prohibited information and leakage checks

The learner and evaluator must not receive:

- gold target IDs or target masks;
- simulator variable names, object names, filenames, or role names encoding target identity;
- parser semantic slots;
- reward or success values generated from the target codebook;
- reference structures or evaluator labels generated from gold semantics;
- clarification answers generated from the benchmark ontology;
- pretrained embeddings trained on the same target names;
- intervention costs assigned using target labels;
- the hidden column order of `B`.

Required negative controls:

1. shuffle anchor responses across target blocks;
2. permute probe indices consistently but not the frozen channel binding;
3. replace `B` with a matrix containing duplicate columns;
4. remove anchor observations;
5. expose a deliberately leaked gold target ID as a positive leakage control;
6. randomize language while preserving non-language trajectories;
7. randomize non-language target instances while preserving language.

A semantic-identification claim is invalid if performance remains unchanged under anchor-response shuffling or duplicate-column replacement.

## Finite-partition identification theorem

### Assumptions

A1. The language-side observations identify `Q` up to a permutation of its classes.

A2. The non-language observations identify `P` up to a permutation of its blocks.

A3. `d: Q -> P` is bijective on the evaluated subset. Non-bijective cases require a separately preregistered extension.

A4. Each `p in P` has a deterministic anchor signature `b(p)` and `b` is injective.

A5. Anchor signatures and their channel bindings are fixed independently of the language codebook, target names, parser, reward, evaluator, and learned representations.

A6. For each `q in Q`, the observational protocol exposes the anchor signature of `d(q)` with sufficient coverage.

A7. The declared trivial equivalence does not permit changing the independently fixed anchor channel identities.

### Proposition AP001.1

Under A1–A7, the denotation `d` is identifiable up to the already-declared trivial equivalences of the separately recovered quotients.

### Proof

By A2 and A4, every recovered target block can be matched to exactly one independently fixed anchor signature because `b` is injective. By A6, every recovered language class is associated with the signature of its denoted target. Therefore each language class is matched to the unique target block with the same signature. Any alternative denotation `d'` producing the same complete observations must satisfy `b(d'(q)) = b(d(q))` for every `q`. Injectivity of `b` implies `d'(q) = d(q)` for every `q`. A joint permutation that changes `d` would have to permute the independently fixed anchor channel identities, which is excluded by A5 and A7. Hence `d` is identified up to the declared trivial equivalences.

## Limits of Proposition AP001.1

The proposition does not establish that A1 or A2 holds for the selected baselines. It also does not solve merge/split ambiguity when two disputed targets have the same anchor signature or when the evaluated denotation is not bijective.

The result becomes trivial supervision rather than discovery if the anchor binding is generated from gold semantics. Therefore the independence audit is part of the theorem assumptions, not an implementation detail.

## Merge/split requirement

To rule out a merged ontology versus a split ontology inside a previously aliased block, every candidate split member must receive a distinct independently fixed signature. If two members share a signature, AP001 identifies only their anchor-equivalence quotient.

No semantic ontology finer than the complete anchor-response equivalence relation may be claimed as identified.

## Preregistered evaluation

The first AP001 experiment must report, for three fixed seeds:

- exact repository and baseline commit;
- dependency lock and environment manifest;
- hashes for generated data, `s_anchor`, `B`, channel binding, and raw results;
- model bytes;
- peak RSS;
- training and evaluation wall time;
- direct adjusted-Rand or pairwise metrics for `Q` and `P`;
- exact-match and permutation-aware recovery metrics for `d`;
- all required negative controls;
- confidence intervals or complete per-seed results.

Task success, reward, next-state prediction, or language likelihood may be reported only as secondary metrics.

## Falsification criteria

AP001 is falsified as a codebook-independent identification protocol if any of the following occurs:

- the anchor manifest depends on semantic target labels;
- an alternative denotation preserves the frozen anchor transcript;
- duplicate anchor columns do not reduce direct `d` recovery;
- shuffled anchors do not reduce direct `d` recovery;
- direct recovery disappears when gold-ID leakage is removed;
- the separately estimated `Q` or `P` is unstable across the three preregistered seeds beyond the declared equivalence;
- a merge/split countermodel survives all frozen anchor observations.

## Status

- Protocol: preregistered.
- Architecture: none introduced.
- Experiment: not started.
- Positive result: finite-partition sufficient condition proved under explicit assumptions.
- Empirical validity of assumptions: not established.
- Novelty: not established.
