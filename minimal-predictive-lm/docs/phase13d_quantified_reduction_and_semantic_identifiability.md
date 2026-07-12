# Phase 13d: quantified reduction and semantic identifiability

## Why the final public axis is different

After Phase 13c, direct arithmetic, Boolean expressions, nested arithmetic, and word sorting all reach 40/40 on the fixed public slice. Object counting remains 0/40.

The missing information is not merely another operator. The prompt can reveal that there are `two apples`, but the answer to “How many fruits?” also requires the proposition `apple is a fruit`. Two worlds can share the same syntax and quantities while assigning the noun to different concepts, producing different correct counts.

## Generic quantifier

Phase 13d adds a domain-neutral pipeline:

1. ground articles and number words from independent observations;
2. parse a variable-length owned-item sequence;
3. identify the queried concept;
4. compute a minimum and maximum possible count under current membership knowledge;
5. answer only when the interval collapses to one value.

The universal concept `objects` is induced from three unrelated examples where the target equals the sum of all listed quantities. No public benchmark prompt or item-category membership is used.

## Public result

The quantifier answers the twelve public questions whose query concept is `objects` and gets all twelve correct. It abstains on the remaining twenty-eight questions involving fruits, animals, vegetables, or musical instruments.

Object-counting accuracy rises from 0% to 30%, and total public accuracy rises from 80% to 86%, with zero wrong answers.

## Identifiability result

For a prompt containing six items of invented types and an ungrounded query concept, the program returns an interval `[0, 6]`. Both endpoints correspond to worlds consistent with its observations, so any exact answer would be unjustified.

When separate membership observations are supplied for an unrelated infrastructure domain, the same quantifier answers the category count exactly. Thus the reduction algorithm and the semantic knowledge source are separable.

## Research consequence

Copying the BBH item vocabulary would turn the remaining problem into a benchmark lookup table. The next research target is instead a compact, provenance-aware concept graph that can acquire lexical membership from ordinary interaction, perception, documents, or a general ontology and reuse it across tasks.

Its cost must include acquisition, verification, storage, contradiction handling, and future reuse. Without such evidence, abstention is the correct behavior.
