# SPARC-HS18: shared event causal compiler

HS18 connects the existing bounded structural-causal adjudicator to English prose through one shared event representation.

The compiler extracts or estimates:

- actual event participation;
- prescriptive versus statistical normality;
- conjunctive and disjunctive outcome conditions;
- omission maintenance versus redundant active addition;
- controlled action, accidental realization, goals, and foreseen side effects;
- proximate temporal paths versus background conditions.

It has no benchmark-axis-name branch. Unsupported causal language abstains rather than guessing.

## V4 learned sparse prototype layer

V4 adds a small local prototype memory trained only on generated structural causal stories. The learned layer routes by sparse clause and event features, then combines its result with the bounded symbolic evidence lattice. Public causal targets are not used for prototype training.

The V4 gate requires:

- at least 90% accuracy and coverage on a separately seeded synthetic shift;
- no more than eight mean prototype candidates per query;
- the HS17 515/600 baseline to be reproduced;
- no regression on any non-causal public axis;
- at least 34/40 on the integrated causal slice;
- at least 112/160 across the four development slices;
- at least 60% accuracy and coverage on the previously uninspected final tail beginning at example 160.

A known research risk is disagreement between the learned prototype and the symbolic lattice for persistent sufficient states, responsibility-sensitive omissions, and norm-sensitive conjuncts. V4 therefore records consensus, learned override, and symbolic retention separately rather than silently replacing one system with the other.

## Evaluation protocol

- generated renamed and reordered causal stories test representation shift;
- the already inspected first 160 BBH causal examples are development diagnostics only;
- the remaining verified tail beginning at example 160 is frozen before V4 inspection;
- HS17 is re-run as the integrated baseline;
- all non-causal public axes must be non-regressing.

## Claim boundary

The compiler remains a bounded causal-language fragment. The prototype memory does not autonomously discover causal variables, social norms, or a general world model, and success does not establish Japanese high-school-level intelligence.
