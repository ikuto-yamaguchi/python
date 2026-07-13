# Phase 18d-12: multiple ungrouped primitive invention

Phase 18d-11 promoted one reusable hidden transformation from an ungrouped stream. Phase 18d-12 mixes two structurally different unknown transformations, known operations, and one-off noise in the same causal stream.

The learner receives only typed `input` and `output` fields. It is not given task IDs, task counts, task boundaries, residual groups, primitive names, family labels, or target parameters.

The candidate meta-grammar contains three generic controls:

- length-preserving affine index transducers, `y_i = x[(a i + b) mod n]`;
- element-wise affine transducers over character code points or numeric elements, `y_i = s x_i + c`;
- a literal sequence lookup control.

Residual candidates must have support from both strings and numeric lists, positive MDL gain, and a unique top probe behavior. Once promoted, the behavior is removed from the unresolved residual buffer and cannot be promoted again.

The frozen stream requires two independent promotions:

- an index transformation with `(a, b) = (1, 1)`;
- an element transformation with `(s, c) = (1, 1)`.

Future examples are not used to choose these parameters. One-type evidence, equal-gain competing clusters, one-off noise, duplicate behaviors, and under-supported clusters are rejected. Metamorphic controls recover different hidden parameters using the same search.

This remains a controlled experiment. The typed record parser, the two candidate families, parameter ranges, probe set, minimum support, local operation persistence, and MDL accounting are human-designed. It does not establish raw-byte invention, unrestricted algorithm discovery, LLM-like general learning, or high-school intelligence.
