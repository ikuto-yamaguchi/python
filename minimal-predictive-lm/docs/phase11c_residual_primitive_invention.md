# Phase 11c: residual-driven primitive invention

## Motivation

Phase 11a can induce programs only inside a fixed grammar. When no program explains the observed transition traces, increasing the search budget does not help if the missing operation is not representable. Phase 11c separates this **representation failure** from ordinary search failure.

The objective is not to patch the engine with one handwritten operation per failed task. Instead, residual input/output evidence proposes a small family of candidate representations. Candidates compete under held-out validation and a lifetime resource objective.

## Candidate generation

For aligned string transformations, the current meta-grammar proposes:

1. whole-string lookup,
2. a character-to-character table,
3. a conditional codepoint interval with one additive offset.

The task label and the name `UPPERCASE` are not supplied. The third candidate is represented only as:

```text
if lower <= codepoint <= upper:
    output = codepoint + offset
else:
    output = codepoint
```

The interval and offset are inferred from changed aligned characters.

## Cross-family validation

A candidate is eligible only if it is exact on training data and on held-out examples from multiple application families. This rejects a whole-string cache even when it has zero training error.

Among surviving candidates, the smallest serialized representation is selected. In the current experiment, the character table and affine rule both generalize across the ASCII validation set, but the affine rule is smaller.

## Lifetime adoption

Representation extension is a migration, not a free local patch. The normalized experimental objective is:

```text
future error reduction * future calls * error price
- primitive storage
- validation evidence
- migration cost
```

A primitive used only once is rejected. The same primitive is adopted when repeated future use repays discovery, validation, storage, and migration.

The conversion coefficient between one avoided error and bits is explicit experimental accounting. It is not claimed to be a physical equivalence between CPU energy and storage.

## Rollback and distribution shift

The learned rule is restricted to the observed ASCII interval. It intentionally fails on accented letters and one-to-many Unicode case mappings. This failure demonstrates that the mechanism has invented a bounded rule, not the universal semantic concept of letter case.

A production system must keep provenance, version the primitive, monitor residuals after deployment, and roll back or refine the representation when distribution shift invalidates it.

## What this establishes

Phase 11c establishes that a fixed-grammar failure can trigger a data-derived representation extension without adding a separate algorithm for every application domain. The invented primitive transfers to unseen labels, repository symbols, sensor names, and dialogue outputs.

It does **not** establish open-ended primitive invention. The proposal meta-grammar is still designed in advance, aligned demonstrations and task boundaries are supplied, and the experiment is synthetic.

## Next research questions

- infer alignment rather than receiving aligned strings,
- generate candidate representation languages from residual structure,
- discover stateful and relational primitives,
- validate one proposed primitive across heterogeneous modalities,
- merge, split, version, forget, and roll back primitives under distribution change,
- connect primitive invention to raw-language task discovery and public benchmarks.
