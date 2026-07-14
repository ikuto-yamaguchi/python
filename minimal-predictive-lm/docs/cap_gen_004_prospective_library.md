# CAP-GEN-004-POLA-001: prospective option library admission

## Purpose reset

The project goal is a small general learner, not an ever-growing collection of anti-shortcut tests. CAP-GEN-003 is therefore frozen. POLA-001 is the first new algorithmic hypothesis after that freeze.

The hypothesis is:

> A learner can reuse abstraction-learning strategy across heterogeneous tasks by causally forecasting how long newly observed subprograms are likely to recur, then buying a short-lived option on an abstraction before retrospective compression alone justifies permanent library admission.

The option is probationary for one task. It becomes permanent only when the next task obtains a real encoding benefit. This changes actual search behavior; it is not only an evaluation gate.

## Prior-art boundary

Established work includes:

- DreamCoder and related library learners that retrospectively compress solved programs;
- Stitch and other abstraction-invention systems;
- adaptive combinator sets for universal induction;
- online library learning in human puzzle solving;
- the 2026 prospective-compression result, which formalizes expected compression of future programs and provides human evidence;
- skill practice and planning methods that optimize expected future competence;
- cache admission, prefetching, and real-option ideas outside abstraction learning.

The 2026 prospective-compression paper explicitly leaves the future-program distribution unspecified. POLA-001 supplies one small causal estimator: the empirical survival distribution of maximal recurring subprogram runs. It also adds one-task probation so an incorrect forecast does not permanently pollute the library.

This is a **candidate novelty**, not an established novel contribution. It must still survive a broader literature review and public benchmarks.

## Algorithm

For each solved opaque program, the learner enumerates contiguous subprograms of length two to four. It maintains consecutive presence runs for each candidate.

When a run ends, only maximal candidates are recorded. Overlapping subprograms from one motif are not counted as independent evidence.

For candidate `h` with current run length `r`, the causal forecast is:

```text
E[remaining uses | completed run length >= r]
```

using only completed earlier runs. At least two completed runs are required.

The learner computes:

```text
retrospective score
  = compression already obtained
  - helper definition cost

prospective score
  = retrospective score
  + expected remaining uses * current incremental compression
```

A positive retrospective score creates a permanent helper. A candidate justified only by the prospective term enters a one-task probationary cache. It becomes permanent only if the next task actually compresses with it.

## Frozen heterogeneous curriculum

The same learner receives one stream of opaque program-token tuples. Family labels are not inputs.

The evaluation curriculum contains:

1. list transformation motif A, repeated for four tasks;
2. list transformation motif B, repeated for four tasks;
3. string-processing motif, repeated for four tasks;
4. grid-transformation motif, repeated for four tasks.

The first two completed motif runs train the run-duration forecaster. The policy is then applied unchanged to string and grid programs.

## Falsifiable predictions

POLA-001 predicts:

1. before two completed motif runs, it should behave like retrospective compression;
2. on later four-task motifs, it should provision a helper after two observations while retrospective compression waits for three;
3. that one-task lead must reduce exact exhaustive-search nodes after charging induction and storage;
4. isolated unrelated tasks must produce no helper admissions;
5. when motif durations abruptly shorten, forecast error must be bounded by temporary probation rather than permanent library pollution.

Failure on any item rejects the frozen algorithm.

## Frozen result

Primitive vocabulary size is derived from the curriculum, not tuned per learner.

```text
no library total cost       4,076,863,808
retrospective total cost    3,584,929,656
prospective total cost      2,927,677,672
```

Prospective admission reduces total counted cost by more than 18% against retrospective admission and by more than 28% against no library.

For the held-out-style grid motif:

```text
retrospective permanent admission: after task index 17
prospective probation:             after task index 16
```

On the next grid task, exhaustive search falls from `345,025,250` nodes to `140,607` nodes one task earlier.

The string motif shows the same one-task lead.

## Controls

### Isolated programs

Twelve unrelated programs share no recurring candidate. Prospective admission creates zero options and zero permanent helpers.

### Duration shift

After two four-task runs, motif durations abruptly shorten to two. The prospective policy creates two unsuccessful probationary options but does not make them permanent. Its total regret against retrospective admission is ten counted operations, with eight temporary storage tokens.

This is not zero regret, but it is bounded and explicit.

## Why this is closer to the actual objective

The reusable component is no longer a hand-given cycle operator. It is an **online abstraction-admission policy** learned from one task family and reused in different program vocabularies.

It changes when useful abstractions become available and therefore changes future problem-solving cost. That is a real capability mechanism rather than another leakage detector.

## Remaining limitations

POLA-001 still does not establish general intelligence:

- solution programs are provided after each task;
- subprogram boundaries are contiguous and hand-delimited;
- the curriculum is generated rather than a public benchmark;
- only recurrence duration is modeled;
- no natural language, perception, or environment interaction is solved;
- search remains exhaustive and finite;
- novelty has not been established by peer-level literature review.

## Hard next gate

No more hand-designed curricula may be added merely to improve these numbers.

The next cycle must do both:

1. run the same policy on a public program or reasoning corpus with chronological order; and
2. compare against at least retrospective compression, no library, and a hindsight oracle.

If prospective admission does not reduce held-out search or sample cost on public data, this central hypothesis is rejected rather than patched indefinitely.
