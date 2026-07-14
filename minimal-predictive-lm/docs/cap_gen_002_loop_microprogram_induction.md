# CAP-GEN-002-RII-002: compositional loop-microprogram induction

## Research question

RII-001 jointly discovered raw span boundaries and delayed source/target links, but its
operator family was manually bounded to:

```text
optional reversal + one byte-affine map
```

That family cannot change output length and risks turning future work into a list of
hand-added transformations.  RII-002 asks whether the same boundary-free raw-stream
search can synthesize transformations compositionally from smaller machine operations.

## Substrate

The current machine repeats one program body for each input byte.  Its observable
instructions are:

```text
INC  DEC  NOT  EMIT
```

A direction bit chooses forward or reverse traversal.  Program bodies contain up to five
instructions and must end in `EMIT`.  The frozen search space contains 682 programs.

Examples of programs found by search, not named in the learner:

```text
reverse:    direction=reverse, body=[EMIT]
shift +3:   direction=forward, body=[INC, INC, INC, EMIT]
duplicate:  direction=forward, body=[EMIT, EMIT]
```

`duplicate` changes output length and is not representable by the RII-001 byte-affine
operator class.

This loop-normal-form machine is **not universal**.  It has no registers beyond one byte,
no writable memory, conditional branch, nested loop, indexing, or recursive call.  The
claim is compositional extension beyond the previous hand-enumerated family, not general
program induction.

## Why this is not Phase 11 repeated

Phase 11a/11c synthesized programs or primitives after receiving task examples, typed
values, aligned source/target strings, or a bounded candidate representation.  RII-002
reuses the raw search introduced by RII-001:

- the learner receives one `bytes` object;
- every byte position can start a candidate boundary;
- no record, event, source, target, task, domain, or transformation label is supplied;
- source/target pairings are proposed by temporal proximity and validated prospectively;
- alternate anchor descriptions of the same exact raw gaps are merged;
- one program is stored once when reused by several surface links.

The operator search is still bounded, but the source/target examples on which it operates
are not supplied by a human.

## Frozen falsification stream

The mixed stream contains six hidden surface relations:

- two use reversal;
- two use three increments per byte;
- two emit every source byte twice.

Values, relation ordering, local noise, and value lengths vary.  Anchor, value, and noise
bytes share an alphabet, so punctuation is not a privileged boundary channel.

Required checks:

1. recover 192 hidden source/target boundaries with precision and recall 1.0;
2. discover six surface links but only three shared programs;
3. recover the exact hidden program signatures;
4. freeze the model and predict 48 unseen-value targets exactly;
5. show RII-001 recovers only four links because affine maps cannot duplicate output;
6. accept no program on an independent-target control stream;
7. report program search, learned bits, inference operations, and MDL gains.

## Resource interpretation

The search is intentionally exhaustive inside a tiny space.  It measures the cost rather
than hiding it:

- 682 possible loop programs;
- every supported raw relation candidate is tested in description-length order;
- program executions during induction are reported;
- the emitted program body determines inference operations per input byte;
- duplicate programs across surface links share one stored definition.

A successful controlled result is useful only if later search methods avoid exponential
growth as registers, branches, and memory are introduced.

## Prior-art and novelty boundary

This is not novel merely because it performs enumerative synthesis or library sharing.
DreamCoder, Stitch, inductive programming, streaming string transducers, finite-state
transducers, and superoptimization all cover much richer aspects of program learning.
The restricted candidate difference is the integration of:

- raw byte-level boundary proposal;
- latent delayed source/target pairing;
- chronological validation;
- MDL admission;
- shared compositional program synthesis;

without supplied task examples or aligned strings.

The exact novelty of that integration remains unverified.  No publication claim is made.

## Failure and promotion boundaries

Passing RII-002 does not establish natural-language understanding, unrestricted concept
formation, a universal operator language, public reasoning transfer, or human-level
intelligence.  It remains a generated exact-transform environment with recurring
contexts.

The next architecture step must do at least one of the following:

1. add generic writable state and conditional control while keeping search tractable;
2. learn equivalent context classes instead of requiring exact recurring byte anchors;
3. demonstrate operator reuse on natural/public raw data;
4. improve several frozen CAP-GEN axes with the same learned artifact.

Adding `XOR`, `ROTATE`, `SORT`, or other transformation-specific opcodes solely to pass a
new synthetic case is prohibited.  New machine state is admitted only when it expands a
generic computational capability and wins under complete resource accounting.
