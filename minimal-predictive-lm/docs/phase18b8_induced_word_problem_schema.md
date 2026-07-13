# Phase 18b-8: induced word-problem schema

Phase 18b-6 used a fixed compiler. Phase 18b-8 asks whether clue roles and the algebraic schema can instead be selected from demonstrations.

The parser only extracts a controlled target pair, quoted clue spans, numeric values, units, and the question pair. It does not preassign clue semantics. The learner searches:

- every count/value assignment of recurring global clue spans,
- active/inactive status for recurring entity-specific clue spans,
- three count equations,
- four weighted-value equations.

Candidates are scored by whether the shared Phase 18b-7 exact solver reproduces demonstration answers. A unique zero-error schema is required. Symmetric calibration that leaves multiple schemas optimal is rejected.

Held-out evaluation changes domains, values, clause order, entity order, and cue combinations. Unknown cues, extra numeric clues, and unit mismatch abstain.

This is controlled schema induction. The target/clue/question wrapper is still fixed, only one two-entity linear family is available, and the result is not free Japanese understanding or high-school intelligence.
