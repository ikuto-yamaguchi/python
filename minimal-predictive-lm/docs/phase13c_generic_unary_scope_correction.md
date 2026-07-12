# Phase 13c: generic unary-scope correction

## Diagnostic evidence

Phase 13b answered 31 of 40 public multistep-arithmetic problems, with 17 correct and 14 wrong. Nine were explicit abstentions.

A diagnostic pass separated surface structures. Among the 24 expressions containing multiplication by a negative operand, the model obtained one correct answer, fourteen wrong answers, and nine abstentions. All sixteen expressions without that structure were correct.

This identifies a reusable grammar defect rather than a benchmark topic: a prefix unary operator was not binding tightly enough inside a binary product.

## Correction protocol

Five independent expressions are added as interaction evidence:

- multiplication by a negative value;
- multiplication of two negative values;
- addition around a negative product;
- subtraction around a negative product;
- division by a negative value.

No benchmark expression, target, task name, handler, or grammar exception is used. The same bounded precedence search is rerun.

The selected representation assigns multiplication and unary negation the same rank, while unary operators remain right-associative. This is sufficient for the prefix operator to bind to the following operand before the product is reduced.

## Public result

On the fixed public 200-example suite:

- multistep arithmetic improves from 17/40 to 40/40;
- wrong multistep answers fall from 14 to 0;
- multistep abstentions fall from 9 to 0;
- overall accuracy improves from 68.5% to 80.0%;
- coverage improves from 75.5% to 80.0%;
- every answered item is correct.

Boolean expressions, direct arithmetic, and word sorting remain at 100%. Object counting remains at 0% and is not patched with a benchmark vocabulary.

## Generality boundary

The correction generalizes across arbitrary arithmetic expressions inside the current token and operator language. It does not imply open-ended syntax induction. The parser architecture and bounded precedence search remain designed meta-structure, and the interaction set was authored after inspecting the structural failure class.

The remaining object-counting gap is qualitatively different. Syntax can recover quantities and noun phrases, but deciding that `apple` is a fruit or `flute` is a musical instrument requires prior lexical-semantic grounding. Adding the benchmark's item list would violate the research objective; the next work must separate generic quantified reduction from concept acquisition and account for the information needed to learn category membership.
