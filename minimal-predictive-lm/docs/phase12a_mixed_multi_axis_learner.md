# Phase 12a: mixed multi-axis learner

## Motivation

A collection of efficient domain-specific solvers does not establish scalable
intelligence. The important question is whether one learner can turn
interaction evidence into reusable programs and primitives while task types are
mixed in one workload.

Phase 12a therefore removes a domain label from the runtime path. The learner is
not told that an example is arithmetic, state management, provenance, or string
transformation. It observes a raw prompt together with arguments, before/after
state, and output during calibration.

## Shared learning path

Every prompt is passed through the same generic front end:

1. NFKC normalization
2. extraction of numeric values and ASCII `key=value` bindings
3. `state_` bindings become sparse pre-state
4. word and operator features become possible routing evidence
5. inputs are grouped only by value types and state-key signature
6. a typed MDL program is induced when the fixed grammar is sufficient
7. a residual string primitive is proposed when the typed grammar is insufficient
8. lexical features are selected only when one signature requires multiple programs

There is no arithmetic handler, state handler, condition handler, provenance
handler, or event handler. The final model contains 11 learned routing rules and
reports zero domain-specific handlers.

## Representations reused across axes

The same typed grammar supplies:

- `ADD / SUB / MUL / DIV`
- `CONCAT`
- `IF_EQ`
- argument and state reads
- sparse state writes

The same residual primitive inducer supplies affine character transformations.
The same lexical rule selection separates programs that share an input type
signature, such as concatenation, provenance selection, conditional selection,
and event-source extraction.

## Fairness boundaries

The mixed manifest contains 40 pinned public BIG-bench arithmetic examples and
30 deterministic synthetic examples across six other axes. Calibration prompts
have zero exact overlap with benchmark prompts.

Because only one axis is public, the entire manifest is deliberately marked
`public=False`. The benchmark harness therefore cannot authorize a public
multi-domain parity or Pareto claim. This experiment can justify an exploratory
open-model run, not a general LLM comparison.

## Search accounting

The 892-byte compiled model required 108,238 candidate evaluations. This cost is
not omitted from the report. Inference is small after compilation, but the
current induction process is still expensive relative to the resulting program.
Future phases must reduce induction cost through macro reuse, cached semantic
signatures, and value-of-computation stopping rather than simply increasing the
candidate budget.

## Failure retained during development

The first public run scored 0/40 because calibration used symbolic arithmetic
while BIG-bench used English operator phrases. This revealed a grounding gap.
The repair changed the independent interaction evidence to the English surface
family and let the existing generic lexical learner induce the distinctions.
No benchmark examples or exact prompts were inserted into calibration, and no
operator-specific parser was added.

## Remaining gaps

- most non-arithmetic axes are synthetic
- prompt extraction relies on constrained numeric and ASCII binding forms
- routing uses sparse surface words, not open syntax or semantics
- the residual primitive meta-language is bounded
- no long-context understanding, knowledge retrieval, coding repository, or free generation
- no energy measurement
- no comparable lifetime ledger for MPM induction and LLM pretraining

Phase 12b should run the exact mixed manifest and matched calibration evidence
through SmolLM2-135M-Instruct. The result must be labeled exploratory because
the whole suite is not public. The next evidence-advancing phase must replace
synthetic axes with pinned public raw-input tasks.
