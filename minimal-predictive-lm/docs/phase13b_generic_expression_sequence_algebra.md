# Phase 13b: generic expression and sequence algebra

## Objective

Phase 13a established a frozen public baseline: direct arithmetic worked, while boolean expressions, nested arithmetic, object counting, and word sorting all caused abstention.

Phase 13b does not add one solver per benchmark. It introduces two reusable forms:

1. a typed expression algebra shared by numeric and Boolean values;
2. a variable-length sequence transformation shared by words, identifiers, paths, sensor labels, and command names.

## Induction

Atomic operator semantics are induced from independent observations. Numeric operators reuse the Phase 11 typed program synthesizer. Boolean operators are represented by the minimum consistent truth table. Operator precedence is selected from a bounded rank search by requiring one assignment to explain independent expressions.

The ordering program is chosen from a bounded comparator family. Its lexical activation cues are extracted from repeated words in independent prompts; no BBH word list is stored.

## Public transfer

On the same fixed 200-example public suite, accuracy changes from 20.0% to 68.5%:

- Boolean expressions: 0% to 100%;
- direct arithmetic: remains 100%;
- multistep arithmetic: 0% to 42.5%;
- word sorting: 0% to 100%;
- object counting: remains 0%.

The same induced algebra also obtains 6/6 on held-out numeric, Boolean, identifier-ordering, and filesystem-ordering examples.

## Failure discovered

Every multistep failure except one correct case contained multiplication followed by a negative operand. The learned unary precedence was too weak, producing both abstentions and wrong scope. Phase 13c preserves this imperfect result and fixes the generic scope problem separately.

## Limits

The tokenizer, shunting-yard execution structure, truth-table representation, and comparator candidate families are still human-designed meta-grammar. Operator meanings and ranks are induced only within that bounded language. This is broader reuse, not open-ended representation invention.
