# CAP-GEN-002-RII-001: raw interchange induction

## Why this experiment exists

The rejected PR #12 repackaged Phase 1--19.  Minimum predictive state, sparse indexed
memory, lifetime resource selection, external knowledge, macro learning, primitive
invention, and taskless mixed streams had already been implemented in earlier phases.
Repeating those components is not progress.

The remaining structural gap is narrower:

> From one raw continuous observation stream, discover which byte intervals behave as
> replaceable variables, which distant intervals depend on them, and which transformation
> is reusable, without supplying tokens, records, event boundaries, aligned input/output
> pairs, task IDs, role candidates, or semantic operator names.

This trial tests that gap directly.  It does not add another reasoning solver.

## Exact difference from Phase 1--19

- Phase 1/2 received process symbols and transition observations; this trial proposes
  candidate boundaries at every byte position.
- Phase 9 received a human-designed raw grounder and event/role hypothesis language.
- Phase 11c received aligned input/output strings and a bounded transformation proposal
  family.  Phase 11e removed record labels but retained punctuation cues, a bounded role
  inventory, nearby identifier candidates, and constant-offset transformations.
- Phase 18d removed more task metadata but still operated on segmented or typed values and
  a narrow meta-grammar.
- Phase 19 learned raw-byte statistics and long exact contexts, but did not create delayed
  variable links or executable transformations.

RII-001 receives only `bytes`.  Hidden boundaries and relation identities exist solely in
the scorer.

## Working hypothesis: predictive interchange symmetry

A span is a variable candidate when different byte strings repeatedly occupy the same
raw left/right context.  Two such span families are linked when a compact transformation
of the earlier span predicts the later span across chronologically held-out occurrences.

The learner searches:

1. every byte position;
2. several generic anchor lengths;
3. every gap length inside a fixed resource budget;
4. every delayed pair of retained gap families;
5. every program in the current tiny byte-transducer substrate.

It admits a link only when:

- the program fits the earlier occurrences;
- it predicts later validation occurrences that were not used to synthesize it;
- literal target storage is more expensive than anchors, link, program, pointers, and
  lengths combined;
- alternate anchor descriptions that identify the same raw target boundaries are merged.

The current program substrate is deliberately small:

```text
read source forward or backward
for each byte: y = scale*x + shift (mod 256)
```

It contains no `reverse-task`, `Caesar-task`, source-role, target-role, benchmark, or
subject identifier.  Nevertheless, the family itself is human chosen.  Passing this
trial does **not** establish unrestricted operator invention.  The next trial must replace
it with a resource-bounded universal microprogram substrate.

## False-link bound for the control model

Let:

- `R` be the number of candidate delayed links;
- `P` be the number of candidate programs tested per link;
- `v` be the number of independent validation pairs;
- `ell` be the minimum target length in bytes.

If control targets are independent and uniform conditional on every source, a fixed
program matches all validation bytes with probability at most `256^(-v*ell)`.  By the
union bound,

```text
Pr(any false accepted exact link) <= R * P * 256^(-v*ell).
```

For the frozen experiment, `R=2756`, `P<=510`, `v>=4`, and `ell>=4`, giving an idealized
upper bound below `4.2e-33`.  The random-control stream is also executed rather than
relying on the bound alone.

This bound does not cover structured natural data, dependent noise, adaptive candidate
selection, or approximate programs.  Those require stronger prospective controls.

## Prior-art boundary

This is not novel merely because it uses compression, segmentation, slots, programs, or
causal variables.

- Brent's unsupervised word-discovery model infers segmentation under a lexicon model and
  given utterance boundaries; it does not induce nonlocal executable span transforms:
  https://arxiv.org/abs/cs/9905007
- Sequitur and grammar compression extract repeated substrings; repeated text alone does
  not establish a delayed variable/operator dependency.
- DreamCoder and Stitch learn reusable program libraries from tasks or an existing DSL
  program corpus:
  https://arxiv.org/abs/2006.08381
  https://arxiv.org/abs/2211.16605
- Slot Attention learns object slots from framed perceptual inputs with a specified slot
  architecture:
  https://arxiv.org/abs/2006.15055
- CITRIS/iCITRIS and BISCUIT provide causal-identifiability results using temporal frames
  plus intervention targets or interaction structure:
  https://arxiv.org/abs/2202.03169
  https://arxiv.org/abs/2206.06169
  https://arxiv.org/abs/2306.09643

The candidate contribution is therefore restricted to the **joint, boundary-free search
for delayed interchange relations and executable transformations on one raw byte stream**,
with chronological validation and complete coding cost.  A broader novelty claim requires
an exhaustive literature review and a stronger operator substrate.

## Frozen experiment

The learner receives one delimiter-free mixed stream containing four unknown surface
links.  Two links share reversal; two share the same byte-affine shift.  Values, ordering,
and noise vary.  The scorer alone knows the four source/target span boundaries.

Required outcomes:

- recover every hidden source and target boundary with no false boundary;
- discover four surface links but only two shared programs;
- freeze the artifact and exactly predict new values in a separately generated stream;
- beat a boundary-aware most-frequent-target baseline;
- accept no relation when target values are generated independently;
- report learned payload, search operations, inference operations, and peak index entries.

## Promotion boundary

RII-001 is a controlled missing-capability probe.  It is not promoted to CAP-GEN-002 on
its own.  Promotion additionally requires all of the following:

1. replace the hand-bounded byte-affine program family with one generic universal or
   provably extensible microprogram substrate;
2. remove repeated fixed anchors or demonstrate boundary recovery under multiple unseen
   surface encodings;
3. learn from natural or public raw data rather than a generated stream;
4. improve multiple previously zero CAP-GEN public axes with one frozen artifact;
5. preserve the already solved axes and beat matched neural/statistical baselines on
   executable bits, inference operations, or peak memory.

## Anti-repeat rule

A follow-up that only adds more affine transformations, more delimiters, another relation
solver, or another controlled 100% task is rejected.  The next work item must attack the
operator-substrate or natural-stream limitation, not decorate this gate.
